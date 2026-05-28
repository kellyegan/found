# FOUND — Phase 2 Component Inventory

[[IMGORG]]

This inventory is organized by:

- application-level and system components
- reusable UI components
- view-specific components

The goal is to:

- avoid duplicated QML components
- encourage composable UI architecture
- identify shared interaction patterns early
- separate logic components from visual components

This inventory intentionally focuses on **conceptual components**, not implementation details.

---

# 1. Application-Level & System Components

These components exist at the top level of the application and manage major application state or coordinate system-wide behavior.

---

## AppWindow

### Purpose

Root application window.

### Responsibilities

- Initialize application shell
- Manage top-level layouts
- Manage global overlays and modals
- Handle application-wide keyboard shortcuts

### Contains

- SplashScreen
- MainRouter
- ModalLayer
- GlobalNotificationOverlay

---

## ModalLayer

### Purpose

Z-stacked layer that renders modals above all other application content.

### Used For

- ImportConfirmModal
- Future dialogs

---

## GlobalNotificationOverlay

### Purpose

Z-stacked layer that renders notification toasts above all other application content, including modals.

### Used For

- NotificationToast instances (import complete, errors, warnings)

---

## MainRouter

### Purpose

Controls active application view/state.

### Responsibilities

- Route between major views
- Maintain navigation history
- Restore previous state

### Routes

- Splash
- LibraryView
- ImageView
- ImportConfirmModal
- Future views

---

## NavigationManager

### Purpose

Browser-style navigation history management.

### Responsibilities

- Push navigation state
- Pop navigation state
- Restore filters
- Restore selections
- Restore scroll positions

---

## ThemeManager

### Purpose

Centralized theme/style definitions.

### Responsibilities

- Color palette
- Typography
- Spacing constants
- Animation timing

---

## ApiClient

### Purpose

Frontend communication layer.

### Responsibilities

- API requests
- Async request handling
- Retry handling
- Error normalization
- Import job tracking

---

## SelectionManager

### Purpose

Centralized image selection state.

### Responsibilities

- Single selection
- Multi-selection
- Range selection (shift-click anchor)

---

## DragDropManager

### Purpose

Centralized drag/drop coordination.

### Responsibilities

- Drag sources
- Drop targets
- Hover feedback

---

## FilterStateManager

### Purpose

Centralized filter state.

### Responsibilities

- Active tag filters (include/exclude list)
- Active category filters (include/exclude list)
- Missing-image filter toggle

---

## ThumbnailLoader

### Purpose

Thumbnail request management.

### Responsibilities

- Async thumbnail loading
- Retries on failure
- Prioritization: visible tiles before buffer tiles

---

## ImageLoader

### Purpose

Full-resolution image loading.

### Responsibilities

- Async loading
- Cancellation when navigating away
- Failure handling

---

## ImportJobManager

### Purpose

Tracks import jobs.

### Responsibilities

- Progress tracking
- Completion events
- Polling the backend job endpoint

---

# 2. Shared Layout Components

Reusable structural UI components.

---

## TitleBar

### Purpose

Top navigation/title region.

### Used In

- LibraryView
- ImageView

### Contains

- page title
- back navigation
- optional actions

---

## SidebarOverlay

### Purpose

Collapsible overlay sidebar.

### Used In

- LibraryView

### Responsibilities

- open/close animation
- overlay interaction
- collection browsing

---

## BottomInfoPanel

### Purpose

Metadata display/edit region.

### Used In

- LibraryView
- ImageView

### Contains

- metadata fields
- tag editor
- category editor
- collection editor

---

## OverlayContainer

### Purpose

Reusable dimmed overlay background layer.

### Used For

- sidebars
- future dialogs

---

## TagSuggestionList

### Purpose

Displays matching tag suggestions as the user types.

### Used In

- TagSearchField (filtering)
- TagEditor (metadata editing)

### Behavior

Appears while typing; dismissed on selection or blur.

---

# 3. Thumbnail Browsing Components

Core image-browsing system.

---

## ThumbnailGrid

### Purpose

Main image browsing surface.

### Responsibilities

- Virtualized rendering
- Lazy loading
- Horizontal scrolling
- Selection rendering

### Implementation Note

Uses QML's `ListView` in horizontal orientation. Row layout is achieved by composing multiple `ListView` instances or a `GridView` configured for horizontal flow.

### Contains

- ThumbnailTile instances

---

## ThumbnailTile

### Purpose

Individual image tile.

### Responsibilities

- Render thumbnail
- Display selection state
- Display missing state
- Display loading state

### States

- normal
- selected
- loading
- missing
- failed thumbnail

---

## ThumbnailImage

### Purpose

Actual thumbnail rendering element.

### Responsibilities

- Preserve aspect ratio
- Apply letterboxing
- Async image loading

---

## ThumbnailPlaceholder

### Purpose

Fallback placeholder.

### Used For

- loading state
- missing thumbnails
- failed generation

---

## SelectionOverlay

### Purpose

Visual selection indicator rendered over a ThumbnailTile.

### Used In

- ThumbnailTile

### States

- selected
- multiselect
- active/focused

---

# 4. Filtering Components

Filtering and discovery system.

---

## FilterBar

### Purpose

Top-level filtering controls.

### Contains

- CategoryFilterDropdown
- TagSearchField
- MissingImageToggle

