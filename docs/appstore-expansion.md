# Cytoscape App Store Expansion — Design & Implementation Reference

---

## 1. Overview

The Cytoscape App Store has been expanded from supporting primarily Desktop applications to supporting three application types: **Desktop Apps**, **Web Apps**, and **Service Apps**. The Web App implementation supports two submission mechanisms — GitHub/repository-based submission and pre-built bundle upload. The Service App implementation allows an application to be registered through an external service endpoint.

This document describes the current architecture, the models and views backing each pipeline, the automated/human review design, security considerations, infrastructure changes, and known issues encountered during implementation.

---

## 2. Primary Goals

1. Allow Cytoscape Web applications to be distributed through the App Store.
2. Allow external services to be registered as Cytoscape Service Apps.
3. Provide a consistent submission, validation, review, and publication workflow across all three app types.
4. Host approved Web application bundles using App Store-controlled storage/CDN infrastructure.
5. Generate the Web App manifest from App Store data rather than trusting a developer-supplied manifest.
6. Introduce automated checks before human review.
7. Maintain compatibility and security requirements for applications running inside Cytoscape hosts.
8. Keep the three pipelines close enough in shape that review tooling, admin UI, and staff workflows can eventually be shared.

---

## 3. Application Types

### 3.1 Desktop Apps
Use the existing App Store release mechanism (`AppPending` → confirm → `App`/`Release`). Predates the Web/Service work; largely unchanged, though it shares the ID-collision risk class described in §10.4 once multiple pending tables share a URL/view namespace.

### 3.2 Web Apps
Loaded dynamically by Cytoscape Web via Module Federation. A bundle contains `remoteEntry.js`, `main.mjs`, `assets/`, etc., and must expose an `./AppConfig` module. The following identifiers must remain consistent:

```text
CyApp.id  ==  AppConfig.id  ==  Module Federation scope/name
```

Two submission mechanisms:

- **Mechanism 1 — GitHub/repository submission.** Submitter provides a repo URL/ref; Store retrieves, builds, checks, stores, reviews, publishes. **Status: parked** — only `repo_url` is currently captured and stored; ref resolution and build steps are drafted but not wired in. This mechanism is intended to be the primary form of submission.
- **Mechanism 2 — Pre-built bundle upload.** Submitter uploads a `.zip`; Store extracts, validates structure, checks, reviews, publishes. **Status: functional** through submission → structural validation → confirmation → pending storage. Automated checks and CDN publication are designed but not yet live.

### 3.3 Service Apps
Backed by an external service endpoint rather than a bundle. Lifecycle:

```text
PENDING → VALIDATED → CHECKER_PASSED → APPROVED / DECLINED
```

Reachability is checked twice: a quick synchronous check at submission time (fast feedback, rejects obviously-broken URLs), and an authoritative out-of-band pass via a management command (`check_service_apps`) that runs reachability, a `/status` health check, spec validation, and consistency checks — deliberately not run inline, since a slow/hanging remote endpoint shouldn't block the request/response cycle.

---

## 4. Model Changes

### 4.1 `App`
Gained a `platform` field, backed by a module-level `AppPlatform` `TextChoices` (`desktop` / `web` / `service`), so a single `App` row can be filtered by pipeline without joining out to pending/release tables.

### 4.2 Web — `WebBundlePending`

```python
class WEB_SUBMISSION_ORIGIN(models.TextChoices):
    WEB_URL = 'web_url', 'Web URL'
    WEB_BUNDLE = 'web_bundle', 'Web Bundle'

class WebBundlePending(models.Model):
    class Status(models.TextChoices):
        DEFAULT = 'default_status', 'Default Status'
        PENDING_AUTOMATED_CHECKS = 'pending_automated_checks', 'Running Automated Checks'
        CHECKS_FAILED = 'checks_failed', 'Automated Checks Failed'
        PENDING_REVIEW = 'pending_review', 'Pending Manual Review'
        # PUBLISHED / REJECTED are not modeled as pending-row terminal
        # states — see §7.4.

    id = models.BigAutoField(primary_key=True)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=128)
    author = models.CharField(max_length=512, blank=True)
    version = models.CharField(max_length=32)
    description = models.TextField(blank=True)
    license = models.CharField(max_length=64, blank=True)   # spelled with an 's'
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DEFAULT)
    created = models.DateTimeField(auto_now_add=True)
    bundle = models.FileField(upload_to="webpending/", storage=get_webbundles_storage, null=True)
    bundle_hash = models.CharField(max_length=64)
    origin = models.CharField(max_length=32, choices=WEB_SUBMISSION_ORIGIN.choices,
                               default=WEB_SUBMISSION_ORIGIN.WEB_BUNDLE)

    class Meta:
        ordering = ['-created']
```

