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

**4.4.1 - Intentions for Web Apps**
Currently, the only release model for web applications is `WebBundleRelease`, however this is solely due to the fact that `WebUrlRelease` does not exist. Once the repository submission mechanism is implemented, `WebBundlePending` and `WebUrlPending` will converge on the same release model e.g. `WebAppRelease`.

### 4.5 Service — `ServiceAppPending` / `ServiceRelease`
Lifecycle-bearing models for the Service pipeline (§3.3). No SSRF-relevant fields are exposed to the submitter beyond the endpoint URL itself — the private-IP check (§8.2) happens at request time, not as a stored/validated field constraint.

---

## 5. View Changes

### 5.1 Page-generation functions
Separate functions per app type: `_mk_app_page(...)` (Desktop), `_mk_web_page(...)` (Web), `_mk_service_page(...)` (Service).

### 5.2 Platform-aware POST/action handling

Web and Service page views follow the existing App Store action pattern:

1. Read `action` from `request.POST`.
2. Validate that the action is recognized for that platform.
3. Execute the platform-specific action handler.
4. Convert expected `ValueError` failures to `400 Bad Request`.
5. Return JSON for AJAX requests; otherwise render/redirect normally.

Actions must not accidentally fall through to Desktop release logic. Platform checks should happen before operating on a release or pending object.

### 5.3 Web bundle submission and confirmation views

The functional Web bundle flow adds a confirmation step between upload and acceptance/review.

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

The confirmation view must:

- retrieve the `WebBundlePending` row using the correct model;
- enforce staff-or-submitter authorization;
- support cancel and accept actions;
- transition an accepted submission into the review workflow rather than directly publishing it;
- route an existing editable app into the appropriate edit-with-upload-release flow; and
- show a generic submission-received page for a new app awaiting review.

The bundle flow also requires the upload/submit view to pass the form into the template on GET, render non-field validation errors, and keep the submit button inside the form. These were real integration issues encountered while wiring the flow.

### 5.4 Service submission and acceptance views

Service submissions use their own pending/release pipeline and must not reuse Web bundle storage or release lookup logic. The view layer handles:

```text
submission
   ↓
synchronous reachability check
   ↓
ServiceAppPending
   ↓
confirmation / acceptance
   ↓
VALIDATED
   ↓
out-of-band checker
   ↓
CHECKER_PASSED → review/approval → ServiceRelease
```

The synchronous reachability check is intentionally lightweight. The authoritative `check_service_apps` management command performs reachability, `/status` health checks, specification validation, and consistency checks outside the request/response cycle.

The Service acceptance view must update the pending object's lifecycle state rather than deleting the row. A previous implementation incorrectly deleted accepted rows instead of moving them to `VALIDATED`.

The Service views also need to return the response generated by their helper functions. A missing return from `_service_accepted` was one of the integration bugs encountered during implementation.

### 5.5 Web URL submission views — parked mechanism

`WebUrlPending` remains a parked submission mechanism. Its submission view currently captures and stores the repository URL/ref information but does not implement the build/retrieval pipeline.

The intended view flow is:

```text
Web URL submission
      ↓
WebUrlPending
      ↓
retrieve/ref-resolve/build (not yet wired)
      ↓
shared validation/review/publish pipeline
```

Known view issues in this parked path include:

- `_create_web_url_pending` originally failed to call `.save()`, leaving `pending.id = None` and causing `NoReverseMatch` during redirect;
- `confirm_web_url` originally called `_bundle_user_cancelled`, even though `WebUrlPending` does not implement the bundle storage cleanup contract; and
- a Web URL submission was routed to `confirm_web_bundle`, producing `No WebBundlePending matches the given query` because the redirect/confirm endpoint did not preserve the submission origin.

These are symptoms of the cross-pipeline dispatch problem described below.

### 5.6 Cross-pipeline ID dispatch

