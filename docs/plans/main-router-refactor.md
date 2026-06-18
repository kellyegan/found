# MainRouter Refactor Plan

Branch: `refactor/main-router-organization`

## Goal

`MainRouter.qml` mixes structural layout, visual layering, application flows, and logic. This refactor breaks it into focused components and reorganises what remains so the z-order, layout anchors, and wiring are immediately readable.

Each commit produces clean, functional, passing code. No red tests on any commit.

---

## Commits

### Commit 1 — Extract `RelocationFlow.qml`
**Status: ✅ Done** (`39eb460`)

Moved the locate dialog, prefix bulk-relocate, and result summary out of `MainRouter` into a self-contained `shell/RelocationFlow.qml`. `MainRouter` instantiates it with `anchors.fill: parent; z: 25`.

---

### Commit 2 — Extract `ImportHandler.qml`
**Status: ✅ Done** (uncommitted)

Moved the drag drop area, deferred scan timer, and import panel overlay into `shell/ImportHandler.qml`. `MainRouter` instantiates it anchored below `TitleBar` and above `CategoriesBar` with `z: 20`.

Files changed:
- `found_app/qml/shell/ImportHandler.qml` (new)
- `found_app/qml/shell/MainRouter.qml` (inline block replaced with `ImportHandler {}`)
- `found_app/tests/test_qml_shell.py` (4 new tests)

---

### Commit 3 — Self-managing `SplashScreen`
**Status: ✅ Done** (`1f0ea81`)

Move `splashDismissed` out of `MainRouter` and into `SplashScreen.qml` as a `property bool dismissed: false`. The existing `dismissed()` signal handler sets it internally. `MainRouter.readyContainer` then reads `splashScreen.dismissed` instead of a local property.

Files to change:
- `found_app/qml/views/SplashScreen.qml` — add `property bool dismissed`, handle own signal
- `found_app/qml/shell/MainRouter.qml` — remove `splashDismissed`, reference `splashScreen.dismissed`
- `found_app/tests/test_qml_shell.py` — test that `dismissed` defaults to false; test that it becomes true after signal

---

### Commit 4 — Extract `CollectionDeleteFlow.qml`
**Status: ✅ Done** (`6151999`)

Move the `_removeCollectionId`/`_removeCollectionName` state and the `ConfirmDialog` for collection deletion into `shell/CollectionDeleteFlow.qml`. Expose a `requestDelete(collectionId, collectionName)` method so `CollectionsSidePanel`'s `onRemoveCollectionRequested` can call it.

Files to change:
- `found_app/qml/shell/CollectionDeleteFlow.qml` (new)
- `found_app/qml/shell/MainRouter.qml` — remove inline state and dialog, add `CollectionDeleteFlow {}`
- `found_app/tests/test_qml_shell.py` — test exists/loads, `open` defaults to false, confirm/cancel signals

---

### Commit 5 — Add `reservedHeight` to `CategoriesBar`
**Status: ✅ Done** (`b87068d`)

Three views (`LibraryView`, `CollectionView`, `ImportHandler`) reach into `CategoriesBar`'s private `_tabHeight + _stripHeight`. Replace with a single public `readonly property real reservedHeight` on `CategoriesBar`. Update all callers.

Files to change:
- `found_app/qml/components/CategoriesBar.qml` — add `readonly property real reservedHeight: _tabHeight + _stripHeight`
- `found_app/qml/shell/MainRouter.qml` — replace three `_tabHeight + _stripHeight` references with `categoriesBar.reservedHeight`
- `found_app/tests/test_qml_shell.py` — test that `reservedHeight` equals the sum

---

### Commit 6 — Reorganise `readyContainer` by z-layer
**Status: ✅ Done** (`b41769e`)

Reorder all children of `readyContainer` bottom-to-top by z-value, and group `Connections` blocks after all visual elements. Add region comments. No logic changes — structure only.

Intended declaration order inside `readyContainer`:

```
// ── Properties ─────────────────────────────────────────────
// (panel state, _lastView, _viewPanelState)

// ── Layer -1: Background ────────────────────────────────────
MouseArea (z: -1)

// ── Layer 0: Content views ──────────────────────────────────
LibraryView, CollectionView, ImageView, SettingsView

// ── Layer 0: Chrome ─────────────────────────────────────────
TitleBar

// ── Layer 5: Structural bars ─────────────────────────────────
CategoriesBar

// ── Layer 10: Side panels ───────────────────────────────────
CollectionsSidePanel, MetadataSidePanel

// ── Layer 20: Import overlay ─────────────────────────────────
ImportHandler

// ── Layer 25: Modal flows ────────────────────────────────────
RelocationFlow, CollectionDeleteFlow

// ── Layer 40: Dropdowns ──────────────────────────────────────
FilterDropdown

// ── Connections ──────────────────────────────────────────────
NavigationManager, AppState, SelectionManager
```

Files to change:
- `found_app/qml/shell/MainRouter.qml` — reorder only, no logic changes
- Tests: run full suite to confirm no regressions (no new tests needed)

---

## Progress summary

| # | Commit | Status |
|---|--------|--------|
| 1 | Extract `RelocationFlow.qml` | ✅ Committed `39eb460` |
| 2 | Extract `ImportHandler.qml` | ✅ Done — needs commit |
| 3 | Self-managing `SplashScreen` | ✅ `1f0ea81` |
| 4 | Extract `CollectionDeleteFlow.qml` | ✅ `6151999` |
| 5 | `CategoriesBar.reservedHeight` | ✅ `b87068d` |
| 6 | Reorganise `readyContainer` by z-layer | ✅ `b41769e` |
