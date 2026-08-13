# Submitting Apps to the Cytoscape App Store

A quick guide for developers submitting a **Web App** or **Service App**.

---

## Web Apps

Web Apps are bundles loaded dynamically by Cytoscape Web via Module Federation.

### Before you submit

Make sure your build:
- Produces a `remoteEntry.js` file and exposes an `./AppConfig` module
- Has a consistent app identity across three places — these **must match**:
  - `CyApp.id`
  - `AppConfig.id`
  - Your Module Federation scope/name
- Declares a valid `compatibleHostVersions` semver range

### Steps

1. **Build your app.** Run your production build (e.g. `npm run build`). This should generate a `dist` folder containing `remoteEntry.js`, `main.mjs`, and any other assets your app needs.
2. **Package your bundle from the `dist` folder.** Zip the **contents of `dist`** (not the `dist` folder itself, and not your source/`node_modules`) — `remoteEntry.js` must sit at the root of the zip, not nested inside a subfolder. Max size: **50 MB**.
3. **Go to the Web App submission form.**
4. **Fill out the form:**
   - App name
   - Version
   - Author(s)
   - Description (optional)
   - License
   - Tags (optional, comma-separated)
   - Upload your `.zip` bundle
5. **Submit.** The Store validates your bundle structure automatically (zip integrity, safe file paths, presence of `remoteEntry.js`). If validation fails, you'll see the specific error on the form — fix it and resubmit.
6. **Confirm your submission** on the confirmation page that follows.
7. **Wait for review.** Your submission enters the pending queue for review before publication. You'll be notified of the outcome.

### If you need to resubmit
If your submission is rejected or fails checks, you can resubmit the **same version number** — it isn't permanently blocked. Only published versions are locked.

### Common rejection reasons
- App identity mismatch (`CyApp.id` / `AppConfig.id` / MF scope don't agree)
- Missing or unloadable `./AppConfig` module
- Unparsable `compatibleHostVersions`
- Bundle exceeds 50 MB
- Zip contains unsafe paths (e.g. `../`)
- Zipped the wrong folder (source files, `node_modules`, or `dist` nested a level too deep instead of its contents)

---

## Service Apps

Service Apps are backed by an external service endpoint you host and maintain — not a bundle.

### Before you submit

Make sure your service:
- Is publicly reachable (not on a private/internal network — the Store cannot reach `localhost` or private IP ranges)
- Exposes a working `/status` health check endpoint
- Matches whatever spec format the Store validates against

### Steps

1. **Deploy your service** somewhere publicly reachable.
2. **Go to the Service App submission form.**
3. **Provide your service endpoint URL** and any required metadata.
4. **Submit.** The Store does a quick reachability check immediately — if your endpoint is unreachable, you'll be told right away.
5. **Wait for automated validation.** A more thorough check runs afterward: reachability, `/status` health check, spec validation, and consistency checks.
6. **Wait for review/approval.**

### Common rejection reasons
- Endpoint unreachable or times out
- `/status` check fails
- Spec validation fails (malformed or missing required fields)
- Endpoint resolves to a private/internal IP

---

## Which one should I submit?

| | Web App | Service App |
|---|---|---|
| What you provide | A built JS bundle | A hosted service endpoint |
| Runs where | Inside the Cytoscape Web host | On your own infrastructure |
| Update process | Upload a new version | Update your service directly |

---