`AppPending`, `ServiceAppPending`, `WebUrlPending`, and `WebBundlePending` use independent `BigAutoField` sequences. Therefore, the same numeric ID can legitimately exist in multiple pending tables.

This is unsafe:

```python
# BROKEN
pending_url = get_object_or_404(WebUrlPending, id=int(id))
pending_bundle = get_object_or_404(WebBundlePending, id=int(id))
```

`get_object_or_404()` raises immediately when the first table has no match, and even a fallback lookup would be ambiguous when both tables contain the same ID.

The correct approach is to preserve the pipeline/origin in the URL or dispatch context and query exactly one model. For example, the confirm route should conceptually distinguish:

```text
/web/confirm/bundle/<id>/
/web/confirm/url/<id>/
```

or use an equivalent explicit origin parameter. The `origin` field already present on Web pending models is the schema hook for eventually consolidating the two mechanisms.

`make_bundle_release(...)`, which copies the approved bundle into the published storage namespace, updates the application/release metadata, and generates the App-Store-owned `manifest.json` from the approved release record. The view must not trust an uploaded manifest as the source of publication metadata.

The Web release URL structure is versioned and immutable:

```text
/web/<app-name>/<version>/
```

Service publication stores the external service endpoint rather than a bundle.

### 5.8 Download and install views

The download endpoint must now distinguish between externally downloaded Desktop releases and Web/Service installations.

Desktop continues to use:

```python
def release_download(request, app_name, version):
    app = get_object_or_404(App, name=app_name, platform=Platform.DESKTOP)
    release = get_object_or_404(Release, app=app, version=version, active=True)
    _record_download(app, release, Download, ReleaseDownloadsByDate)
    return HttpResponseRedirect(release.release_file_url)
```

Web and Service apps use an install endpoint because there is no Desktop release file to download:

```python
def release_install(request, app_name, version):
    app = get_object_or_404(App, name=app_name)

    if app.platform == 'service':
        release = get_object_or_404(
            ServiceRelease, app=app, version=version, active=True
        )
        _record_download(
            app, release, ServiceDownload, ServiceReleaseDownloadsByDate
        )
        return HttpResponseRedirect(release.service_endpoint)

    elif app.platform == 'web':
        release = get_object_or_404(
            WebBundleRelease, app=app, version=version, active=True
        )
        _record_download(
            app, release, WebBundleDownload, WebBundleReleaseDownloadsByDate
        )
        return HttpResponseRedirect(release.install_url)

    raise Http404
```

The URL configuration must distinguish the action prefix. A generic two-segment pattern such as:

```python
re_path(r'^(\w{1,100})/(.{1,31})$', release_download, name='release_download')
```

must not also be used unchanged for `release_install`, because the install URL contains the explicit `install/` prefix. The intended routing is conceptually:

```text
/download/<app-name>/<version>/             → release_download
/download/install/<app-name>/<version>/     → release_install
```

The install view therefore owns Web/Service redirects, while the Desktop download view remains restricted to `Platform.DESKTOP`.

### 5.9 Download recording changes

The shared `_record_download(...)` helper is used by all three release types, but its download model and per-date statistics model are platform-specific:

```text
Desktop → Download → ReleaseDownloadsByDate
Web     → WebBundleDownload → WebBundleReleaseDownloadsByDate
Service → ServiceDownload → ServiceReleaseDownloadsByDate
```

The helper increments `App.downloads`, records the individual download/install event, and increments the release-specific and all-release daily counters.

The helper must receive `request` if it derives the client IP address from the request. A previous implementation referenced `request` inside `_record_download` without accepting it, producing `NameError`. The view should therefore pass the request explicitly:

```python
def _record_download(request, app, release, download_model, by_date_model):
    ip4addr = _client_ipaddr(request)
    ...
```

All callers must then use:

```python
_record_download(request, app, release, ...)
```

### 5.10 Service/Web install URL behavior

