# Moveable Side Panels

## Goal

Replace the current fixed left/right panel layout with a system where:

- Any side panel can be dragged (via its EdgeTab) to either the left or right side
- Within a side, panel tabs can be reordered by dragging vertically
- The single drag gesture determines both target side (X position) and stack position (Y position) in one motion
- Multiple panels on the same side stack their EdgeTabs vertically; all tabs are always visible
- Opening a panel on a side automatically closes the other panel on that side
- Panel side assignments and stack order persist across sessions (via `AppSettings`)
- Different views expose different sets of panels (library: Collections + Metadata; collection/image: Metadata only)

## Current State

`SidePanel.qml` is a reusable base with an `edge` property (`"left"` | `"right"`), a `tabIndex` for vertical tab positioning, and an `open` flag. `CollectionsSidePanel` hardcodes `edge: "left"`; `MetadataSidePanel` hardcodes `edge: "right"`. `MainRouter` owns two boolean properties (`sidebarOpen`, `metadataSidebarOpen`) and saves/restores them per-view on navigation.

## New Architecture

### Key structural decisions

**EdgeTabs live in a dedicated window-level layer, not inside SidePanels.**

The original design embedded `EdgeTab` as a child of `SidePanel`. This created three compounding problems: EdgeTabs were obscured by open panel content unless z-ordering was carefully managed; the drag DragHandler lived in SidePanel-local coordinate space, requiring explicit `mapToItem` calls to place the ghost overlay at the window level; and the ghost/indicator had to be dynamically reparented to `Window.contentItem`.

By moving all EdgeTabs into a single `PanelTabStrip` item that lives in `MainRouter` at a high z-value, all three problems dissolve: tabs are always on top, drag coordinates are already in window scope, and the ghost overlay is a natural sibling within the same layer.

**`@Property` reactive properties instead of `Q_INVOKABLE` query functions for QML bindings.**

`Q_INVOKABLE` functions are not tracked by QML's binding engine — a binding like `edge: PanelLayout.panelEdge(panelId)` evaluates once and never re-evaluates when `layoutChanged` fires. Exposing `edges`, `order`, and `openPanels` as `@Property` with NOTIFY signals makes all QML bindings reactive without any `Connections` boilerplate.

---

### `PanelLayoutManager` (Python `QObject` service)

Owns three data structures:

1. **`_edges: dict[str, str]`** – which side each panel is on, e.g. `{"collections": "left", "metadata": "right"}`. Loaded from `AppSettings` at construction; written on every change.
2. **`_order: list[str]`** – global ordered list of all panel IDs, e.g. `["collections", "metadata"]`. Per-side stack position is derived by filtering this list to panels on the same side. Loaded from `AppSettings`; written on every change.
3. **`_open: dict[str, str]`** – which panel ID (if any) is open on each side, e.g. `{"left": "collections", "right": ""}`. Not persisted (panels start closed each session).

Exposed to QML as context property `PanelLayout`.

**Persistence pattern** — mirrors `ThemeManager` exactly:

- Constructor: `def __init__(self, parent=None, settings: AppSettings | None = None)`
- Read at startup via `self._settings.get(...)` with defaults
- Write on change via `self._settings.set(...)`
- `None` settings accepted silently (test mode)
- Key namespace: `panels/<panelId>/edge` and `panels/order`

**Reactive QML properties:**

```python
@Property("QVariantMap", notify=layoutChanged)
def edges(self):
    return dict(self._edges)

@Property("QVariantList", notify=layoutChanged)
def order(self):
    return list(self._order)

@Property("QVariantMap", notify=openStateChanged)
def openPanels(self):
    return dict(self._open)
```

These replace the `panelEdge`, `tabIndex`, and `openPanelOnSide` Q_INVOKABLE query methods. `tabIndex` is computed in QML (see `SidePanelBody` below).

**Q_INVOKABLE methods (mutations only):**

