# Found App — Frontend Restructure Plan (Final)

## Target structure

```
found_app/                              # renamed from frontend/
├── __init__.py
├── __main__.py                         # ~30 lines after Phase 2
├── version.py
├── core/
│   ├── api_client.py                   # api/client.py + absorbs all _make_* closures
│   ├── app_controller.py               # app/controller.py
│   ├── app_state.py                    # state/app_state.py
│   ├── bootstrap.py                    # NEW: AppContainer — ViewModel wiring & signal connections
│   ├── process_manager.py              # backend/process_manager.py
│   └── connection_monitor.py           # backend/connection_monitor.py
├── services/
│   ├── filter_state.py                 # filters/filter_state_manager.py
│   ├── navigation.py                   # navigation/navigation_manager.py
│   └── selection.py                    # selection/selection_manager.py
├── viewmodels/
│   ├── library_view_model.py           # library/view_model.py (keep _PageThread, _VerifyThread here)
│   ├── collections_view_model.py
│   ├── collection_editor_view_model.py
│   ├── categories_view_model.py
│   ├── category_editor_view_model.py
│   ├── import_view_model.py
│   ├── metadata_view_model.py
│   ├── tag_editor_view_model.py
│   └── tag_search_view_model.py
├── models/
│   └── thumbnail_grid_model.py         # library/thumbnail_grid_model.py
├── providers/
│   └── thumbnail_provider.py           # library/thumbnail_provider.py
├── theme/
│   └── theme.py
├── qml/
│   ├── main.qml                        # stays at root
│   ├── shell/
│   │   ├── AppWindow.qml
│   │   ├── TitleBar.qml
│   │   └── MainRouter.qml
│   ├── views/
│   │   ├── SplashScreen.qml
│   │   ├── LibraryView.qml
│   │   ├── CollectionView.qml
│   │   └── ImageView.qml
│   └── components/
│       ├── ThumbnailGrid.qml
│       ├── ThumbnailTile.qml
│       ├── CategoriesBar.qml
│       ├── CategoryChip.qml
│       ├── CollectionItem.qml
│       ├── CollectionsSidebar.qml
│       ├── FilterChip.qml
│       ├── FilterDropdown.qml
│       ├── ImportPanel.qml
│       ├── MetadataOverlay.qml
│       └── TagSearchField.qml
└── tests/
```

---

## QML relative imports required

Traced from the actual component dependency graph — only five files need additions:

| File                       | Add import                                       |
| -------------------------- | ------------------------------------------------ |
| `main.qml`                 | `import "shell"`                                 |
| `shell/MainRouter.qml`     | `import "../views"` and `import "../components"` |
| `shell/TitleBar.qml`       | `import "../components"`                         |
| `views/LibraryView.qml`    | `import "../components"`                         |
| `views/CollectionView.qml` | `import "../components"`                         |

All `components/` files that reference siblings (`ThumbnailGrid → ThumbnailTile`, `CategoriesBar → CategoryChip`, etc.) need nothing — same-directory resolution is automatic.

`__main__.py` needs no `addImportPath()` calls for QML resolution. Python just loads `qml/main.qml` and QML handles the rest.

---

## QML registration — three tiers

**Tier 1 & 2: Existing ViewModels and services — `qmlRegisterSingletonInstance`**

Python retains full constructor control; QML gets a clean import namespace instead of implicit globals.

```python
from PySide6.QtQml import qmlRegisterSingletonInstance

# services
qmlRegisterSingletonInstance(SelectionManager,  "com.found.services", 1, 0, "Selection",   selection)
qmlRegisterSingletonInstance(NavigationManager, "com.found.services", 1, 0, "Navigation",  navigation)
qmlRegisterSingletonInstance(FilterStateManager,"com.found.services", 1, 0, "FilterState", filter_state)

# viewmodels
qmlRegisterSingletonInstance(LibraryViewModel,  "com.found.viewmodels", 1, 0, "LibraryState", library_vm)
# etc.
```

QML side: `import com.found.services 1.0` then use `Selection`, `Navigation`, `FilterState` directly.

**Tier 3: New ViewModels going forward — `@QmlElement`**

Design without constructor args; inject deps via `@Property` setters after QML instantiation.

```python
QML_IMPORT_NAME = "com.found.viewmodels"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class NewViewModel(QObject):
    ...
```

---

## Target `__main__.py`

```python
def main():
    app = QGuiApplication(sys.argv)

    container = AppContainer()           # core/bootstrap.py
    container.register_qml_types()       # all qmlRegisterSingletonInstance calls

    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbnails", container.thumbnail_provider)
    engine.load(str(Path(__file__).parent / "qml" / "main.qml"))

    if not engine.rootObjects():
        sys.exit(1)

    app.aboutToQuit.connect(container.shutdown)
    container.start()
    exit_code = app.exec()
    del engine
    sys.exit(exit_code)
```

---

## Phased execution

- [*] **Phase 0 — Package rename + ApiClient consolidation** _(Lowest blast radius — no logic changes)_ **COMPLETE**

1. `git mv frontend found_app`
2. Find/replace `from frontend.` → `from found_app.` across all source and test files
3. Update `python -m frontend` → `python -m found_app` in `CLAUDE.md` and `Makefile`
4. Consolidate all `_make_*` closures from `__main__.py` into named methods on `ApiClient` (e.g. `api_client.fetch_page(...)`, `api_client.list_collections()`)
5. Run full test suite — no logic changed, only paths and one class

---

- [ ] **Phase 1 — QML restructure** _(Impacts `test_qml_shell.py` only — no Python logic changes)_

1. Create `qml/shell/`, `qml/views/`, `qml/components/`
2. Move QML files into subdirectories
3. Add the five relative `import` statements listed above
4. Update `test_qml_shell.py` — `QML_DIR` currently assumes a flat directory; tests loading `views/LibraryView.qml` need updated paths
5. Run tests, then run the app manually to verify UI

---

- [ ] **Phase 2 — Core & Services** _(Move one file at a time, run tests after each)_

1. `backend/process_manager.py` → `core/process_manager.py`
2. `backend/connection_monitor.py` → `core/connection_monitor.py`
3. `app/controller.py` → `core/app_controller.py`
4. `state/app_state.py` → `core/app_state.py`
5. `api/client.py` → `core/api_client.py`
6. `filters/filter_state_manager.py` → `services/filter_state.py`
7. `navigation/navigation_manager.py` → `services/navigation.py`
8. `selection/selection_manager.py` → `services/selection.py`
9. Create `core/bootstrap.py` (`AppContainer` class) — migrate ViewModel instantiation and all cross-ViewModel signal wiring out of `__main__.py`

---

- [ ] **Phase 3 — ViewModels, Models, Providers** _(One feature slice at a time; update test imports as you go)_

1. `library/thumbnail_grid_model.py` → `models/thumbnail_grid_model.py`
2. `library/thumbnail_provider.py` → `providers/thumbnail_provider.py`
3. `library/view_model.py` → `viewmodels/library_view_model.py` *(private thread classes stay here)*
4. Repeat for each remaining feature module
5. For each ViewModel migrated: replace its `setContextProperty` with `qmlRegisterSingletonInstance` in `AppContainer`
6. Keep test files named for their feature (`test_library_view_model.py`); only update the import paths, don't reorganize the test directory