Web release installation uses the release's `install_url` property rather than redirecting directly to a service endpoint. The URL ultimately points Cytoscape Web at the App Store-hosted manifest for the selected release.

For Service Apps, the installation target is the external service endpoint. If the Service pending model has an install URL helper that wraps the endpoint, the release model should expose the corresponding release-level property so the view does not depend on a pending-row object after publication.

The important view-layer rule is that the redirect target is derived from the **published release**, not from the pending submission.

Another thing to note is the future possiblity of service app support in Cytoscape 3, which requires a different install behavior from Cytoscape Web. This is still currently under development, however it should be noted that all data will be the same across both options `(version, release history, etc)`.

### 5.11 URL configuration requirements

The platform expansion therefore requires URL patterns for at least:

```text
Desktop app page
Web app page
Service app page
Web bundle submission
Web bundle confirmation
Web URL submission (parked)
Web URL confirmation (parked)
Service submission
Service confirmation/acceptance
Desktop release download
Web release install
Service release install
```

Every URL that accepts a pending-row ID must identify the pipeline/origin explicitly. Every release download/install URL must identify the release action explicitly enough that Django cannot route an install request into `release_download` or vice versa.


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

### 6.4 `app_page.html` — release list loop and download/install links
 
**Original (Desktop-only) block:**
```django-html
{% if app.platform == 'desktop' %}
<a href="{% url 'release_download' app.name release.version %}">
    {{ release.version }}
</a>
{% else %}
{{ release.version }}
{% endif %}
```
For Web/Service releases, the version rendered as **plain, unlinked text** — nothing in the page could trigger a download/install action for those platforms, which was the direct cause of "clicking doesn't increment the download count" for non-Desktop apps: there was no click target to begin with.

**Final control flow** — `release_download` stays Desktop-only; Web/Service route through a separate `release_install` URL:
```django-html
{% if app.platform == 'desktop' %}
<a href="{% url 'release_download' app.name release.version %}">
{% else %}
<a href="{% url 'release_install' app.name release.version %}">
{% endif %}
    {{ release.version }}
</a>
```
 **Loop source changed** from a Desktop-only related manager to a unified accessor so one loop body serves all three platforms:
```django-html
{% for release in app.get_releases %}
```
`get_releases` (equivalent in intent to an `all_releases` property) branches internally on `app.platform` to return `release_set` / `webbundlerelease_set` / `servicerelease_set` as appropriate, so the template doesn't need a platform `{% if %}` around the loop itself — only around the parts of the release detail block that are genuinely platform-specific (see below).
 
**Fields inside the loop that remain conditionally Desktop-only**, since Web/Service releases don't populate them:
```django-html
{% if release.releaseapi_set.count %}
{% with releaseapi=release.releaseapi_set.get %}
<p><strong>API</strong> ... pom.xml / Javadocs links ... </p>
{% endwith %}
{% endif %}
 
{% if release.dependents.count %}
<p><strong>Apps that depend on this release</strong> ... </p>
{% endif %}
```
`release.works_with` and `release.created_iso` render blank (not an error) for Web/Service releases if those fields/properties don't exist on `WebBundleRelease`/`ServiceRelease` — flagged as a cosmetic cleanup item, not a functional bug, since Django templates fail silently on missing attributes rather than raising.

### 6.5 Separate submission forms, shared confirm-page shape
`web_bundle_upload_form.html` (bundle mechanism) and `web_url_upload_form.html` (URL mechanism, parked) remain separate templates, matching their separate views (`submit_web_bundle` / `submit_web_url`) and separate forms (`web_bundle_submission` / `web_url_form`) — no shared submission template exists yet. `confirm_webapp.html`, by contrast, is shared: both `confirm_web_bundle` and (once wired correctly per §6.6) `confirm_web_url` render into it, with `{{ pending }}`'s fields differing by which pending model was passed in. This asymmetry — separate submission forms, one shared confirm template — is a direct consequence of the submission forms collecting genuinely different fields (`repo_url` vs. `bundle` upload) while the confirm/accept/cancel flow itself is close to identical across mechanisms.



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