- `setLayout(panelId: str, edge: str, sideIndex: int)` – atomic update: moves panel to `edge` at `sideIndex` within that side's stack. If the panel was open and is moving sides, it stays open and any panel currently open on the new side is closed. Persists edge and order. Emits `layoutChanged`; also emits `openStateChanged` if open state changed.
- `setPanelEdge(panelId: str, edge: str)` – moves panel to edge, appending to end of that side's stack. Used for programmatic resets and initial default overrides (not called from drag UI).
- `togglePanel(panelId: str)` – opens panel (closing any other on same side) or closes it if already open. Emits `openStateChanged`.
- `saveViewState(view: str)` – snapshots `_open` for that view.
- `restoreViewState(view: str, availablePanels: list[str])` – applies saved state, restricted to panels available in the entering view.

**Signals:**

- `layoutChanged()` — edge or order changed
- `openStateChanged()` — which panel is open on a side changed

Both signals may fire together from `setLayout` when a move affects open state.

**`setLayout` algorithm:**

```python
def setLayout(self, panelId, edge, sideIndex):
    old_edge = self._edges[panelId]
    was_open = self._open.get(old_edge) == panelId
    open_state_changed = False

    if old_edge != edge:
        if was_open:
            self._open[old_edge] = ""
            self._open[edge] = panelId
            open_state_changed = True
        # else: closed panel moving sides — new side's open state unchanged

    self._edges[panelId] = edge

    # Rebuild order: remove panelId, insert so it becomes
    # the sideIndex-th panel on `edge`.
    order = [p for p in self._order if p != panelId]
    peers = [p for p in order if self._edges[p] == edge]

    if sideIndex >= len(peers):
        ref = peers[-1] if peers else None
        insert_at = order.index(ref) + 1 if ref else len(order)
    else:
        insert_at = order.index(peers[sideIndex])

    order.insert(insert_at, panelId)
    self._order = order

    if self._settings:
        self._settings.set(f"panels/{panelId}/edge", edge)
        self._settings.set("panels/order", ",".join(self._order))

    self.layoutChanged.emit()
    if open_state_changed:
        self.openStateChanged.emit()
```

Defaults (if no persisted values): order = `["collections", "metadata"]`, collections → left, metadata → right.

---

### `PanelTabStrip.qml` — window-level tab container (new)

Lives directly in `MainRouter` with a high `z` value so it always renders above all panel bodies. Contains all EdgeTabs for the current view. Owns the drag ghost and insertion indicator during drag.

Two implicit columns — left strip and right strip — each anchored to their respective edge and centred vertically. Each column's contents are driven by `PanelLayout.order` filtered to that edge and to `availablePanels`:

```qml
Item {
    id: root
    anchors.fill: parent
    z: 100

    property var availablePanels: []

    // Left strip
    Column {
        anchors { left: parent.left; verticalCenter: parent.verticalCenter }
        spacing: 4
        Repeater {
            model: PanelLayout.order.filter(
                       p => PanelLayout.edges[p] === "left"
                         && root.availablePanels.includes(p))
            EdgeTab {
                panelId: modelData
                onLayoutRequested: (edge, idx) =>
                    PanelLayout.setLayout(panelId, edge, idx)
                onToggleRequested: PanelLayout.togglePanel(panelId)
            }
        }
    }

    // Right strip
    Column {
        anchors { right: parent.right; verticalCenter: parent.verticalCenter }
        spacing: 4
        Repeater {
            model: PanelLayout.order.filter(
                       p => PanelLayout.edges[p] === "right"
                         && root.availablePanels.includes(p))
            EdgeTab {
                panelId: modelData
                onLayoutRequested: (edge, idx) =>
                    PanelLayout.setLayout(panelId, edge, idx)
                onToggleRequested: PanelLayout.togglePanel(panelId)
            }
        }
    }

    // Ghost tab and insertion indicator are created here as children
    // during drag (see EdgeTab drag implementation)
}
```

Because `PanelLayout.order` and `PanelLayout.edges` are reactive `@Property`, the Repeater models update automatically when `layoutChanged` fires.

---

### `EdgeTab.qml` — drag gesture

**API:**

- `property string panelId`
- `signal layoutRequested(string targetEdge, int targetSideIndex)` — fired on drag release
- `signal toggleRequested()` — fired on tap (no drag)
- `property bool dragActive: false`

