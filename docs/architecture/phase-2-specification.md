# FOUND — Phase 2 Specification

## 1. Product Overview

### Purpose

Found is a desktop application for managing large personal image reference libraries intended for artists, designers, researchers, and other creative users.

The application indexes images in their existing filesystem locations while storing metadata, organizational data, and generated thumbnails locally.

The Phase 2 frontend provides the primary graphical interface for:

- Browsing image collections
- Searching and filtering images
- Organizing images with tags, categories, and collections
- Viewing full-resolution images
- Importing images into the library
- Managing image metadata

The frontend communicates exclusively through the backend REST API.

---

## 2. Design Principles

### Image-first interface

The interface prioritizes image visibility over controls and metadata.

- Images occupy the majority of screen space.
- Metadata panels remain secondary and collapsible.
- Text labels and interface chrome should remain minimal.
- Sidebars and overlays appear only when needed.

---

### Minimal visual distraction

The application should feel visually calm and unobtrusive.

- Dark-mode interface
- Black or near-black background
- Light text
- Minimal borders and separators
- Sparse interface elements

---

### Large-scale browsing

The interface is designed to support browsing libraries of 50,000+ images efficiently.

The browsing experience should remain fluid and responsive regardless of library size.

---

### Non-destructive organization

Found does not manage or relocate original image files.

- Images remain in original locations.
- Removing an image from the library does not delete the file.
- Collections are virtual organizational groupings.

---

## 3. Technical Architecture

### Architecture Overview

```text
Frontend GUI        External Tools
      │___________________|
      |
      ▼
FastAPI REST API
      │
 ┌────┴────┐
 │         │
 ▼         ▼
SQLite   Thumbnail Cache
```

Original image files remain on disk and are never copied into application storage.

---

### Technology Stack

#### Language

- Python 3.13+

#### Core Packages

- PySide6 — user interface framework
- QtQuick/QML — visual UI layer
- httpx — API communication

---

### Frontend Architecture

The GUI communicates exclusively through an API client layer.

The frontend must never:

- access the database directly
- access thumbnail cache directly

All application data must pass through the REST API.

---

## 4. Application State & Navigation

### Application States

The application supports the following high-level states:

- Splash / Backend Loading
- Backend Error
- Empty Library
- Library Browsing
- Collection Browsing
- Image Viewing
- Import Review
- Import Processing

---

### Navigation Model

Found uses browser-style navigation history.

Examples:

```text
Library
→ Collection
→ Image View
→ Back
→ Collection
```

```text
Filtered Library
→ Image View
→ Back
→ Same filtered library state
```

---

### State Persistence

When navigating between views, the application should preserve:

- active filters
- selected images
- scroll position
- collection state
- current browsing context

Example:

```text
Filter: Architecture
Scroll Position: Image 32,441
Selection: 5 images

→ Open Image View
→ Back

Return to same state
```

---

## 5. Core UI Views

### 5.1 Splash Screen

#### Purpose

Displayed while backend services initialize.

The splash screen occupies the full application window.

---

#### Components

**Title**

Centered horizontally and vertically.

**Version**

Displayed near bottom-left area.

**Status**

Centered near bottom area.

Displays:

- startup progress
- retry status
- backend errors

**License & Copyright**

Displayed near bottom-right area.

**Background Image**

Future enhancement:

- customizable image
- optionally sourced from library

---

#### Backend Failure Behavior

If backend startup fails:

- splash screen displays error message
- 2 automatic retry attempts occur, spaced 10 seconds apart
- after retries are exhausted the error state is displayed
- user may quit application manually at any point

---

#### User Flow

1. Application launches
2. Backend initializes
3. Splash screen remains visible until the backend is ready and the user clicks to continue

---

### 5.2 Library View

#### Purpose

Primary browsing interface for the image library.

This is the central workspace of the application.

---

#### Layout Structure

```text
+--------------------------------------------------+
| Title Bar                      |    Filter Panel |
+--------------------------------------------------+
|          |                                       |
|  Sidebar |               Thumbnail               |
|  overlay |                 Grid                  |
|          |                                       |
|          |                                       |
|          |---------------------------------------+
|          |           Information Panel           |
+--------------------------------------------------+
```

---

#### Title Bar

Located at top-left.

Contains:

- current page title
- back navigation
- current collection name (if applicable)

---

#### Filter Panel

Located at top-right.

Contains:

- category filtering
- tag filtering
- missing-image filtering (only visible when there are missing images)

---

#### Sidebar Overlay

Collapsible overlay panel.

Appears above thumbnail grid.

Contains:

- collections list
- new collection field/button

Collections are displayed alphabetically.

Collections with no images appear visually muted.

The sidebar is hidden while browsing a collection.

---

#### Thumbnail Grid

Primary browsing area.

**Layout**