---

## CategoryFilterDropdown

### Purpose

Category filter selector.

### Features

- Tri-state filtering per category
- Multiple active categories supported

### States

- Off
- On (include)
- Exclude

---

## TagSearchField

### Purpose

Tag lookup and filter entry field.

### Responsibilities

- Text input
- Delegates to TagSuggestionList for autocomplete
- Displays active filter chips

---

## FilterChip

### Purpose

Represents a single active filter item.

### Used For

- Active tag filters
- Active category filters
- Bulk-edit metadata items (shared, partial)

### States

- include
- exclude
- mixed (item present on some but not all selected images; used in bulk editing)

---

## MissingImageToggle

### Purpose

Toggle to show only missing images.

---

# 5. Metadata Editing Components

Shared metadata editing system.

---

## MetadataField

### Purpose

Generic read-only metadata display row.

### Used For

- filename
- filesize
- dimensions
- path
- dates

---

## TagEditor

### Purpose

Tag management UI for the info panel.

### Features

- Add tags via TagSuggestionList
- Remove tags with (x) per chip
- Bulk editing: shows shared tags with remove button; shows partial tags with mixed FilterChip

---

## CategoryEditor

### Purpose

Category management UI for the info panel.

### Features

- Add/remove categories
- Bulk editing: shows shared and partial categories via FilterChip states

---

## CollectionEditor

### Purpose

Collection membership editor for the info panel.

### Features

- Add/remove collections
- Multi-selection support

---

## MetadataSection

### Purpose

Logical metadata grouping container.

### Groups

- File Info (filename, path, dimensions, filesize, date added)
- Organization (tags, categories, collections)
- Status (missing state)

---

# 6. Collection Components

Collection browsing system.

---

## CollectionList

### Purpose

Displays all collections in the sidebar.

### Responsibilities

- Alphabetical ordering
- Empty-state styling (muted appearance for empty collections)
- Drag/drop targets

---

## CollectionListItem

### Purpose

Single collection entry in the sidebar.

### States

- normal
- active (currently browsing this collection)
- empty (no images; visually muted)
- drag-hover

---

## NewCollectionField

### Purpose

Inline create-new-collection UI.

### Features

- Inline text entry
- Validation

---

## CollectionCoverImage

### Purpose

Displays the cover image for a collection.

### Used In

- CollectionListItem

### Behavior

Automatically set to the first image added to the collection. Updates when the cover image is removed.

---

# 7. Image View Components

Full-resolution image viewer system.

---

## ImageViewport

### Purpose

Displays the full-resolution image.

### Responsibilities

- Zoom
- Pan
- Centering

---

## FullscreenOverlay

### Purpose

Fullscreen image presentation mode.

### Responsibilities

- Hide title bar and info panel
- Immersive image display

---

## ImageNavigationControls

### Purpose

Navigate previous/next within the current browsing context.

### Features

- Previous image
- Next image
- Fetches next cursor page from API when adjacent image is not yet loaded

---

## ZoomController

### Purpose

Centralized zoom behavior.

### Responsibilities

- Zoom level
- Zoom limits
- Zoom focus point

---

# 8. Import Workflow Components

Import pipeline UI.

---

## ImportConfirmModal

### Purpose

Allows the user to review and confirm an import before it begins.

### Contains

- ImportPreviewSection
- ConflictResolutionList (conditional — only shown when conflicts exist)

### Behavior

Always shown on drag-drop import. The conflicts section is omitted when no conflicts are detected.

---

## ImportPreviewSection

### Purpose

Displays a categorized summary of the pending import.

### Shows

- Images ready to import (count + first 10 thumbnails)
- Images already in library (count + first 10 thumbnails)

---

## ConflictResolutionList

### Purpose

Displays hash-conflict entries requiring user resolution.

### Contains

- ConflictCard instances

---

## ConflictCard

### Purpose

Single import conflict display.

### Contains

- Preview image
- Existing path
- Incoming path
- Resolution selector (existing path selected by default)

---

## ImportProgressOverlay

### Purpose

Displays active import progress after the user confirms.

---

## ImportCompletionNotification

### Purpose

Triggers a NotificationToast on successful import completion.

---

# 9. Notification Components

Application feedback system.

---

## NotificationToast

### Purpose

Transient notification displayed via GlobalNotificationOverlay.

### Used For

- Import complete
- Errors
- Warnings

---

## ErrorBanner

### Purpose

Persistent error display.

### Used For

- Backend unavailable at runtime
- API failures requiring user awareness

---

# 10. Empty State Components

Reusable empty-state displays.

---

## EmptyLibraryState

### Purpose

Displayed when no images are indexed.

### Shows

```text
NO IMAGES YET
DRAG AND DROP HERE TO ADD
```

---

## EmptyCollectionState

### Purpose

Displayed when a collection contains no images.

---

## EmptyFilterResultState

### Purpose

Displayed when active filters return no results.

---

# 11. Future/Backlog Components

Not Phase 2 scope — retained for planning reference.

---

## MoodBoardCanvas

Future infinite canvas system.

---

## SlideShowPlayer

Future slideshow system.

---

## SemanticSearchBar

Future AI search system.

---

## MasonryThumbnailGrid

Future alternate layout.

---

## AdjustableThumbnailSlider

Future user-adjustable thumbnail size control.