**Drag implementation:**

A `DragHandler` (both axes) captures the gesture. Because `EdgeTab` lives inside `PanelTabStrip`, which fills the window, all coordinates are already in window space — no `mapToItem` needed.

While dragging, two visual items are created as children of `PanelTabStrip` (the grandparent):

**Ghost tab** — semi-transparent copy of the EdgeTab that snaps to the resolved target:

- X: locked to left or right edge based on `dragHandler.centroid.position.x < window.width / 2 ? "left" : "right"`. The ghost never floats in the middle.
- Y: snaps to the nearest insertion slot in the target side's stack (midpoint between adjacent tabs, or above first / below last). Snaps with a short `NumberAnimation`.
- Same size and corner radii as a real EdgeTab; ~0.5 opacity; accent colour.

**Insertion indicator** — a short accent-coloured horizontal bar (~3 px tall, same width as an EdgeTab) placed between the tabs that will become the ghost's neighbours. Animates to a new slot in real time as the cursor crosses midpoint thresholds.

**On release:** compute `targetEdge` and `targetSideIndex` from the snapped ghost position → emit `layoutRequested(targetEdge, targetSideIndex)`. Destroy ghost and indicator. The Repeater re-orders the real tabs via the updated `PanelLayout.order` binding.

**On cancel** (`DragHandler.onCanceled`): destroy ghost and indicator without emitting `layoutRequested`. Reset `dragActive` to false. No state change.

**Snap threshold:** `targetEdge = dragHandler.centroid.position.x < window.width / 2 ? "left" : "right"` — uses the pointer position, not the tab's own position.

---

### `SidePanelBody.qml` (renamed from `SidePanel.qml`)

The drawer frame only — no EdgeTab, no drag signals. Binds entirely to the reactive `PanelLayout` properties:

```qml
property string panelId: ""

readonly property string edge: PanelLayout.edges[panelId] ?? "left"
readonly property bool isOpen: PanelLayout.openPanels[edge] === panelId

// tabIndex: position of this panel within its side's stack
readonly property int tabIndex: {
    var peers = PanelLayout.order.filter(
        p => PanelLayout.edges[p] === edge)
    return peers.indexOf(panelId)
}
```

All three bindings re-evaluate automatically when `layoutChanged` or `openStateChanged` fires — no `Connections` boilerplate needed.

**Edge-change transition:** when `edge` changes, animate the panel sliding to its new side rather than jumping. Use a `Behavior` on the relevant anchor or an `x` transition so the drawer glides left or right.

---

### `CollectionsSidePanel.qml` / `MetadataSidePanel.qml`

Compose `SidePanelBody` with panel-specific content. Remove all hardcoded `edge` values; set only `panelId`:

```qml
SidePanelBody {
    panelId: "collections"
    // panel-specific content
}
```

No panel-management logic remains in either component.

---

### `MainRouter.qml` — wiring

`PanelTabStrip` is declared once with high `z`, receiving the current view's `availablePanels`:

```qml
PanelTabStrip {
    availablePanels: currentView === "library"
                     ? ["collections", "metadata"]
                     : ["metadata"]
    z: 100
}
```

Replace `sidebarOpen`/`metadataSidebarOpen` with:

```qml
readonly property bool leftPanelOpen:  PanelLayout.openPanels["left"]  !== ""
readonly property bool rightPanelOpen: PanelLayout.openPanels["right"] !== ""
```

Navigation handler calls `PanelLayout.saveViewState` / `restoreViewState` as before.

No panel toggle or layout signals bubble through `SidePanelBody` — all interaction flows through `PanelTabStrip` → `PanelLayout`.

---

## Commit Sequence

### Commit 1 — `PanelLayoutManager` service with persistence

**Files:**

- [x] `found_app/services/panel_layout.py` (new)
- [x] `found_app/tests/test_panel_layout.py` (new)

**Tests:**

