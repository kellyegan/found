# FOUND — Phase 2 Component Inventory

[[IMGORG]]

This inventory is organized by:

- application-level systems
- reusable UI components
- view-specific components
- interaction systems

The goal is to:

- avoid duplicated QML components
- encourage composable UI architecture
- identify shared interaction patterns early
- separate logic components from visual components

This inventory intentionally focuses on **conceptual components**, not implementation details.

---

# 1. Application-Level Components

These components exist at the top level of the application and manage major application state.

---

## AppWindow

### Purpose

Root application window.

### Responsibilities

- Initialize application shell
- Manage top-level layouts
- Manage global overlays/modals
- Handle application-wide keyboard shortcuts

### Contains

- SplashScreen
- MainRouter
- GlobalNotificationOverlay
- ModalLayer

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
- ImportModal
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

- modals
- sidebars
- future dialogs

---

# 3. Thumbnail Browsing Components

Core image-browsing system.

---

## ThumbnailGrid

### Purpose

Main image browsing surface.

### Responsibilities

- virtualized rendering
- lazy loading
- horizontal scrolling
- selection rendering

### Contains

- ThumbnailTile instances

---

## ThumbnailTile

### Purpose

Individual image tile.

### Responsibilities

- render thumbnail
- display selection state
- display missing state
- display loading state

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

- preserve aspect ratio
- apply letterboxing
- async image loading

---

## ThumbnailPlaceholder

### Purpose

Fallback placeholder.

### Used For

- loading
- missing thumbnails
- failed generation

---

## SelectionOverlay

### Purpose

Visual selection indicator.

### Used In

- ThumbnailTile

### States

- selected
- multiselect
- active/focused

---

## HorizontalScrollViewport

### Purpose

Custom scrolling viewport.

### Responsibilities

- horizontal scrolling
- drag panning
- momentum handling

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

- tri-state filtering
- multiple category support

### States

- Off
- On
- Exclude

---

## TagSearchField

### Purpose

Tag lookup/filter field.

### Responsibilities

- text input
- autocomplete suggestions
- selected filter display

---

## TagSuggestionList

### Purpose

Displays matching tags.

### Behavior

Appears while typing.

---

## FilterChip

### Purpose

Displays active filters.

### Used For

- tags
- categories
- future filters

### States

- include
- exclude

---

## MissingImageToggle

### Purpose

Toggle missing-image visibility.

---

# 5. Metadata Editing Components

Shared metadata editing system.

---

## MetadataField

### Purpose

Generic metadata display row.

### Used For

- filename
- filesize
- dimensions
- path
- dates

---

## TagEditor

### Purpose

Tag management UI.

### Features

- add/remove tags
- bulk editing support
- autocomplete integration

---

## CategoryEditor

### Purpose

Category management UI.

### Features

- add/remove categories
- multi-selection editing

---

## CollectionEditor

### Purpose

Collection membership editor.

### Features

- add/remove collections
- multi-selection support

---

## MetadataSection

### Purpose

Logical metadata grouping.

### Example Groups

- File Info
- Organization
- Status

---

# 6. Collection Components

Collection browsing system.

---

## CollectionList

### Purpose

Displays collections in sidebar.

### Responsibilities

- alphabetical ordering
- empty-state styling
- drag/drop targets

---

## CollectionListItem

### Purpose

Single collection entry.

### States

- normal
- active
- empty
- drag-hover

---

## NewCollectionField

### Purpose

Create new collection UI.

### Features

- inline creation
- validation

---

## CollectionCoverImage

### Purpose

Displays collection preview image.

### Future Use

- collection cards
- collection overview pages

---

# 7. Image View Components

Full-resolution image viewer system.

---

## ImageViewport

### Purpose

Displays full-resolution image.

### Responsibilities

- zoom
- pan
- centering

---

## FullscreenOverlay

### Purpose

Fullscreen image presentation.

### Responsibilities

- hide chrome
- immersive viewing

---

## ImageNavigationControls

### Purpose

Navigate within current browsing context.

### Features

- previous image
- next image

---

## ZoomController

### Purpose

Centralized zoom behavior.

### Responsibilities

- zoom level
- zoom limits
- zoom focus

---

# 8. Import Workflow Components

Import pipeline UI.

---

## ImportConflictModal

### Purpose

Resolve import conflicts.

### Contains

- ImportPreviewSection
- ConflictResolutionList
- ImportActionBar

---

## ImportPreviewSection

### Purpose

Preview import result categories.

### Used For

- ready-to-import
- already-in-library

---

## ConflictResolutionList

### Purpose

Displays import conflicts.

### Contains

- ConflictCard instances

---

## ConflictCard

### Purpose

Single import conflict display.

### Contains

- preview image
- existing path
- incoming path
- resolution selector

---

## ImportProgressOverlay

### Purpose

Displays active import progress.

### Future Enhancement

Background import monitoring.

---

## ImportCompletionNotification

### Purpose

Displays successful import completion.

---

# 9. Notification Components

Application feedback system.

---

## NotificationToast

### Purpose

Transient notification display.

### Used For

- import complete
- errors
- warnings

---

## ErrorBanner

### Purpose

Persistent error display.

### Used For

- backend unavailable
- API failures

---

# 10. Empty State Components

Reusable empty-state system.

---

## EmptyLibraryState

### Purpose

Displayed when library contains no images.

---

## EmptyCollectionState

### Purpose

Displayed for empty collections.

---

## EmptyFilterResultState

### Purpose

Displayed when filters return no images.

---

# 11. Interaction System Components

Non-visual interaction logic systems.

---

## SelectionManager

### Purpose

Centralized selection state.

### Responsibilities

- single selection
- multi-selection
- range selection

---

## DragDropManager

### Purpose

Centralized drag/drop handling.

### Responsibilities

- drag sources
- drop targets
- hover feedback

---

## FilterStateManager

### Purpose

Centralized filter state.

### Responsibilities

- active tags
- categories
- missing-image filter
- future filters

---

## ThumbnailLoader

### Purpose

Thumbnail request management.

### Responsibilities

- async loading
- retries
- prioritization

---

## ImageLoader

### Purpose

Full-resolution image loading.

### Responsibilities

- async loading
- cancellation
- failure handling

---

## ImportJobManager

### Purpose

Tracks import jobs.

### Responsibilities

- progress tracking
- completion events
- polling

---

# 12. Future/Backlog Components

Not Phase 2 but useful for planning.

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

Future thumbnail size control.
