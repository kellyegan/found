# FOUND — Phase 2 UI Layout

This document defines the spatial layout of each view in the Found application: which zones exist, what elements populate each zone, and how zones behave under different states.

This is a design reference document. Functional behavior, interaction models, and component definitions are specified in the Phase 2 Specification and Component Inventory.

---

# 1. Library View

## Zone Map

```
+----------------------------------------------------------+
|  Title                  |  Status  |       Search        |
+----------------------------------------------------------+
|                                                          |
| [◀]                   Thumbnail Grid                [▶] |
|                                                          |
|                                                          |
|                                                          |
+----------------------------------------------------------+
|                      Categories                          |
+----------------------------------------------------------+
```

The Collections overlay extends from the left edge and the Metadata overlay from the right edge. Both sit above the thumbnail grid without compressing it.

---

## Title Bar

Full-width bar spanning the top of the window. Divided into three zones:

**Title zone (left)**

- Current page title
- Back navigation
- Active collection name (when browsing a collection)

**Status zone (center)**

- Status indicators — only visible when there is something to report:
  - Import progress
  - Missing image count / indicator
  - Backend connection state

**Search zone (right)**

Contains two elements: the keyword search field and the filter dropdown icon.

- Keyword search field — tag autocomplete; dropdown appears below the title bar and may temporarily overlap the thumbnail grid or metadata overlay
- Filter dropdown icon — grey when no filters are active, blue when filters are active; clicking opens the filter dropdown

**Filter dropdown**

Opens below the title bar. Groups active filters by type, with a separator between each group:

```
[ Keywords ]
  chip: landscape ×
  chip: architecture ×
─────────────────────
[ Categories ]
  chip: Photography (include) ×
  chip: Illustration (exclude) ×
─────────────────────
[ Missing Images ]
  toggle: show only missing
─────────────────────
  Clear all filters
```

- Keyword chips appear here when selected from the search field autocomplete
- Multiple keyword chips may be active simultaneously
- Clear all filters removes keywords, category filters, and missing image toggle — does not affect the active collection
- The active collection is excluded from the filter indicator state

---

## Collections Overlay

Left-edge collapsible overlay. Slides over the thumbnail grid without compressing it.

**Toggle tab** — positioned on the left edge of the grid at mid-height:

- Triangle points toward the left edge when the panel is open
- Triangle points toward center when collapsed

**Contents**

- Collection list (alphabetical ordering; empty collections appear visually muted)
- Drag-drop targets for adding images to collections
- New collection inline field

The sidebar is hidden while browsing a collection (per existing spec).

---

## Metadata Overlay

Right-edge collapsible overlay. Slides over the thumbnail grid without compressing it.

**Toggle tab** — positioned on the right edge of the grid at mid-height:

- Triangle points toward the right edge when the panel is open
- Triangle points toward center when collapsed

The panel may remain open regardless of selection state, and is used for viewing and editing metadata for selected images.

**Contents**

Read-only fields:

- Filename
- Path
- Dimensions
- File size
- Date added
- Missing state

Editable fields:

- Tags (TagEditor widget)
- Categories
- Collections

Bulk editing behavior follows the existing spec.

---

## Thumbnail Grid

Occupies the full window width between the title bar and categories bar. Overlays sit above it without affecting its dimensions.

**Scrolling** — horizontal, left to right (mouse wheel and click-drag)

**Layout**

- Row count derived from window height: `rowCount = max(2, round(viewportHeight / 180))`
- `actualThumbnailSize = viewportHeight / rowCount`
- Equal gap (default 50px) between all four sides of each thumbnail tile; gap will be user-adjustable in a future phase
- Top and bottom margin between the grid and the title bar / categories bar
- Left and right margin sized so that edge columns remain visible and scrollable when either overlay is open

**Loading** — virtualized rendering, lazy thumbnail loading, incremental data prefetch per existing spec

---

## Categories Bar

Bottom collapsible bar spanning the full window width.

**Toggle tab** — centered on the bottom edge:

- Triangle points downward (toward edge) when the bar is open
- Triangle points upward (toward center) when collapsed

**Contents**

- Horizontally scrolling list of all categories
- All categories are always shown (category count is expected to remain limited)
- Each category supports tri-state filtering: off / include / exclude

---

# 2. Image View

## Zone Map

```
+----------------------------------------------------------+
|  Title                  |  Status  |       Search        |
+----------------------------------------------------------+
|                                                          |
|  [◀]           Image Viewport                      [▶]  |
|                                                    [meta]|
|                                                          |
|                                                          |
+----------------------------------------------------------+
```

The Metadata overlay sits on the right edge, collapsed by default. No Collections overlay or Categories bar are present in this view.

---

## Title Bar

Same three-zone structure as Library View:

**Title zone (left)**

- Current image title / filename
- Back navigation

**Status zone (center)**

- Same status indicators as Library View — only visible when there is something to report

**Search zone (right)**

