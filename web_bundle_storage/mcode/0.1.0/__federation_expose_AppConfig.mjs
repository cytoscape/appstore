export const __webpack_esm_id__ = 315;
export const __webpack_esm_ids__ = [315];
export const __webpack_esm_modules__ = {

/***/ 190
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {


// EXPORTS
__webpack_require__.d(__webpack_exports__, {
  "default": () => (/* reexport */ MCODEApp)
});
// ESM COMPAT FLAG
__webpack_require__.r(__webpack_exports__);

// EXTERNAL MODULE: consume shared module (default) react@!=1.8...3...1 (singleton)
var consume_shared_module_default_react_1_8_3_singleton_ = __webpack_require__(7309);
;// ./package.json
const package_namespaceObject = {"rE":"1.0.0"};
;// ./src/MCODEApp.tsx
/**
 * Update:
 *   1. `id`          → must match the Module Federation `name` in webpack.config.js
 *   2. `name`        → human-readable name shown in the host's App Settings
 *   3. `description` → one-line summary
 *   4. `resources`   → add/remove panels and menu items
 *   5. `mount()`     → register context menus, event listeners, etc.
 *   6. `unmount()`   → clean up event listeners from mount()
 *
 * Resources (panels and menu items) are registered declaratively — the host
 * renders them automatically. Context menus need `apis` access, so they are
 * registered in mount() instead.
 */


const { /* version */ "rE": version } = package_namespaceObject;
const MCODEApp = {
    id: 'mcode', // must match the Module Federation `name` in webpack.config.js
    name: 'MCODE Web',
    description: 'MCODE finds clusters (highly interconnected regions) in a network',
    version,
    apiVersion: '1.0',
    // ── Declarative resource registration ──────────────────────────────────
    // Panels and menu items are declared here. The host registers them
    // automatically — no mount() needed for these.
    resources: [
        {
            slot: 'right-panel',
            id: 'MCODEPanel',
            title: 'MCODE', // Tab title shown in the right panel.
            component: (0,consume_shared_module_default_react_1_8_3_singleton_.lazy)(() => Promise.all(/* import() */[__webpack_require__.e(978), __webpack_require__.e(762)]).then(__webpack_require__.bind(__webpack_require__, 9762))),
        },
    ],
    // ── Lifecycle hooks ────────────────────────────────────────────────────
    // mount() is called once after the app's resources are registered.
    // Use it for context menus (handlers need api access) and event listeners.
    mount(context) {
        // Context menu items are registered here because their handlers need
        // access to context.apis. The host auto-cleans all items when the app
        // is disabled — no explicit removal in unmount() needed.
        // registerSelectNeighbors(context)
        // TODO: Add more context menu registrations or event listeners here.
        // See src/contextMenus.ts for the pattern.
    },
    unmount() {
        // Only manual cleanup (e.g. event listeners) goes here.
        // Context menu items and resources are auto-cleaned by the host.
        //
        // if (_handler !== null) {
        //   window.removeEventListener('network:switched', _handler)
        //   _handler = null
        // }
    },
};

;// ./src/index.ts



/***/ }

};