`origin` was added specifically as the forward-compatibility hook for eventually merging the URL and bundle pending flows into one table (§10.5) without a further schema migration.

### 4.3 Web — `WebUrlPending` (parked mechanism)

```python
class WebUrlPending(models.Model):
    id = models.BigAutoField(primary_key=True)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=128)
    author = models.CharField(max_length=128, blank=True)
    version = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)
    repo_url = models.URLField(blank=False, null=True)
    origin = models.CharField(max_length=32, choices=WEB_SUBMISSION_ORIGIN.choices,
                               default=WEB_SUBMISSION_ORIGIN.WEB_URL)
```

Deliberately minimal — exists to store a submission, not process one yet.

### 4.4 Web — `WebBundleRelease`

Represents a **published** version, distinct from the pending row that preceded it. Final field split: `WebBundlePending`/`WebBundleRelease` both carry all `AppCatalogEntry` fields (manual entry — no `repository`/`dependencies`) plus internal-only fields — `status`/`decline_reason`/`bundle_file` on Pending; `cdn_base_url`/`bundle_sha256`/`checksums`/`published_by` on Release. `remote_entry_url` is a **derived property** (`urljoin(cdn_base_url, "remoteEntry.js")`), not a stored column.

```python
def make_bundle_release(self, app: "App") -> "WebBundleRelease":
    cdn_base_url = urljoin(settings.CDN_BASE_URL, f"{app.name}/{self.version}/")
    release, _ = WebBundleRelease.objects.get_or_create(app=app, version=self.version)
    release.author = self.author
    release.description = self.description
    release.license = self.license
    release.tags = self.tags
    release.bundle_hash = self.bundle_hash
    release.active = True
    release.save()

    if not app.has_releases:
        app.has_releases = True
    app.latest_release_date = release.created
    _copy_bundle_to_storage(self.bundle, destination=f"{app.name}/{self.version}/")
    write_manifest_json(release)
    app.save()
```

### 4.5 Service — `ServiceAppPending` / `ServiceRelease`
Lifecycle-bearing models for the Service pipeline (§3.3). No SSRF-relevant fields are exposed to the submitter beyond the endpoint URL itself — the private-IP check (§8.2) happens at request time, not as a stored/validated field constraint.

### 4.6 Automated & human review (designed, not yet implemented)

```python
class AutomatedReview(models.Model):
    pending = models.OneToOneField(WebBundlePending, on_delete=models.CASCADE)
    status = models.CharField(choices=[('pending','Pending'),('running','Running'),
                                        ('passed','Passed'),('failed','Failed')])
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    report = models.JSONField(default=dict)

class AutomatedCheck(models.Model):
    review = models.ForeignKey(AutomatedReview, on_delete=models.CASCADE, related_name='checks')
    name = models.CharField(max_length=64)
    result = models.CharField(choices=[('pass','Pass'),('warning','Warning'),('fail','Fail')])
    details = models.JSONField(default=dict)

class HumanReview(models.Model):
    pending = models.ForeignKey(WebBundlePending, on_delete=models.CASCADE, related_name='human_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    decision = models.CharField(choices=[('approve','Approve'),('reject','Reject'),
                                          ('request_changes','Request Changes')])
    reviewed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
```

`HumanReview` is a `ForeignKey`, not `OneToOne` — a `REQUEST_CHANGES` decision doesn't terminate the pending row's lifecycle, so one submission may accumulate multiple review rounds and the audit trail keeps all of them.

