# Found App: Frontend Development Guidelines

Welcome to the `found_app` codebase. This document outlines our architectural pattern, directory structure, and the rules governing how Python and QML interact.

We use a **Layered Model-View-ViewModel (MVVM)** pattern tailored specifically for the quirks of PySide6 and the QML engine. The goal of this architecture is strict separation of concerns, reliable memory management, and high testability.

## 1. Directory Structure & Responsibilities

To keep the project maintainable, every file has a single, unambiguous home based on its architectural role, not just its feature category.

```
found_app/
├── core/           # Infrastructure, lifetime management, and API clients
├── services/       # Shared, stateful cross-cutting concerns (Navigation, Selection)
├── viewmodels/     # UI state machines exposing properties/slots to QML
├── models/         # Standard Qt data models (e.g., QAbstractListModel)
├── providers/      # Heavy asset loaders (e.g., QQuickImageProvider)
├── theme/          # Style tokens: colors, fonts, spacing
└── qml/            # Complete user interface layout
    ├── shell/      # Window chrome, global hotkeys, and main router
    ├── views/      # Full screens / functional routes
    └── components/ # Reusable UI widgets
```

### Core Architecture Responsibilities

- **`core/`**: Houses application-wide infrastructure. The crown jewel here is `app_container.py` (`AppContainer`), which is solely responsible for instantiating services, resolving dependencies via constructor injection, registering Python objects with the QML engine, and managing startup/shutdown lifecycles.

- **`services/`**: Engines that drive cross-cutting logic. They do not care about UI layouts, but they maintain global state (e.g., what items are currently selected across the whole app).

- **`viewmodels/`**: The glue between data and display. ViewModels receive backend data, transform it into QML-friendly types, and expose `@Property` fields and `@Slot` methods. **ViewModels do not know which QML file is rendering them.**

- **`qml/`**: Strictly presentation. QML files bind to ViewModel properties and call ViewModel slots in response to user interactions.


## 2. Python to QML Communication

All Python objects that QML needs to access are registered in `AppContainer.wire_engine(engine)` and exposed as **context properties** on the QML engine's root context. QML files access them directly by the registered name — no module imports are needed.

### Registering objects

`AppContainer.wire_engine(engine)` is the single place all registrations happen:

```python
# core/app_container.py — wire_engine()
ctx = engine.rootContext()
ctx.setContextProperty("LibraryState", self._library_vm)
ctx.setContextProperty("SelectionManager", self._selection)
ctx.setContextProperty("Theme", self._theme)

# Plain Python values work too (strings, ints)
ctx.setContextProperty("baseUrl", self._api_base_url)
ctx.setContextProperty("foundVersion", version_string)

# Image providers are registered separately
engine.addImageProvider("thumbnails", self.thumbnail_provider)
```

### Using context properties in QML

Context properties are available everywhere in the QML tree with no import required:

```qml
// No imports needed to access Python objects
Item {
    color: Theme.background
    text: LibraryState.loadingState
    onClicked: SelectionManager.clear()
}
```

Thumbnail images are accessed via the registered image provider:

```qml
Image {
    source: "image://thumbnails/" + imageId
}
```

### What qualifies for registration

- **QObject subclasses**: ViewModels, services, theme, connection state — anything that exposes `@Property` or `@Slot` to QML.
- **Plain Python values**: Strings and primitives that QML reads but never modifies (e.g., `baseUrl`, `foundVersion`).
- **Image providers**: Subclasses of `QQuickImageProvider`, registered via `addImageProvider`.

### Ownership and memory safety

`AppContainer` must hold a strong Python reference to every registered object as an instance attribute (e.g., `self._library_vm`). If Python's garbage collector reclaims the object, QML is left with a dangling C++ pointer and will crash silently. `AppContainer` owns all registered objects for the lifetime of the application.

### Background work: QThread lifecycle

ViewModels run blocking I/O (API calls, file scans, imports, deletes) on private `QThread` subclasses so the UI stays responsive. **A `QThread`'s Python wrapper must never be allowed to drop to a zero refcount while `run()` is still executing.** If it is freed mid-run, `~QThread()` sees `isRunning() == True` and Qt calls `qFatal("QThread: Destroyed while thread is still running")`, aborting the whole process — surfacing as `SIGABRT` or `SIGSEGV` depending on what the fatal handler touches while unwinding.

This happens easily with a single overwritable attribute:

```python
# 🛑 UNSAFE — a second call overwrites the only Python reference to the
# first thread while it may still be running, and nothing keeps the
# wrapper alive until Qt has actually finished with it.
def loadCollectionImages(self, collection_id):
    thread = _ImagesThread(self._fetcher, collection_id)
    thread.result.connect(self._on_images_result)
    self._images_thread = thread
    thread.start()
```

The safe pattern — used throughout `viewmodels/` (e.g. `LibraryViewModel._delete_threads`, `MetadataViewModel._active_fetch_threads`) — keeps the thread in a list for its entire run and only releases it once Qt confirms it has actually finished:

```python
# ✅ SAFE — the list holds a strong reference for the thread's whole
# run; `finished` fires only once Qt has fully marked the thread as
# not-running, so list cleanup and deleteLater are race-free.
def loadCollectionImages(self, collection_id):
    thread = _ImagesThread(self._fetcher, collection_id)
    thread.result.connect(self._on_images_result)
    self._images_threads.append(thread)
    thread.finished.connect(lambda t=thread: self._images_threads.remove(t) if t in self._images_threads else None)
    thread.finished.connect(thread.deleteLater)
    thread.start()
```

Always pair an active-thread list with `finished -> remove-from-list` and `finished -> deleteLater`. If a new request can make an in-flight result stale (e.g. typing a new search term before the old one returns), also disconnect the old threads' `result` signal up front — see `TagSearchViewModel.search()` / `MetadataViewModel.loadImage()`.


## 3. QML Organization & Import Rules

To prevent broken engine paths and ensure fast component rendering, follow these layout rules within the `qml/` directory:

- **`qml/main.qml`**: Top-level entry point. Imports `"shell"` and instantiates `AppWindow`. Nothing else belongs here.
- **`shell/`**: Contains `AppWindow.qml`, `MainRouter.qml`, and `TitleBar.qml` — window chrome and navigation routing.
- **`views/`**: Represents distinct visual screens (e.g., `LibraryView.qml`, `CollectionView.qml`). A view typically maps closely to a primary ViewModel.
- **`components/`**: Houses modular UI elements (e.g., `FilterChip.qml`, `ThumbnailTile.qml`).

### The Cross-Directory Import Rule

The QML engine's import path points to `qml/`. Types in subdirectories (`shell/`, `views/`, `components/`) are not automatically visible to files in other subdirectories. When a file in one subdirectory needs a type from another, use an **explicit relative path import**:

```qml
// inside qml/views/LibraryView.qml
import QtQuick
import "../components"

Item {
    ThumbnailGrid { ... } // Resolved via relative directory import
}
```

```qml
// inside qml/shell/MainRouter.qml
import QtQuick
import "../views"
import "../components"

Item { ... }
```

Only import directories you actually use types from. `main.qml` uses `import "shell"` because it instantiates `AppWindow`; it does not need `"views"` or `"components"` directly.


## 4. Step-by-Step: Adding a New Feature

When tasked with adding a new feature slice (e.g., a "User Tags" manager), follow this flow:

1. **Define Data Models (`models/`):** If your feature needs a custom list or grid view, write a class extending `QAbstractListModel` inside `models/user_tags_model.py`.

2. **Build the ViewModel (`viewmodels/`):** Create `user_tags_view_model.py` as a `QObject` subclass. Use `@Property` for state QML will bind to and `@Slot()` for user interactions. Accept constructor dependencies (e.g., `ApiClient`) — `AppContainer` will inject them.

3. **Register in `AppContainer` (`core/app_container.py`):**
   - Instantiate your ViewModel in `__init__()`, passing its dependencies.
   - Register it in `wire_engine()` via `ctx.setContextProperty("UserTagsState", self._user_tags_vm)`.
   - Connect any cross-component signals in `_wire_signals()`.

4. **Create the Components (`qml/components/`):** Build individual UI chunks (e.g., `TagChip.qml`, `TagInputField.qml`).

5. **Compose the View (`qml/views/`):** Combine your components into a unified screen (e.g., `TagManagementView.qml`). Access your ViewModel by the context property name you registered in step 3:

   ```qml
   import QtQuick
   import "../components"

   Item {
       text: UserTagsState.count
       onClicked: UserTagsState.addTag(nameField.text)
   }
   ```

6. **Wire the Route (`qml/shell/MainRouter.qml`):** Add your new view to the central routing engine or sidebar.


## 5. Architectural Guardrails (Do's and Don'ts)

> 🛑 **NEVER call `setContextProperty` or `addImageProvider` outside `AppContainer.wire_engine()`.** All Python-to-QML registrations live in exactly one place. Scattering registrations across files makes the dependency graph invisible and breaks testability.

> 🛑 **NEVER let ViewModels manage UI layout.** A ViewModel should manipulate data collections, booleans, and strings. It should never know about pixels, anchors, colors, or specific QML file names.

> ⚠️ **Mind the Python Garbage Collector.** Every object registered via `setContextProperty` must be stored as an instance attribute on `AppContainer` (e.g., `self._library_vm`). If Python loses the reference, the GC will destroy the object and leave QML with a corrupted C++ pointer — often a silent crash.

> 🛑 **NEVER store a background `QThread` in a single overwritable attribute.** A second call replaces the only Python reference to the first thread, letting the GC free it mid-`run()` — Qt then aborts the whole process with `qFatal("QThread: Destroyed while thread is still running")`. Track active threads in a list and connect `finished` to both list-removal and `deleteLater`. See "Background work: QThread lifecycle" above.

> 💡 **Keep Component Names Contextual.** If a component is highly specific to a single view, prefix its name with that view (e.g., `CollectionSidebarItem.qml`). If it is used across 2 or more views, keep it generic (e.g., `FilterChip.qml`).