- Uniform square thumbnail cells
- Original image aspect ratio preserved
- Letterboxing applied where necessary
- Multi-row horizontal scrolling layout
- Row count derived from window height and a target thumbnail size of 180px:
  `rowCount = max(2, round(viewportHeight / 180))`
  `actualThumbnailSize = viewportHeight / rowCount`

**Scrolling Behavior**

Scrolling occurs horizontally from left to right.

Supported interactions:

- mouse wheel scrolling
- click-and-drag panning

The grid must preserve scroll position during navigation.

**Thumbnail Loading**

Thumbnails:

- load lazily
- render virtually
- request data incrementally

QML tile objects are instantiated for the visible columns plus a ±3 column buffer.
API data is prefetched 3 cursor pages (300 images) ahead of the visible right edge.
A LRU thumbnail cache of ~500 entries is maintained in memory.

**Missing Images**

If source image no longer exists:

- thumbnail remains visible if available
- image displays missing-image indicator
- image metadata remains preserved

Missing images can be filtered from the filter panel.

**Failed Thumbnail Generation**

If thumbnail generation fails:

- generic placeholder thumbnail appears
- automatic retry occurs
- image remains openable in Image View if possible

---

#### Information Panel

Located along bottom of window.

Displays metadata for current selection.

**Read-only fields**

- filename
- path
- dimensions
- filesize
- date added
- missing state

**Editable fields**

- tags — uses the Tag Editing Widget (see section 6)
- categories
- collections

**Bulk editing behavior**

When multiple images are selected, editable fields show the intersection of their metadata:

- Items shared by all selected images appear with an (x) to remove from all.
- Items held by some but not all images appear with a mixed/partial indicator. Clicking adds to all; clicking (x) removes from those that have it.
- The add field works as normal and applies the addition to all selected images.

---

#### Empty Library State

If no images exist:

Centered message displays:

```text
NO IMAGES YET
DRAG AND DROP HERE TO ADD
```

---

#### Filtering

**Categories**

Category filters support:

- On
- Off
- Exclude

Multiple category filters may be active simultaneously.

---

**Tags**

Users type into the tag search field.

Matching tags appear as autocomplete suggestions.

Selecting a suggestion adds that tag to the active filter list. Each active tag displays an (x) button to remove it from the list.

Filtering is applied only after selecting a suggestion, not while typing.

Each active tag filter supports:

- On (include)
- Exclude

Multiple tag filters may be active simultaneously.

---

**Collections**

Clicking a collection:

- filters library to that collection
- hides sidebar
- updates title bar

Only one collection may be viewed at a time.

Collections behave similarly to virtual subfolders.

---

### 5.3 Image View

#### Purpose

Displays full-resolution image preview.

Supports image inspection and metadata editing.

---

#### Title Bar

Contains:

- back navigation
- current image title/path context

---

#### Image Display

Centered in window.

Supports:

- zoom
- pan
- fullscreen

---

#### Information Panel

Located along bottom edge.

Displays same metadata fields as Library View.

Supports:

- editing tags
- editing categories
- editing collections

---

#### Navigation

Users can navigate:

- previous image
- next image

Navigation remains constrained to the current browsing context (active filters, active collection, or active selection set).

If the adjacent image is within the already-loaded buffer, it is used directly. If it lies beyond the loaded buffer, the frontend fetches the next cursor page from the API before navigating.

---

#### Fullscreen Behavior

Title bar and information panel may be hidden so image occupies entire window.

---

### 5.4 Import Conflict Modal

#### Purpose

Allows users to review and resolve import conflicts before finalizing imports.

Imports may be initiated from any application view.

---

#### Images Ready To Import

Displays:

- title
- first 10 thumbnails
- total count

---

#### Images Already In Library

Displays:

- title
- first 10 thumbnails
- total count

---

#### Conflicts Section

Displays:

- thumbnail preview
- conflicting paths
- selection controls

Existing path remains default selection.

---

#### Import Workflow

1. User drags files/folders into application
2. Frontend validates supported image types
3. Frontend sends paths to backend preview endpoint
4. Backend returns categorized results:
   - supported file types
   - duplicates
   - conflicts
5. Import modal opens showing:
   - images ready to import
   - images already in library (if any)
   - conflicts section (only shown if conflicts exist)
6. User resolves any conflicts, then confirms or cancels
7. Backend begins import job
8. Success notification appears when import completes
9. Library returns to a temporary filtered state showing recently imported images

---

#### Import Jobs

Each import job operates independently.

Imports may continue in background after initiation.

---

## 6. Shared Interaction Models

### Selection Behavior

#### Single Click

Select single image.

#### Ctrl/Cmd Click

Toggle image selection.

#### Shift Click

Select range.

#### Double Click

Open Image View.

#### Escape

Clear selection.