---

## 5. View Changes

### 5.1 Page-generation functions
Separate functions per app type: `_mk_app_page(...)` (Desktop), `_mk_web_page(...)` (Web), `_mk_service_page(...)` (Service).

### 5.2 POST/action-handling pattern
Both Web and Service page functions follow the existing App Store convention: retrieve `action` from POST → validate it's recognized → execute → convert `ValueError` to `400 Bad Request` → return JSON for AJAX, otherwise render normally.

### 5.3 Confirm-view pattern (bundle mechanism)

```python
def confirm_web_bundle(request, id):
    pending = get_object_or_404(WebBundlePending, id=int(id))
    if not (request.user.is_staff or request.user == pending.submitter):
        return HttpResponseForbidden('You are not authorized to view this page')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'cancel':
            return _bundle_user_cancelled(request, pending)
        elif action == 'accept':
            pending.status = WebBundlePending.Status.PENDING_REVIEW
            pending.save()
            return _bundle_user_accepted(request, pending)

    return html_response("confirm_webapp.html", {'pending': pending}, request)
```

`_bundle_user_accepted` branches on whether an `App` with the same name/platform already exists and is editable by the current user — redirecting into the existing app's edit-with-upload-release flow, or rendering a generic "submission received" page for a brand-new app pending review.

### 5.4 Known view-layer issue: cross-pipeline dispatch
See §10.4 — a dispatcher that looks up a bare `id` across `WebUrlPending`/`WebBundlePending` without knowing the origin in advance is unsafe, since `get_object_or_404` raises immediately on a miss and the two tables can independently contain the same numeric id.

---

## 6. Template Changes

### 6.1 Context differences by app type

**Web page context:**
```text
app, releases, latest_release, cdn_base_url, is_editor,
bundle_latest_release, go_back_to_title, go_back_to_url, install_url
```

**Service page context:**
```text
app, service_endpoint, is_editor, service_latest_release,
go_back_to_title, go_back_to_url, service_install
```

### 6.2 Release-variable distinction
`app.get_releases()` (the general/legacy release collection) does **not** necessarily represent the latest Web bundle or Service release. Templates must use the type-specific variable — `{{ bundle_latest_release.version }}` for Web, `{{ service_latest_release.version }}` for Service — rather than assuming the generic release list's ordering matches.

### 6.3 Install URL generation
```python
@property
def install_url(self):
    return (
        "https://dev1.ndexbio.org/cytoscape/?installApp="
        + quote(self.manifest_url, safe="")
    )
```
Generated from the release version and manifest path; the Service equivalent is built from the stored service endpoint.

---

## 7. Storage, CDN & Manifest Generation

### 7.1 Storage layout
```text
/web/
    <app-name>/
        <version>/
            manifest.json
            remoteEntry.js
            main.mjs
            assets/
```
Published release URLs are intended to remain **immutable** — a `<app-name>/<version>` path always resolves to the same bytes once published, so previously-installed clients don't silently pick up different code. This is why resubmission uses a new version rather than overwriting an existing one.

### 7.2 Pending vs. published separation
Pending/temporary storage lives under a `pending/` namespace, distinct from the published namespace:
```python
@property
def bundle_path(self):
    return f"pending/{fullname_to_name(self.fullname)}/{self.version}/"
```
`delete_files()` asserts this path starts with `pending/` before deleting, guarding against a future refactor accidentally pointing cleanup at published storage. This separation ensures an unapproved bundle can never become publicly accessible merely by having been uploaded.

### 7.3 Manifest generation
`manifest.json` is generated by the App Store from the **approved `WebBundleRelease` record** — not taken from anything the developer uploads. It's built from: submission-form metadata carried onto the release (`fullname`, `author`, `description`, `license`, `tags`), `version`, identity fields (`app.name`/`CyApp.id`, matching `AppConfig.id`/MF scope), `cdn_base_url` (feeding the derived `remote_entry_url`), and `bundle_hash`. `write_manifest_json(release)` runs as the final step of `make_bundle_release`, after the CDN copy — so the manifest is written from the release row's fields only after the bundle is actually in place.

