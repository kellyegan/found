# FilterDropdown → TitleBar Refactor Plan

Branch: `refactor/filter-dropdown-to-titlebar`

## Goal

`FilterDropdown` is logically owned by `TitleBar` — it's triggered by the filter icon in the title bar and anchored to its bottom edge. The only reason it lives in `MainRouter` is that `TitleBar` has no explicit z-value, so `FilterDropdown` couldn't be a child of it without being obscured by the side panels (z: 10).

This refactor fixes the root cause (give TitleBar an explicit z) then moves FilterDropdown inside TitleBar where it belongs. The intermediate `filterDropdownOpen` state in `readyContainer` disappears; the toggle becomes internal to TitleBar.

## Design decisions

- **TitleBar z: 15** — above side panels (10), below modal flows (25). Side panels and import overlay are anchored below TitleBar so there's no visual overlap concern; z only matters when elements share screen area.
- **FilterDropdown calls state singletons directly** — consistent with `ImportHandler`, `RelocationFlow`, `CollectionDeleteFlow`. TitleBar is a shell-level component (`shell/`), not a generic UI primitive.
- **`filterActive` stays as an external property** — TitleBar remains testable without state mocks; MainRouter continues to pass `FilterState.hasActiveFilters`.
- **`filterToggleRequested` signal is removed** — it only existed to notify MainRouter to toggle `filterDropdownOpen`. Once the toggle is internal, the signal has no caller.
- **FilterDropdown.qml is unchanged** — it remains a reusable component; only where it is instantiated changes.

---

## Commits

### Commit 1 — Give TitleBar an explicit z in MainRouter
**Status: ✅ Done** (`42602ed`)

Add `z: 15` to the `TitleBar` instantiation in `MainRouter.qml`. No logic changes.

This establishes TitleBar above the side panels in the stacking order and unblocks Commit 2.

Files to change:
- `found_app/qml/shell/MainRouter.qml` — add `z: 15` to TitleBar

Tests: run full suite; no new tests needed.

---

### Commit 2 — Move FilterDropdown into TitleBar
**Status: ✅ Done** (`40eb457`)

FilterDropdown becomes a child of TitleBar, anchored to the bottom-right of it. TitleBar manages the open/closed toggle internally. FilterDropdown calls state singletons directly for its data and signal handlers.

**TitleBar.qml changes:**
- Add `property bool _filterOpen: false`
- Filter icon `onClicked`: change from `root.filterToggleRequested()` → `root._filterOpen = !root._filterOpen`
- Remove `signal filterToggleRequested()`
- Add `FilterDropdown` child:
  ```qml
  FilterDropdown {
      objectName: "filterDropdown"
      anchors { top: parent.bottom; right: parent.right; rightMargin: Theme.spacingMd }
      width: 280
      open: root._filterOpen
      showMissingOnly: FilterState.showMissingOnly
      importJobActive: FilterState.importJobId !== ""
      activeCategories: { /* compute from FilterState + CategoriesState */ }
      activeTags:       { /* compute from FilterState + TagSearchState  */ }
      onClearAllRequested:          { FilterState.clearAllFilters(); root._filterOpen = false }
      onRemoveCategoryFilter: function(catId) { FilterState.setCategoryFilter(catId, "off") }
      onRemoveTagFilter:      function(tagId)  { FilterState.setTagFilter(tagId, "off") }
      onToggleMissingOnlyRequested: FilterState.setShowMissingOnly(!FilterState.showMissingOnly)
  }
  ```

**MainRouter.qml changes:**
- Remove `property bool filterDropdownOpen` from `readyContainer`
- Remove `TitleBar.onFilterToggleRequested` handler
- Remove the entire `// ── Layer 40: Dropdowns ──` section (FilterDropdown instantiation)

**Test changes:**
- Remove: `test_title_bar_has_filter_toggle_requested_signal` (signal removed)
- Add: `test_title_bar_has_filter_dropdown_child` — `findChild(QObject, "filterDropdown")` is not None
- Add: `test_title_bar_filter_dropdown_closed_by_default` — child's `open` property is False

Files to change:
- `found_app/qml/shell/TitleBar.qml`
- `found_app/qml/shell/MainRouter.qml`
- `found_app/tests/test_qml_shell.py`

---

## Progress summary

| # | Commit | Status |
|---|--------|--------|
| 1 | Give TitleBar `z: 15` in MainRouter | ✅ `42602ed` |
| 2 | Move FilterDropdown into TitleBar | ✅ `40eb457` |