- Displays active keyword and category filter chips — read-only in Image View
- Filter dropdown is visible but non-interactive
- Reflects the browsing context the user navigated from

---

## Image Viewport

Occupies the full window area below the title bar, with margin on all sides.

- Image is centered within the viewport
- Aspect ratio is preserved
- Zoom via mouse wheel
- Pan via click-and-drag

**Navigation controls** — hover only, overlaid on the left and right edges of the viewport:

- Left edge: previous image
- Right edge: next image

Navigation remains constrained to the current browsing context (active filters, active collection, or active selection set) per existing spec.

---

## Metadata Overlay

Right-edge collapsible overlay, same structure and toggle behavior as Library View. Collapsed by default when entering Image View.

**Toggle tab** — right edge at mid-height:

- Triangle points toward right edge when open
- Triangle points toward center when collapsed

**Contents** — identical to Library View metadata overlay:

Read-only fields: filename, path, dimensions, file size, date added, missing state

Editable fields: tags, categories, collections

---

## Fullscreen Mode

Triggered by 'f' (per existing spec).

Hides:

- Title bar (all three zones)
- Metadata overlay toggle tab

The image viewport expands to fill the entire window. Navigation controls remain accessible on hover.

---

# 3. Collection View

## Zone Map

```
+----------------------------------------------------------+
|  Collection Name        |  Status  |       Search        |
+----------------------------------------------------------+
|                                                          |
|                     Thumbnail Grid                  [▶] |
|                                                          |
|                                                          |
|                                                          |
+----------------------------------------------------------+
|                      Categories                          |
+----------------------------------------------------------+
```

No Collections overlay or left-edge toggle tab. The Metadata overlay sits on the right edge.

---

Collection View shares the same layout as Library View with two exceptions:

**Title zone (left)**

- Displays the collection name in place of the page title
- Back navigation returns to Library View

**Collections overlay**

- Not present — no left-edge toggle tab
- The thumbnail grid extends to the full left margin

All other zones — Metadata overlay, Categories bar, Thumbnail Grid, and Title Bar Status and Search zones — are identical to Library View.

---

# 4. Splash Screen

## Zone Map

```
+----------------------------------------------------------+
|                                                          |
|                                                          |
|               +---------------------------+              |
|               |          FOUND            |              |
|               +---------------------------+              |
|                                                          |
|                                                          |
| Version            Status message              License   |
+----------------------------------------------------------+
```

---

## Title

- Centered horizontally and vertically within the window
- Width approximately 80% of the window width
- Future enhancement: background image displayed behind the title block, optionally sourced from the library

---

## Bottom Elements

Positioned at the bottom of the window with approximately 25px margin from the bottom edge. All three elements align to the edges of the title block:

**Version (left)**

- Left edge aligns with the left edge of the title block
- Sourced from `pyproject.toml` via `importlib.metadata`

**Status message (center)**

- Centered horizontally
- Displays backend startup progress, retry status, and errors
- Behavior identical to existing spec: 2 automatic retry attempts spaced 10 seconds apart; error state displayed after retries are exhausted

**License (right)**

- Right edge aligns with the right edge of the title block
- Sourced from `pyproject.toml` via `importlib.metadata`

---

# 5. Import Modal

## Zone Map

```
+----------------------------------------------------------+
|  [dimmed background — current view remains visible]      |
|    +------------------------------------------+          |
|    |  X images already in library, skipping.  |          |
|    |  [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]          |          |
|    |                                           |          |
|    |  X images ready to import                 |          |
|    |  [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]          |          |
|    |                                           |          |
|    |  These images are duplicates              |          |
|    |  [img]  Keep "/path/in/library"           |          |
|    |         Replace with "/path/incoming"     |          |
|    |  [img]  Keep "/path/in/library"           |          |
|    |         Replace with "/path/incoming"     |          |
|    |                                           |          |
|    |              [ CANCEL ]  [ IMPORT ]       |          |
|    +------------------------------------------+          |
+----------------------------------------------------------+
```

---

## Overlay

The modal is centered in the window. A dimmed overlay covers the background — the current view (Library or other) remains visible but darkened behind it.

---

## Modal Content

The modal scrolls internally when content exceeds its height. Sections are hidden entirely when they contain no items.

**Already in library** _(hidden if none)_

- Heading: "X images already in library, skipping."
- Row of up to 10 thumbnails of the existing library images
- These images are skipped automatically — no user action required

**Ready to import** _(hidden if none)_

- Heading: "X images ready to import"
- Row of up to 10 thumbnails

**Duplicates** _(hidden if no conflicts)_

- Heading: "These images are duplicates"
- List of conflict cards, one per duplicate. Each card contains:
  - Thumbnail of the existing library image
  - "Keep `/path/to/image/in/library`" — selected by default
  - "Replace with `/path/to/image/not/in/library`"

---

## Actions

Right-aligned at the bottom of the modal:

- **Cancel** — dismisses the modal, no import occurs
- **Import** — confirms the import with resolved duplicate selections