An earlier design bundled `app-store.json`/`manifest.json` inside the zip itself; this was dropped because a mismatch between an embedded manifest and the submission form would be unresolvable, and the submitter isn't necessarily the manifest's original author. Generating it App-Store-side guarantees the public manifest always corresponds exactly to what was reviewed — a submitter can't post-approval swap install metadata by re-uploading just a manifest file.

Manifest URL: `/web/<app-name>/<version>/manifest.json`.

### 7.4 Pending-state lifecycle
```text
DEFAULT → PENDING_CONFIRMATION → PENDING_AUTOMATED_CHECKS
              │
    ┌─────────┴─────────┐
CHECKS_FAILED        (pass) → PENDING_REVIEW → Human Review
    │                                                │
Fix / Reject                          ┌──────────────┴──────────────┐
                                    Reject                       Approve → PUBLISHED
```
`PUBLISHED`/`REJECTED` are intentionally not modeled as `WebBundlePending.Status` values — publication transitions a row out of the pending table entirely (into `WebBundleRelease` via `make_bundle_release`), and rejection deletes the pending row. A partial unique index on `status=PUBLISHED` (not all rows) allows resubmission at the same version after a prior failure/rejection.

---

## 8. Security Considerations

### 8.1 Web bundle risk surface
Third-party JavaScript executes inside the host environment. Automatically detectable risk signals (evidence, not verdicts): `eval()`, `new Function()`, `innerHTML` assignment, `document.cookie`, `localStorage`/`sessionStorage` access, `fetch()`/`XMLHttpRequest` usage and target domains, known-vulnerable dependencies, deprecated/raw host API usage.

Risks requiring human judgment: *why* does this app need `localStorage`; is this external domain legitimate; is this DOM manipulation actually unsafe in context; is a flagged vulnerability actually exploitable given how the app uses the dependency; is a requested API appropriate for the app's stated purpose. The automated system's job is to make these questions cheap to ask, not to answer them.

### 8.2 Service endpoint SSRF mitigation
Server-side requests to an arbitrary submitter-provided URL are an SSRF vector. Rejected heavyweight mitigations (urllib3 DNS-pinning, custom `HTTPAdapter`) in favor of a ~60-line private-IP check using `requests`, `socket`, and `ipaddress`: resolve the hostname, reject if the resolved address falls in RFC 1918/loopback/link-local ranges, otherwise proceed with a plain `requests.get`. A `settings.DEBUG`-gated `allow_local` flag permits local service registration during development.

### 8.3 Storage-layer enforcement
See §7.2 — the `pending/` vs. published namespace split is the storage-layer half of "upload ≠ publication." No current safeguard prevents the `pending/` namespace from being accidentally served publicly via an Apache misconfiguration beyond code review — an explicit Apache `deny` rule on `pending/` would make this defense-in-depth rather than application-layer-only (tracked as not yet implemented, §11).

### 8.4 Portability as a security-adjacent goal
An app that directly accesses host internals (private Redux state, non-exported MF internals) is coupled to a specific host build and can break, or behave unexpectedly, on host upgrades. Public-API-usage detection, deprecated-API scanning, raw-Store-import detection, and `compatibleHostVersions` validation are all facets of the same underlying question: does the app declare and respect a stable host contract, or silently depend on current internals.

---

## 9. Automated Checks

Each check should produce `PASS / WARNING / FAIL`. Hard failures block publication; warnings are surfaced to the human reviewer for judgment.