- [x] Default edge assignments and order when `settings=None`
- [x] `edges`, `order`, `openPanels` properties return correct values
- [x] `tabIndex` is derivable from `order` filtered by edge
- [x] `setLayout` moves panel to new edge at correct side-index
- [x] `setLayout` with sideIndex past end of peers appends to that side
- [x] `setLayout` on an open panel moving sides: panel stays open on new side, displaces any panel that was open there; emits both `layoutChanged` and `openStateChanged`
- [x] `setLayout` on a closed panel moving sides: new side's open state unchanged; emits only `layoutChanged`
- [x] `setLayout` reorder within same side: open state unchanged; emits only `layoutChanged`
- [x] `togglePanel` opens panel; opening second on same side closes first; toggling open panel closes it; emits `openStateChanged`
- [x] `saveViewState` / `restoreViewState` round-trip with available-panel filtering
- [x] Edge assignments and order persist through a reconstruct with the same `AppSettings` (uses `tmp_path` + `IniFormat`)

- [x] All tests pass (`python -m pytest found_app/tests/test_panel_layout.py -v`)
- [x] Commit

---

### Commit 2 — Wire `PanelLayoutManager` into `AppContainer`

**Files:**

- [ ] `found_app/core/app_container.py`
- [ ] `found_app/tests/test_bootstrap.py`

**Changes:** `AppContainer.__init__` instantiates `PanelLayoutManager(settings=self._settings)`. `wire_engine` exposes it as `PanelLayout` context property.

**Tests:**

- [ ] `PanelLayout` is accessible as a context property in the QML engine

- [ ] All tests pass (`python -m pytest found_app/tests/ -v`)
- [ ] Commit

---

### Commit 3 — `SidePanelBody` and subcomponents

**Files:**

- [ ] `found_app/qml/components/SidePanelBody.qml` (renamed from `SidePanel.qml`)
- [ ] `found_app/qml/components/CollectionsSidePanel.qml`
- [ ] `found_app/qml/components/MetadataSidePanel.qml`
- [ ] `found_app/tests/test_qml_panels.py`

**Changes:**

- [ ] Rename `SidePanel.qml` → `SidePanelBody.qml`; remove EdgeTab child and all drag/signal wiring; add reactive `edge`, `isOpen`, `tabIndex` bindings
- [ ] Add edge-change slide animation
- [ ] `CollectionsSidePanel` sets `panelId: "collections"`, removes `edge: "left"`
- [ ] `MetadataSidePanel` sets `panelId: "metadata"`, removes `edge: "right"`

**Tests:**

- [ ] `SidePanelBody` exposes `panelId`, `edge`, `isOpen`, `tabIndex`
- [ ] `edge` and `isOpen` update when `PanelLayout` signals fire

- [ ] All tests pass (`python -m pytest found_app/tests/ -v`)

**UX verification** (run `/run` and check each manually):

- [ ] App launches with Collections tab on left, Metadata tab on right
- [ ] Clicking the Collections EdgeTab opens the Collections panel
- [ ] Clicking the Metadata EdgeTab opens the Metadata panel
- [ ] Clicking an open panel's EdgeTab closes it
- [ ] Opening one panel does not open or close the other
- [ ] Both panels render correctly with no layout regressions vs. current main

- [ ] Commit

---

### Commit 4 — `PanelTabStrip` and `EdgeTab` drag gesture

**Files:**

- [ ] `found_app/qml/components/PanelTabStrip.qml` (new)
- [ ] `found_app/qml/components/EdgeTab.qml`
- [ ] `found_app/tests/test_qml_panels.py`

**Changes to `EdgeTab`:**

- [ ] Add `property string panelId`, `signal layoutRequested(string targetEdge, int targetSideIndex)`, `signal toggleRequested()`, `property bool dragActive`
- [ ] `DragHandler` + ghost tab + insertion indicator
- [ ] `onCanceled` handler cleans up without emitting `layoutRequested`

**New `PanelTabStrip`:**

- [ ] Left and right `Column` with `Repeater` driven by reactive `PanelLayout` properties
- [ ] Wires `EdgeTab.layoutRequested` → `PanelLayout.setLayout`
- [ ] Wires `EdgeTab.toggleRequested` → `PanelLayout.togglePanel`

**Tests:**