---

### Drag & Drop Behavior

#### Supported Sources

- External file manager
- Thumbnail grid selections

#### Supported Targets

- Collections
- Main application window

#### Collection Drag Behavior

Dragging images onto a collection in the sidebar:

- adds images to that collection
- displays hover feedback on the collection target
- may display insertion animation

#### Main Window Drag Behavior

Dragging files or folders from an external file manager onto the main window:

- always triggers the import preview modal
- the modal displays the categorized preview (ready to import, already in library, conflicts if any)
- the user confirms or cancels before any import begins

---

### Tag Editing Widget

Used in the Information Panel (Library View and Image View) for adding and removing tags on the selected image(s).

#### Layout

Tags are displayed as inline chips, followed immediately by a text input field within the same container row.

```text
[ Devsheet  x ] [ Lotis  x ]  Type and enter ...
```

#### Chip appearance

Each tag chip displays the tag name and a circular remove button (×). Clicking × removes that tag from the selected image(s).

#### Adding a tag

The user types into the inline input field. As they type, a dropdown of autocomplete suggestions appears below the widget, populated by `GET /tags?search=<query>`. Selecting a suggestion from the dropdown adds that tag.

If the user types a name that does not match any existing tag and presses Enter, a new tag is created and immediately applied.

#### Autocomplete behavior

- Suggestions appear after the first character is typed.
- Up to 20 suggestions are shown, ordered alphabetically.
- Already-applied tags are excluded from suggestions.
- Pressing Escape closes the suggestion list without adding a tag.
- Pressing Enter with no suggestion highlighted confirms the typed text as a new tag.

#### Bulk editing

When multiple images are selected, the widget reflects the intersection and union of their tags:

- Tags shared by **all** selected images appear as normal chips with a (×) to remove from all.
- Tags held by **some but not all** selected images appear as chips with a mixed/partial indicator. Clicking the chip adds it to all; clicking (×) removes it from those that have it.
- Adding a tag via the input applies it to all selected images.

---

### Bulk Metadata Editing

Multiple selected images support:

- add/remove tags
- add/remove categories
- add/remove collections

Thumbnail grid updates dynamically if active filters change.

---

## 7. Keyboard Shortcuts

### General

| Shortcut   | Action                           |
| ---------- | -------------------------------- |
| Escape     | Clear selection / close overlays |
| Enter      | Open selected image              |
| Ctrl/Cmd+A | Select all                       |

---

### Navigation

| Shortcut            | Action          |
| ------------------- | --------------- |
| Left / Right Arrows | Navigate images |
| Backspace           | Navigate back   |

---

### Image View

| Shortcut            | Action                |
| ------------------- | --------------------- |
| Space               | Toggle fullscreen     |
| Left / Right Arrows | Previous / next image |

Future phases may expand keyboard-driven workflows.

---

## 8. API Client Requirements

### Responsibilities

The API client layer manages:

- backend communication
- request lifecycle
- thumbnail retrieval
- import job tracking
- error handling
- retries
- request cancellation

---

### Communication Rules

- GUI communicates only through REST API
- No direct database access
- No direct filesystem metadata access
- No direct thumbnail cache access

---

### Asynchronous Behavior

All API communication should remain asynchronous.

The UI thread must never block on:

- image loading
- thumbnail loading
- imports
- metadata operations

---

## 9. Performance Requirements

### Thumbnail Grid Performance

The application must remain responsive while browsing 50,000+ indexed images.

Requirements:

- virtualized rendering
- lazy thumbnail loading
- incremental data prefetch (100 images per cursor page, 3 pages ahead)
- smooth scrolling

---

### UI Responsiveness

The following operations must not freeze the UI:

- filtering
- scrolling
- importing
- metadata editing
- thumbnail loading

---

### Window Resizing

Row count is derived from window height and the target thumbnail size (180px).

As window width increases, additional thumbnail columns become visible.

Future versions may support user-adjustable thumbnail sizing.

---

## 10. Non-Goals (Phase 2)

The following features are explicitly outside Phase 2 scope:

- image editing
- recursive imports
- cloud synchronization
- AI semantic search
- hierarchical tags
- plugin system
- annotations
- mood board annotations
- multi-window support
- file deletion from disk
- dynamic collections
- multiple databases
- masonry layout
- adjustable thumbnail sizing
- tag suggestions based on AI
- ratings/favorites system

---

## 11. Future Backlog

Potential future enhancements include:

- adjustable thumbnail sizes
- horizontal masonry layout
- mood board annotations
- slideshow system
- AI semantic search
- CLIP embeddings
- weighted inspiration browsing
- browser extensions
- plugin architecture
- dynamic collections
- advanced keyboard workflows
- collection ordering options
- pinned collections
- multi-database support
- AI-generated tag suggestions