| Check | What it verifies | Blocking? |
|---|---|---|
| Bundle structure | Zip extracts cleanly; required files present | Hard fail |
| `./AppConfig` load test | MF container loads and resolves `./AppConfig` | Hard fail |
| Application identity | `CyApp.id == AppConfig.id == MF scope` | Hard fail |
| React/ReactDOM/MUI compatibility | Shared-dependency versions vs. supported host env | Warning |
| `compatibleHostVersions` | Valid semver range — Store is stricter than the host, which may treat unparsable ranges as compatible-with-warning | Hard fail |
| `@cytoscape-web/api-types` | Detects usage + version | Informational |
| Public API usage | Which host APIs the app depends on | Informational |
| Deprecated/raw Store usage | Direct/raw Store imports vs. public API — a portability signal (§8.4) | Warning |
| Bundle size | Absolute size + delta vs. previous published version | Warning above a size-increase threshold |
| Dependency vulnerabilities | Severity-classified (Critical/High/Medium/Low) | Blocking policy configurable per severity |
| License report | Flags potentially incompatible dependency licenses | Warning |
| Security pattern scan | `eval()`, `new Function()`, `innerHTML`, cookie/storage access | Warning |
| Network domain detection | Domains contacted via `fetch()`/`XMLHttpRequest` | Warning on new/unexpected domains |

### 9.1 `./AppConfig` load test — implementation notes
Must verify the module can actually be **loaded**, not merely that `remoteEntry.js` exists — a bundle can contain a syntactically valid `remoteEntry.js` while still failing `container.get("./AppConfig")` at runtime. Sequence: load `remoteEntry.js` → initialize MF container → request `./AppConfig` → execute → validate returned config. Better implemented as a Node.js validator invoked via `subprocess` (the runtime concept is inherently JS-based) with a Playwright-based browser validator as a secondary option if DOM/`window` globals are needed during config evaluation.


---

## 10. Known Issues & Bugs

### 10.1 Service pipeline
- `_service_accepted` was deleting rows instead of setting `VALIDATED`.
- `check_reachable` returning `None` silently instead of `False`.
- Duplicate pending-row creation on resubmission; wrong spec field name (`name` vs `fullname`); `_service_accepted` not returning its response value.

### 10.2 Web bundle mechanism
- Submit button rendered outside `</form>`; missing `context['form']` on GET; `form.non_field_errors` not rendered; `NameError` on `contains_app_store_json`; variable-name collision in the `remoteEntry.js` generator.

### 10.3 Web URL mechanism (parked, bugs found while wiring the stub)
- `_create_web_url_pending` never called `.save()` → `pending.id = None` → `NoReverseMatch` on redirect.
- `confirm_web_url`'s cancel action called `_bundle_user_cancelled` (calls `.delete_files()`, which `WebUrlPending` doesn't implement) instead of `_url_user_cancelled`.
- A submission was routed to `confirm_web_bundle` for an id that only existed in `WebUrlPending` → `No WebBundlePending matches the given query` — traced to the confirm template/redirect pointing at the wrong endpoint (see §10.4).

### 10.4 Cross-pipeline ID collision (recurring pattern)
`AppPending`/`ServiceAppPending` and, later, `WebUrlPending`/`WebBundlePending` each use independent `BigAutoField`s — two unrelated rows in sibling tables can hold the same numeric `id` simultaneously. A dispatcher that looks up a bare `id` without knowing the origin in advance is unsafe:

```python
# BROKEN — get_object_or_404 raises immediately on a miss, so this
# never reaches the second lookup; and even if it did, both tables
# can independently contain id=N.
def confirm_webapp(request, id):
    pending_url = get_object_or_404(WebUrlPending, id=int(id))
    pending_bundle = get_object_or_404(WebBundlePending, id=int(id))
    ...
```

This directly caused the §10.3 bugs. Three architectural fixes were evaluated:

- **A — status quo, two separate tables.** Duplicates lifecycle logic (confirm view, review queue) across near-identical models; source of the collision bugs.
- **B — single table, `origin`-discriminated, mechanism-specific fields nullable.** One shared id space, one confirm view branching only where fields differ. Minor cost: a few null columns.
- **C — base + one-to-one detail tables.** Fully normalized, zero nulls, requires joins for mechanism-specific reads.

**Interim decision:** since the URL mechanism is parked (storage only), building B or C now is premature. `origin` (already present on both models, §4.2–4.3) is the hook that lets this converge to Option B additively once the URL mechanism needs real handling, rather than requiring a destructive migration later. This is tracked technical debt, not an oversight — collision bugs should be expected to resurface in any new code path touching both pending tables until the merge happens.