### 7.4 Intended Pending-state lifecycle
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

### 10.6 Database/migration: download statistics unique constraints and duplicate cleanup

`ReleaseDownloadsByDate` stores the per-release daily download count. The intended schema enforces one row per `(release, when)` pair:
```python
class ReleaseDownloadsByDate(Model):
    release = ForeignKey(Release, on_delete=models.CASCADE, null=True)
    when = DateField()
    count = PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['release', 'when'],
                name='release_unique_by_date'
            )
``` 
`release=None` is used for the total download count across all releases for a given day. The same uniqueness pattern is used for the new Service and Web download-stat tables:
```python
class ServiceReleaseDownloadsByDate(models.Model):
    release = ForeignKey(ServiceRelease, on_delete=models.CASCADE, null=True)
    when = DateField()
    count = PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['release', 'when'],
                name='service_release_unique_by_date'
            )
        ]


class WebBundleReleaseDownloadsByDate(models.Model):
    release = ForeignKey(WebBundleRelease, on_delete=models.CASCADE, null=True)
    when = DateField()
    count = PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['release', 'when'],
                name='web_release_unique_by_date'
            )
        ]
```
**Migration History**

On apps-stage.cytoscape.org, The `download` migration sequence is:
```text
0003
  ↓
0004_servicedownload_servicereleasedownloadsbydate_and_more
  ├── Create ServiceDownload
  ├── Create ServiceReleaseDownloadsByDate
  ├── Create WebBundleDownload
  ├── Create WebBundleReleaseDownloadsByDate
  ├── Add release_unique_by_date to ReleaseDownloadsByDate
  ├── Add release FKs to the new Web/Service download tables
  └── Add web_release_unique_by_date and service_release_unique_by_date
```
The corrected `0004` therefore adds `release_unique_by_date` directly and does not contain (if migration files contains this statement, remove it):
```python
migrations.RemoveConstraint(
    model_name='releasedownloadsbydate',
    name='unique_by_date',
)
```
### Checking the live database before applying the constraint:
The database schema must be checked independently of Django's migration state:
```sql
SHOW INDEX FROM download_releasedownloadsbydate;
```
A unique `(release_id, when)` constraint should appear as a non-unique (`Non_unique = 0`) composite index containing both columns. If the old `unique_by_date` constraint is absent, do not create a migration that attempts to remove it.