- [ ] `EdgeTab` exposes `panelId`, `dragActive`; signals `layoutRequested` and `toggleRequested` exist
- [ ] `dragActive` is writable
- [ ] `PanelTabStrip` renders correct tab count for a given `availablePanels` list

- [ ] All tests pass (`python -m pytest found_app/tests/ -v`)

**UX verification** (run `/run` and check each manually):

_Tab visibility:_

- [ ] EdgeTabs are visible above all content when a panel is open
- [ ] EdgeTabs are never clipped or hidden by the open panel body
- [ ] EdgeTabs remain reachable by the pointer when a panel is open

_Drag basics:_

- [ ] Starting a drag on an EdgeTab shows the ghost tab and insertion indicator
- [ ] Ghost appears on the left edge when the cursor is in the left half of the window
- [ ] Ghost appears on the right edge when the cursor is in the right half of the window
- [ ] Ghost snaps vertically to the nearest insertion slot; slot updates in real time as cursor moves
- [ ] Insertion indicator appears between the correct pair of tabs throughout the drag

_Drag outcomes:_

- [ ] Releasing in the same position as the original tab leaves everything unchanged
- [ ] Dragging Collections tab to the right side moves the tab and panel to the right
- [ ] Panel body slides to new side with an animation; it does not teleport
- [ ] Dragging an open panel to the opposite side: panel stays open on the new side
- [ ] If a panel is open on the target side when a drag lands there, that panel closes

_Drag cancel:_

- [ ] Pressing Escape mid-drag returns the ghost to its origin and leaves state unchanged
- [ ] Ghost tab and insertion indicator are removed cleanly after any drag (release or cancel)

- [ ] Commit

---

### Commit 5 — `MainRouter` full wiring and per-view state

**Files:**

- [ ] `found_app/qml/shell/MainRouter.qml`
- [ ] `found_app/tests/test_view_state_persistence.py`

**Changes:**

- [ ] Remove `sidebarOpen`, `metadataSidebarOpen`
- [ ] Add `PanelTabStrip` with view-driven `availablePanels`
- [ ] Add `leftPanelOpen` / `rightPanelOpen` from `PanelLayout.openPanels`
- [ ] Navigation handler calls `PanelLayout.saveViewState` / `restoreViewState`

**Tests:**

- [ ] Panel open state is saved and restored correctly on view navigation
- [ ] `restoreViewState` ignores panels not in `availablePanels`
- [ ] Mutual exclusion: opening one panel closes any other on the same side
- [ ] Cross-view isolation: panel state in library view is independent of image view
- [ ] Reorder persists: panel order saved to `AppSettings` survives app restart

- [ ] All tests pass (`python -m pytest found_app/tests/ -v`)

**UX verification** (run `/run` and check each manually):

_View-correct tabs:_

- [ ] Library view shows both Collections and Metadata EdgeTabs
- [ ] Collection/Image view shows only the Metadata EdgeTab
- [ ] Navigating from library to image view: Collections tab disappears cleanly
- [ ] Navigating back to library: Collections tab reappears in its correct position

_State persistence across navigation:_

- [ ] Open a panel in library view, navigate to image view, return — panel is open again
- [ ] Close a panel in library view, navigate away and back — panel stays closed
- [ ] Panel open state in library view is unaffected by panel interaction in image view

_Persistence across sessions:_

- [ ] Drag a panel to the opposite side, quit the app, relaunch — panel is on the new side
- [ ] Reorder tabs, quit, relaunch — order is preserved

- [ ] Commit

---

## Open Questions / Future Work

- **Drag ghost in offscreen tests:** test `layoutRequested` signal emission directly rather than the visual ghost, since `PanelTabStrip` requires a real window for coordinate geometry.
- **More panels:** add to `PanelLayoutManager._DEFAULTS` (edge + position in default order); add panel ID to `availablePanels` in the relevant views.
- **Persisted open state:** panels start closed every session. `saveViewState`/`restoreViewState` could write to `AppSettings` if always-restore-open is desired.
- **Single-panel views:** dragging the only panel to the same side/index is a no-op (algorithm is idempotent). No special handling needed.
