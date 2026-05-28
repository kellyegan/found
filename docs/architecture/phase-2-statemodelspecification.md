# FOUND — Phase 2 State Model Specification

[[IMGORG]]

## Purpose

This document defines the application state architecture for Found.

The purpose of the state model is to:

- centralize UI behavior
- preserve navigation consistency
- support browser-style history
- maintain responsive async workflows
- simplify QML architecture
- support restoration of browsing context

This specification defines:

- global application state
- view state
- selection state
- filtering state
- loading state
- navigation state
- import state

This is a conceptual architecture document and does not prescribe implementation details.

---

# 1. State Architecture Principles

## Single Source of Truth

Each major application system should maintain a single authoritative state source.

Examples:

| System     | State Owner        |
| ---------- | ------------------ |
| Navigation | NavigationManager  |
| Selection  | SelectionManager   |
| Filters    | FilterStateManager |
| Imports    | ImportJobManager   |

---

## State Persistence

Navigation should preserve:

- filters
- scroll position
- selection
- current collection
- browsing context

Returning to a previous view should restore the exact prior state.

---

## Asynchronous State Updates

All backend communication is asynchronous.

The UI must remain responsive during:

- thumbnail loading
- filtering
- imports
- metadata updates
- image loading

---

## View Independence

Views should derive their displayed state from centralized state managers rather than storing duplicate local state.

---

# 2. Global Application State

## AppState

Top-level application lifecycle state.

---

### States

| State           | Description                        |
| --------------- | ---------------------------------- |
| Launching       | Application process starting       |
| BackendStarting | Backend initialization in progress |
| BackendRetrying | Backend failed, retrying           |
| Ready           | Application operational            |
| BackendError    | Backend unavailable                |
| ShuttingDown    | Application exiting                |

---

### Responsibilities

Controls:

- splash screen visibility
- backend retry flow
- fatal error handling
- startup completion

---

# 3. Navigation State

## NavigationManager

Controls browser-style navigation history.

---

## Navigation Entry Structure

Each navigation entry stores:

| Property        | Purpose                 |
| --------------- | ----------------------- |
| route           | Current view            |
| filters         | Active filters          |
| selection       | Selected image IDs      |
| scrollPosition  | Thumbnail grid position |
| collectionId    | Current collection      |
| focusedImageId  | Active image            |
| fullscreenState | Image view fullscreen   |
| timestamp       | History ordering        |

---

## Routes

| Route       | Description           |
| ----------- | --------------------- |
| Splash      | Startup screen        |
| Library     | Main library browsing |
| Collection  | Collection browsing   |
| ImageView   | Full image viewer     |
| ImportModal | Import conflict flow  |

---

## Navigation Behavior

### Push Navigation

Occurs when:

- entering image view
- entering collection view
- opening modal flows

---

### Pop Navigation

Occurs when:

- back navigation activated
- modal closed

---

### Restoration Behavior

Returning to previous route restores:

- filters
- selection
- scroll position
- browsing context

---

# 4. Library Browsing State

## LibraryViewState

Controls the main thumbnail browsing experience.

---

## Stored State

| Property           | Purpose                    |
| ------------------ | -------------------------- |
| visibleImageIds    | Current result set         |
| scrollOffset       | Horizontal scroll position |
| selectedImageIds   | Current selection          |
| activeCollectionId | Current collection         |
| activeFilters      | Applied filters            |
| sidebarOpen        | Sidebar visibility         |
| loadingState       | Current loading state      |

---

## Loading States

| State              | Description                   |
| ------------------ | ----------------------------- |
| Idle               | No active loading             |
| Loading            | Initial load                  |
| IncrementalLoading | Loading additional thumbnails |
| Empty              | No images available           |
| Error              | Failed request                |

---

# 5. Filter State

## FilterStateManager

Centralized filter management.

---

## Filter Types

### Tag Filters

Structure:

| Property | Example         |
| -------- | --------------- |
| tag      | architecture    |
| mode     | include/exclude |

---

### Category Filters

Structure:

| Property | Example         |
| -------- | --------------- |
| category | reference       |
| mode     | include/exclude |

---

### Missing Image Filter

Boolean state.

| State | Meaning           |
| ----- | ----------------- |
| Off   | Show all images   |
| On    | Show missing only |

---

## Filter Combination Rules

### Tags

Multiple tag filters may be active simultaneously.

---

### Categories

Multiple category filters may be active simultaneously.

---

### Collections

Only one collection may be active at a time.

Collections behave like virtual folders.

---

## Filter Persistence

Filters persist during:

- image navigation
- collection navigation
- back navigation

---

# 6. Selection State

## SelectionManager

Centralized image selection system.

---

## Selection Data

| Property            | Purpose                    |
| ------------------- | -------------------------- |
| selectedImageIds    | Current selected images    |
| primarySelectionId  | Focused image              |
| selectionAnchor     | Shift-select anchor        |
| lastInteractionType | Mouse/keyboard interaction |

---

## Selection Modes

| Mode     | Description              |
| -------- | ------------------------ |
| Single   | One selected image       |
| Multiple | Multiple selected images |
| Range    | Shift-selected range     |
| Empty    | No selection             |

---

## Selection Persistence

Selection state persists when:

- entering image view
- returning from image view
- navigating browser history

Selection resets only when:

- explicitly cleared
- incompatible navigation occurs