Cleaning existing duplicate rows
Before adding `release_unique_by_date`, all existing duplicate `(release_id, when)` pairs must be merged. The table can contain millions of rows, so first add a temporary composite index:
```sql
CREATE INDEX temp_release_when
ON download_releasedownloadsbydate (release_id, `when`);
```
Then identify duplicate release/date pairs:
```sql
SELECT
    release_id,
    `when`,
    COUNT(*) AS duplicate_count,
    SUM(count) AS total_count
FROM download_releasedownloadsbydate
GROUP BY release_id, `when`
HAVING COUNT(*) > 1;
```
Inspect the actual rows before modifying them:
```sql
SELECT id, release_id, `when`, count
FROM download_releasedownloadsbydate
WHERE (release_id, `when`) IN (
    (57, '2026-06-25'),
    (96, '2026-03-21'),
    (223, '2026-04-10'),
    (310, '2026-06-03'),
    (383, '2026-08-17'),
    (661, '2026-06-22'),
    (692, '2026-06-12'),
    (716, '2026-06-12'),
    (740, '2026-05-24'),
    (795, '2026-04-09'),
    (798, '2026-06-14'),
    (871, '2026-06-04'),
    (935, '2026-06-14'),
    (938, '2026-06-29'),
    (947, '2026-06-07'),
    (1012, '2026-06-17'),
    (1120, '2026-06-28'),
    (1153, '2026-04-29'),
    (1240, '2026-03-19'),
    (1277, '2026-06-09')
)
ORDER BY release_id, `when`, id;
```
For the duplicate set encountered during implementation, each pair consisted of one row with `count = 2` and one row with `count = 1`. The correct cleanup is to preserve the total count (`3`) rather than deleting one row and losing a download.
Before modifying the data, make a backup from the Linux shell, not from inside the MariaDB prompt:
```bash
mysqldump -u appstoreuser -p AppStore download_releasedownloadsbydate \
    > /tmp/releasedownloadsbydate_backup.sql
```
Verify the backup:
```bash
ls -lh /tmp/releasedownloadsbydate_backup.sql
```
Then merge duplicate counts while keeping the lowest-ID row:
```sql
UPDATE download_releasedownloadsbydate a
JOIN (
    SELECT
        release_id,
        `when`,
        MIN(id) AS keep_id,
        SUM(count) AS total_count
    FROM download_releasedownloadsbydate
    GROUP BY release_id, `when`
    HAVING COUNT(*) > 1
) b
    ON a.id = b.keep_id
SET a.count = b.total_count;
```
Delete the duplicate rows, keeping the lowest ID for each release/date pair:
```sql
DELETE a
FROM download_releasedownloadsbydate a
JOIN download_releasedownloadsbydate b
    ON a.release_id = b.release_id
    AND a.`when` = b.`when`
    AND a.id > b.id;
```
Verify that no duplicate release/date pairs remain:
```sql
SELECT
    release_id,
    `when`,
    COUNT(*) AS duplicate_count,
    SUM(count) AS total_count
FROM download_releasedownloadsbydate
GROUP BY release_id, `when`
HAVING COUNT(*) > 1;
```
The expected result is:
```text
Empty set
```
After the data is clean, apply the Django migration:
```bash
python manage.py migrate download
```
Verify the resulting database index:
```sql
SHOW INDEX FROM download_releasedownloadsbydate;
```
Once `release_unique_by_date` exists and the migration has succeeded, the temporary index can be removed:
```sql
DROP INDEX temp_release_when
ON download_releasedownloadsbydate;
```
The temporary index should not be removed until the duplicate cleanup and migration are complete.

If the migration (e.g. `0004`) partially created its four new tables before failing, remove only those partially-created tables before retrying `0004`:
```sql
DROP TABLE IF EXISTS download_servicedownload;
DROP TABLE IF EXISTS download_servicereleasedownloadsbydate;
DROP TABLE IF EXISTS download_webbundledownload;
DROP TABLE IF EXISTS download_webbundlereleasedownloadsbydate;
```
Do not drop `download_releasedownloadsbydate`, because it contains the existing historical download statistics that must be cleaned and retained.
Check migration state with:
```bash
python manage.py showmigrations download
```
After correcting the migration and cleaning duplicate data, `0004` can be applied normally.


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
- (Not yet implemented) `deny` rule on the `pending/` namespace, per §8.3

---

## 12. Implementation Status

**Implemented / actively integrated:** app-type distinction (`App.platform`); Web/Service page/view handling; `WebBundlePending`, `WebBundleRelease`, `ServiceAppPending`, `ServiceRelease` models; bundle upload + structural validation; pending storage + confirm-page flow; Service endpoint storage, dual reachability checks, SSRF mitigation; type-specific latest-release retrieval and templates; Apache hosting with corrected MIME types; `origin` field on both Web pending models;

**Designed / not yet implemented:** automated review pipeline (`AutomatedReview`/`AutomatedCheck`, all §9 checks); `./AppConfig` load-test validator (approach pending confirmation against ESM-based bundles); `HumanReview` model + reviewer UI; CDN publication (no infra stood up); GitHub URL mechanism (ref resolution, build step, confirm branching); `WebUrlPending`/`WebBundlePending` unification (§10.4); Apache `deny` rule on `pending/`.


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