### 10.5 Database/migration: `WebUrlPending.submitter` FK
`OperationalError 1005` on table creation. Root cause: this deployment's `auth_user.id` is `bigint(20)` (widened outside Django's own migration history at some point), while Django's FK-column-type inference for `ForeignKey(User)` always generates `int(11)`, since it reads `django.contrib.auth.models.User`'s hardcoded `AutoField` definition rather than the live column — a mismatch invisible to Django, so `makemigrations`/`migrate` regenerates `int` indefinitely regardless of the real column type.

**Resolution:** `migrations.SeparateDatabaseAndState` — `state_operations` records an ordinary `ForeignKey` (default `db_constraint=True`, keeping the model workaround-free) while `database_operations` hand-writes `CREATE TABLE` with `submitter_id BIGINT` and a real `FOREIGN KEY ... REFERENCES auth_user(id)`, correct in one pass.

---

## 11. Infrastructure & Deployment

### 11.1 Apache configuration
```apache
Alias /web /var/www/appstore/web_bundle_storage
AddType application/javascript .js .mjs
```
Browsers reject JS modules served with the wrong MIME type. This surfaced as a real bug — `main.mjs`/`remoteEntry.js` returning `Content-Type: text/html`, causing `Expected a JavaScript-or-Wasm module script`. Root cause was Apache routing the request through the wrong handler/path, not solely a missing `AddType` directive. **Apache requires a reload/restart after config changes** to take effect — worth calling out explicitly in deployment runbooks, since an edit with no reload silently does nothing.

### 11.2 Deployment checklist
- Apache alias + MIME-type configuration for `/web`
- JS/JSON MIME types (`.js`, `.mjs`, `manifest.json`)
- Web bundle storage directories (`pending/` and published, kept separate per §7.2)
- CDN/public bundle URLs
- Manifest URL routing
- Apache reload/restart after any config change
- (Not yet implemented) `deny` rule on the `pending/` namespace, per §8.3

---

## 12. Implementation Status

**Implemented / actively integrated:** app-type distinction (`App.platform`); Web/Service page/view handling; `WebBundlePending`, `WebBundleRelease`, `ServiceAppPending`, `ServiceRelease` models; bundle upload + structural validation; pending storage + confirm-page flow; Service endpoint storage, dual reachability checks, SSRF mitigation; type-specific latest-release retrieval and templates; Apache hosting with corrected MIME types; `origin` field on both Web pending models; `WebUrlPending` stub (storage-only, `.save()` bug fixed).

**Designed / not yet implemented:** automated review pipeline (`AutomatedReview`/`AutomatedCheck`, all §9 checks); `./AppConfig` load-test validator (approach pending confirmation against ESM-based bundles); `HumanReview` model + reviewer UI; CDN publication (no infra stood up); GitHub URL mechanism (ref resolution, build step, confirm branching); `WebUrlPending`/`WebBundlePending` unification (§10.4); Apache `deny` rule on `pending/`.

**Open/unresolved bugs:** Desktop `confirm_submission` test failures (§10.6); `weburlpending` charset mismatch (§10.5).

---

## 13. Target Review Pipeline

```text
Web Bundle Upload → Create Pending Bundle → Extract Bundle
                                                   │
                                    ┌──────────────┼──────────────┐
                                Structure      AppConfig       Security
                                Validation       Load          Analysis
                                    └──────────────┼──────────────┘
                                                   ▼
                                           AutomatedReview
                                                   │
                                        ┌──────────┴──────────┐
                                      FAIL                   PASS
                                        │                       │
                                  Fix/Reject             Human Review
                                                                 │
                                                    ┌────────────┴────────────┐
                                                 Reject                   Approve
                                                                              │
                                                                    Create Release
                                                                              │
                                                                    Generate Manifest
                                                                              │
                                                                        Publish CDN
```

Intended to be reusable by both the bundle-upload and (once built out) GitHub-URL mechanisms from "Extract Bundle" onward — the two should differ only in how the bundle is *obtained*, not in how it's validated, reviewed, or published.