---

# 7. Thumbnail Grid State

## ThumbnailGridState

Controls rendering behavior of thumbnail browsing.

---

## Stored State

| Property       | Purpose                      |
| -------------- | ---------------------------- |
| visibleRange   | Currently rendered range     |
| preloadRange   | Buffered thumbnails          |
| thumbnailSize  | Current thumbnail dimensions |
| rowCount       | Fixed row count              |
| viewportWidth  | Current visible width        |
| scrollVelocity | Scroll momentum              |

---

## Rendering Rules

### Virtualization

Only visible thumbnails and nearby buffer thumbnails should render.

---

### Lazy Loading

Thumbnail requests occur incrementally during scrolling.

---

### Placeholder States

Thumbnail tiles may enter:

| State   | Description                 |
| ------- | --------------------------- |
| Loading | Thumbnail request active    |
| Loaded  | Thumbnail available         |
| Missing | Source image missing        |
| Failed  | Thumbnail generation failed |

---

# 8. Image View State

## ImageViewState

Controls full-resolution viewing experience.

---

## Stored State

| Property       | Purpose                 |
| -------------- | ----------------------- |
| currentImageId | Displayed image         |
| currentContext | Source browsing context |
| zoomLevel      | Current zoom            |
| panOffset      | Current pan position    |
| fullscreen     | Fullscreen enabled      |
| uiVisible      | Overlay visibility      |
| loadingState   | Image loading status    |

---

## Context Navigation

Image navigation occurs within:

- current filter set
- current collection
- current browsing result set

---

## Loading States

| State   | Description   |
| ------- | ------------- |
| Loading | Image loading |
| Loaded  | Ready         |
| Missing | File missing  |
| Failed  | Load failed   |

---

# 9. Metadata Editing State

## MetadataEditorState

Tracks metadata editing interactions.

---

## Stored State

| Property           | Purpose                    |
| ------------------ | -------------------------- |
| editingTargetIds   | Affected images            |
| pendingTags        | Unsaved tag changes        |
| pendingCategories  | Unsaved category changes   |
| pendingCollections | Unsaved collection changes |
| savingState        | Save operation status      |

---

## Save States

| State  | Description       |
| ------ | ----------------- |
| Idle   | No active save    |
| Saving | API update active |
| Saved  | Update complete   |
| Failed | Save failed       |

---

# 10. Sidebar State

## SidebarState

Controls collection sidebar behavior.

---

## Stored State

| Property              | Purpose                 |
| --------------------- | ----------------------- |
| open                  | Sidebar visible         |
| activeCollectionId    | Highlighted collection  |
| dragHoverCollectionId | Current drag target     |
| creationMode          | Creating new collection |

---

## Visibility Rules

### Visible

- standard library browsing

### Hidden

- collection browsing
- fullscreen image view

---

# 11. Import System State

## ImportJobManager

Controls import workflow and background job tracking.

---

## Import Job Structure

| Property    | Purpose               |
| ----------- | --------------------- |
| jobId       | Unique import ID      |
| status      | Current state         |
| progress    | Completion percentage |
| addedImages | Imported images       |
| conflicts   | Conflict entries      |
| failures    | Failed imports        |

---

## Import States

| State     | Description         |
| --------- | ------------------- |
| Preparing | Frontend validation |
| Reviewing | Conflict modal open |
| Importing | Backend processing  |
| Completed | Import succeeded    |
| Failed    | Import failure      |
| Cancelled | User cancelled      |

---

## Concurrent Imports

Multiple import jobs may exist simultaneously.

Each job maintains independent state.

---

# 12. Notification State

## NotificationManager

Controls transient user feedback.

---

## Notification Types

| Type    | Example             |
| ------- | ------------------- |
| Success | Import completed    |
| Warning | Missing image       |
| Error   | Backend unavailable |
| Info    | Retry in progress   |

---

## Notification Behavior

Notifications may:

- auto-dismiss
- persist until acknowledged
- stack visually

---

# 13. Backend Connection State

## BackendConnectionState

Tracks API availability.

---

## States

| State        | Description           |
| ------------ | --------------------- |
| Connected    | API available         |
| Reconnecting | Retry active          |
| Disconnected | API unavailable       |
| Failed       | Fatal startup failure |

---

## Behavior

When disconnected:

- UI remains responsive
- errors displayed
- retries occur automatically

---

# 14. Drag & Drop State

## DragDropState

Tracks active drag operations.

---

## Stored State

| Property        | Purpose              |
| --------------- | -------------------- |
| dragging        | Active drag          |
| draggedImageIds | Images being dragged |
| hoverTarget     | Current drop target  |
| dragSource      | Origin view          |

---

## Drag Sources

- thumbnail grid
- external file manager

---

## Drop Targets

- collections
- application window

---

# 15. Empty State Model

## EmptyStateManager

Controls empty-state UI presentation.

---

## Empty State Types

| State             | Description                   |
| ----------------- | ----------------------------- |
| EmptyLibrary      | No images indexed             |
| EmptyCollection   | Collection contains no images |
| EmptyFilterResult | No filter matches             |
| MissingImagesOnly | All visible images missing    |

---

# 16. Future State Expansion

Future phases may add:

- mood board state
- slideshow playback state
- AI search state
- embedding generation state
- plugin state
- multi-database state

---
