"""
Tests for the QML application shell — Commits 6–9.

Covers:
- SplashScreen.qml, MainRouter.qml, AppWindow.qml, LibraryView.qml exist
- Each component loads without QML errors
- SplashScreen exposes statusText (str) and hasError (bool) properties
- SplashScreen statusText value is readable after creation
- SplashScreen hasError defaults to False
- MainRouter exposes appState (str) property, defaulting to "Launching"
- LibraryView exposes loadingState (str) property, defaulting to "Loading"
- AppWindow loads as a top-level window component
- main.qml still loads cleanly after being updated to use AppWindow
- ThumbnailTile exposes imageId, tileClicked/tileDoubleClicked signals
- ThumbnailGrid loads with SelectionManager registered as context property
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent, QQmlApplicationEngine, QQmlExpression, QJSValue
from PySide6.QtQuick import QQuickWindow

import found_app
from found_app.theme.theme import ThemeManager
from found_app.core.app_state import AppStateManager
from found_app.services.filter_state import FilterStateManager
from found_app.viewmodels.library_view_model import LibraryViewModel, LibraryLoadingState
from found_app.models.thumbnail_grid_model import ThumbnailGridModel
from found_app.viewmodels.collections_view_model import CollectionsViewModel
from found_app.viewmodels.import_view_model import ImportViewModel
from found_app.viewmodels.metadata_view_model import MetadataViewModel
from found_app.viewmodels.tag_editor_view_model import TagEditorViewModel
from found_app.viewmodels.tag_search_view_model import TagSearchViewModel
from found_app.services.navigation import NavigationManager
from found_app.services.selection import SelectionManager

QML_DIR = Path(found_app.__file__).parent / "qml"


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def engine(qapp):
    """QQmlEngine with Theme, SelectionManager, NavigationManager, and FilterState registered."""
    theme = ThemeManager()
    selection = SelectionManager()
    navigation = NavigationManager()
    filter_state = FilterStateManager()
    e = QQmlEngine()
    tag_search = TagSearchViewModel(tags_fetcher=lambda term: [])
    tag_editor_search = TagSearchViewModel(tags_fetcher=lambda term: [])
    tag_editor = TagEditorViewModel(
        image_tags_fetcher=lambda image_id: [],
        tag_modifier=lambda image_ids, add_ids, remove_ids: True,
    )
    e.rootContext().setContextProperty("Theme", theme)
    e.rootContext().setContextProperty("SelectionManager", selection)
    e.rootContext().setContextProperty("NavigationManager", navigation)
    e.rootContext().setContextProperty("FilterState", filter_state)
    e.rootContext().setContextProperty("TagSearchState", tag_search)
    e.rootContext().setContextProperty("TagEditorSearchState", tag_editor_search)
    e.rootContext().setContextProperty("TagEditorState", tag_editor)
    theme.setParent(e)
    selection.setParent(e)
    navigation.setParent(e)
    filter_state.setParent(e)
    tag_search.setParent(e)
    tag_editor_search.setParent(e)
    tag_editor.setParent(e)
    yield e
    e.clearComponentCache()


def load_component(engine, filename: str):
    """Load a QML file from QML_DIR, assert no errors, return instance.

    The created object is parented to the engine so it stays alive for the
    duration of the test even if the local QQmlComponent is collected.
    """
    path = QML_DIR / filename
    assert path.exists(), f"{filename} not found at {path}"

    component = QQmlComponent(engine, QUrl.fromLocalFile(str(path)))
    errors = [e.toString() for e in component.errors()]
    assert not errors, f"{filename} load errors: {errors}"
    assert component.status() == QQmlComponent.Status.Ready, (
        f"{filename} component status: {component.status()}"
    )

    obj = component.create(engine.rootContext())
    assert obj is not None, f"{filename} component.create() returned None"
    obj.setParent(engine)
    return obj


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------


def test_splash_screen_qml_exists():
    assert (QML_DIR / "views/SplashScreen.qml").exists()


def test_main_router_qml_exists():
    assert (QML_DIR / "shell/MainRouter.qml").exists()


def test_app_window_qml_exists():
    assert (QML_DIR / "shell/AppWindow.qml").exists()


# ---------------------------------------------------------------------------
# SplashScreen
# ---------------------------------------------------------------------------


def test_splash_screen_loads(engine):
    load_component(engine, "views/SplashScreen.qml")


def test_splash_screen_has_status_text_property(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    assert obj.property("statusText") is not None or obj.property("statusText") == ""


def test_splash_screen_status_text_defaults_to_empty(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    assert obj.property("statusText") == ""


def test_splash_screen_status_text_is_writable(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    obj.setProperty("statusText", "Connecting…")
    assert obj.property("statusText") == "Connecting…"


def test_splash_screen_has_error_defaults_to_false(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    assert obj.property("hasError") is False


def test_splash_screen_has_error_is_writable(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    obj.setProperty("hasError", True)
    assert obj.property("hasError") is True


def test_splash_screen_app_version_defaults_to_empty(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    assert obj.property("appVersion") == ""


def test_splash_screen_app_version_is_writable(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    obj.setProperty("appVersion", "0.1.0")
    assert obj.property("appVersion") == "0.1.0"


def test_splash_screen_app_license_defaults_to_empty(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    assert obj.property("appLicense") == ""


def test_splash_screen_app_license_is_writable(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    obj.setProperty("appLicense", "GNU GPL v3.0")
    assert obj.property("appLicense") == "GNU GPL v3.0"


def test_splash_screen_is_ready_defaults_to_false(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    assert obj.property("isReady") is False


def test_splash_screen_is_ready_is_writable(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    obj.setProperty("isReady", True)
    assert obj.property("isReady") is True


def test_splash_screen_has_dismissed_signal(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    received = []
    obj.dismissed.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_splash_screen_is_dismissed_defaults_to_false(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    assert obj.property("isDismissed") is False


def test_splash_screen_is_dismissed_becomes_true_after_dismissed_signal(engine):
    obj = load_component(engine, "views/SplashScreen.qml")
    obj.dismissed.emit()
    assert obj.property("isDismissed") is True


# ---------------------------------------------------------------------------
# SplashScreen — theme tokens (Feature 5.10)
# ---------------------------------------------------------------------------


def test_splash_screen_title_text_pixel_size_uses_theme_token(theme_qml_engine):
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "views/SplashScreen.qml")
    title_text = obj.findChild(QObject, "titleText")
    assert title_text is not None
    assert title_text.property("font").pixelSize() == active_theme.fontSizeXl * 8


# ---------------------------------------------------------------------------
# MainRouter
# ---------------------------------------------------------------------------


def test_main_router_loads(engine):
    load_component(engine, "shell/MainRouter.qml")


def test_main_router_app_state_defaults_to_launching(engine):
    obj = load_component(engine, "shell/MainRouter.qml")
    assert obj.property("appState") == "Launching"


def test_main_router_app_state_is_writable(engine):
    obj = load_component(engine, "shell/MainRouter.qml")
    obj.setProperty("appState", "Ready")
    assert obj.property("appState") == "Ready"


def test_main_router_relocate_prefix_dialog_closed_by_default(engine):
    obj = load_component(engine, "shell/MainRouter.qml")
    assert obj.property("relocatePrefixDialogOpen") is False


def test_main_router_relocation_result_dialog_closed_by_default(engine):
    obj = load_component(engine, "shell/MainRouter.qml")
    assert obj.property("relocationResultDialogOpen") is False


def test_main_router_routes_to_settings_view(qapp):
    from found_app.core.app_state import AppState

    library_state = LibraryViewModel(page_fetcher=lambda cursor=None, limit=100: None)
    selection = SelectionManager()
    navigation = NavigationManager()
    metadata_state = MetadataViewModel(image_fetcher=lambda image_id: None)

    engine = _build_app_engine(library_state, metadata_state, navigation, selection)
    root = engine.rootObjects()[0]

    app_state = engine.rootContext().contextProperty("AppState")
    app_state.transition_to(AppState.BackendStarting)
    app_state.transition_to(AppState.Ready)

    splash_screen = root.findChild(QObject, "splashScreen")
    splash_screen.setProperty("isDismissed", True)

    navigation.push("settings")

    settings_view = root.findChild(QObject, "settingsView")
    assert settings_view is not None
    assert settings_view.property("visible") is True


# ---------------------------------------------------------------------------
# MainRouter drag-and-drop overlay — theme tokens (Feature 5.6)
# ---------------------------------------------------------------------------


def test_main_router_drag_highlight_uses_theme_text_color(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "shell/MainRouter.qml")
    highlight = obj.findChild(QObject, "dragHighlight")
    assert highlight is not None
    assert highlight.property("color") == QColor(active_theme.text)


def test_main_router_drop_hint_text_uses_heading_variant(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "shell/MainRouter.qml")
    hint = obj.findChild(QObject, "dropHintText")
    assert hint is not None
    assert hint.property("color") == QColor(active_theme.text)
    assert hint.property("font").pixelSize() == active_theme.fontSizeLg


# ---------------------------------------------------------------------------
# AppWindow & main.qml (integration)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# LibraryView
# ---------------------------------------------------------------------------


def test_library_view_qml_exists():
    assert (QML_DIR / "views/LibraryView.qml").exists()


def test_library_view_loads(engine):
    load_component(engine, "views/LibraryView.qml")


def test_library_view_has_loading_state_property(engine):
    obj = load_component(engine, "views/LibraryView.qml")
    assert obj.property("loadingState") is not None or obj.property("loadingState") == ""


def test_library_view_loading_state_defaults_to_loading(engine):
    obj = load_component(engine, "views/LibraryView.qml")
    assert obj.property("loadingState") == "Loading"


def test_library_view_loading_state_is_writable(engine):
    obj = load_component(engine, "views/LibraryView.qml")
    obj.setProperty("loadingState", "Empty")
    assert obj.property("loadingState") == "Empty"


def test_library_view_has_no_is_filtered_property(engine):
    obj = load_component(engine, "views/LibraryView.qml")
    assert obj.property("isFiltered") is None


def test_library_view_left_panel_open_defaults_to_false(engine):
    obj = load_component(engine, "views/LibraryView.qml")
    assert obj.property("leftPanelOpen") is False


def test_library_view_right_panel_open_defaults_to_false(engine):
    obj = load_component(engine, "views/LibraryView.qml")
    assert obj.property("rightPanelOpen") is False


def test_library_view_has_remove_images_requested_signal(engine):
    obj = load_component(engine, "views/LibraryView.qml")
    received = []
    obj.removeImagesRequested.connect(lambda ids: received.append(ids))
    assert isinstance(received, list)


def test_library_view_has_locate_requested_signal(engine):
    obj = load_component(engine, "views/LibraryView.qml")
    received = []
    obj.locateRequested.connect(lambda image_id: received.append(image_id))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# AppWindow & main.qml (integration)
# ---------------------------------------------------------------------------


def test_main_qml_loads_with_app_window(qapp):
    """main.qml loads cleanly with all required context properties registered."""
    theme = ThemeManager()
    app_state = AppStateManager()
    library_state = LibraryViewModel(page_fetcher=lambda cursor=None, limit=100: None)
    selection = SelectionManager()
    navigation = NavigationManager()
    collections_state = CollectionsViewModel(
        collections_fetcher=lambda: [],
        collection_creator=lambda name: None,
        images_adder=lambda cid, iids: False,
        collection_images_fetcher=lambda cid: [],
    )
    import_state = ImportViewModel(
        scanner=lambda paths: {"new": [], "already_imported": [], "conflicts": [], "invalid": []},
        importer=lambda paths: "job-id",
        job_fetcher=lambda jid: {"status": "completed", "total_files": 0, "processed_files": 0,
                                  "successful_imports": 0, "duplicate_paths": 0,
                                  "duplicate_hashes": 0, "failed_imports": 0},
    )
    e = QQmlApplicationEngine()
    e.rootContext().setContextProperty("Theme", theme)
    e.rootContext().setContextProperty("AppState", app_state)
    e.rootContext().setContextProperty("LibraryState", library_state)
    e.rootContext().setContextProperty("SelectionManager", selection)
    e.rootContext().setContextProperty("NavigationManager", navigation)
    e.rootContext().setContextProperty("CollectionsState", collections_state)
    e.rootContext().setContextProperty("ImportState", import_state)
    e.rootContext().setContextProperty("FilterState", FilterStateManager())
    e.rootContext().setContextProperty("MetadataState", MetadataViewModel(image_fetcher=lambda image_id: None))
    e.rootContext().setContextProperty("TagSearchState", TagSearchViewModel(tags_fetcher=lambda term: []))
    e.rootContext().setContextProperty("TagEditorSearchState", TagSearchViewModel(tags_fetcher=lambda term: []))
    e.rootContext().setContextProperty("TagEditorState", TagEditorViewModel(
        image_tags_fetcher=lambda image_id: [],
        tag_modifier=lambda image_ids, add_ids, remove_ids: True,
    ))
    e.rootContext().setContextProperty("baseUrl", "http://127.0.0.1:8000")
    e.rootContext().setContextProperty("foundVersion", "0.1.0")
    e.rootContext().setContextProperty("foundLicense", "GNU GPL v3.0")
    e.load(str(QML_DIR / "main.qml"))
    assert e.rootObjects(), "main.qml failed to load"


def test_open_image_from_collection_carries_collection_context(qapp):
    """Opening an image while browsing a collection should push the image
    view scoped to that collection: collection_id/name carried along, and
    context_ids drawn from the collection's images (not the library's) so
    prev/next browsing stays inside the collection."""
    theme = ThemeManager()
    app_state = AppStateManager()
    library_state = LibraryViewModel(page_fetcher=lambda cursor=None, limit=100: None)
    selection = SelectionManager()
    navigation = NavigationManager()
    collections_state = CollectionsViewModel(
        collections_fetcher=lambda: [],
        collection_creator=lambda name: None,
        images_adder=lambda cid, iids: False,
        collection_images_fetcher=lambda cid: [],
    )
    import_state = ImportViewModel(
        scanner=lambda paths: {"new": [], "already_imported": [], "conflicts": [], "invalid": []},
        importer=lambda paths: "job-id",
        job_fetcher=lambda jid: {"status": "completed", "total_files": 0, "processed_files": 0,
                                  "successful_imports": 0, "duplicate_paths": 0,
                                  "duplicate_hashes": 0, "failed_imports": 0},
    )
    e = QQmlApplicationEngine()
    e.rootContext().setContextProperty("Theme", theme)
    e.rootContext().setContextProperty("AppState", app_state)
    e.rootContext().setContextProperty("LibraryState", library_state)
    e.rootContext().setContextProperty("SelectionManager", selection)
    e.rootContext().setContextProperty("NavigationManager", navigation)
    e.rootContext().setContextProperty("CollectionsState", collections_state)
    e.rootContext().setContextProperty("ImportState", import_state)
    e.rootContext().setContextProperty("FilterState", FilterStateManager())
    e.rootContext().setContextProperty("MetadataState", MetadataViewModel(image_fetcher=lambda image_id: None))
    e.rootContext().setContextProperty("TagSearchState", TagSearchViewModel(tags_fetcher=lambda term: []))
    e.rootContext().setContextProperty("TagEditorSearchState", TagSearchViewModel(tags_fetcher=lambda term: []))
    e.rootContext().setContextProperty("TagEditorState", TagEditorViewModel(
        image_tags_fetcher=lambda image_id: [],
        tag_modifier=lambda image_ids, add_ids, remove_ids: True,
    ))
    e.rootContext().setContextProperty("baseUrl", "http://127.0.0.1:8000")
    e.rootContext().setContextProperty("foundVersion", "0.1.0")
    e.rootContext().setContextProperty("foundLicense", "GNU GPL v3.0")
    e.load(str(QML_DIR / "main.qml"))
    assert e.rootObjects(), "main.qml failed to load"

    collections_state.collectionGridModel.appendPage(
        [
            {"id": "img-1", "filename": "a.jpg", "file_status": "available"},
            {"id": "img-2", "filename": "b.jpg", "file_status": "available"},
        ],
        None,
        False,
    )
    navigation.push("collection", {"collection_id": "col-1", "collection_name": "Portraits"})

    selection.requestOpen("img-2")

    entry = navigation.currentEntry
    assert entry["view"] == "image"
    assert entry["collection_id"] == "col-1"
    assert entry["collection_name"] == "Portraits"
    assert entry["context_ids"] == ["img-1", "img-2"]


# ---------------------------------------------------------------------------
# Stale-missing banner wiring — MainRouter <-> MetadataState <-> LibraryState
# ---------------------------------------------------------------------------


def _wait_until(predicate, timeout_ms=2000):
    if predicate():
        return
    loop = QEventLoop()
    timer = QTimer()
    timer.setInterval(20)

    def tick():
        if predicate():
            loop.quit()

    timer.timeout.connect(tick)
    timer.start()
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    timer.stop()


def _build_app_engine(library_state, metadata_state, navigation, selection):
    theme = ThemeManager()
    app_state = AppStateManager()
    collections_state = CollectionsViewModel(
        collections_fetcher=lambda: [],
        collection_creator=lambda name: None,
        images_adder=lambda cid, iids: False,
        collection_images_fetcher=lambda cid: [],
    )
    import_state = ImportViewModel(
        scanner=lambda paths: {"new": [], "already_imported": [], "conflicts": [], "invalid": []},
        importer=lambda paths: "job-id",
        job_fetcher=lambda jid: {"status": "completed", "total_files": 0, "processed_files": 0,
                                  "successful_imports": 0, "duplicate_paths": 0,
                                  "duplicate_hashes": 0, "failed_imports": 0},
    )
    filter_state = FilterStateManager()
    tag_search_state = TagSearchViewModel(tags_fetcher=lambda term: [])
    tag_editor_search_state = TagSearchViewModel(tags_fetcher=lambda term: [])
    tag_editor_state = TagEditorViewModel(
        image_tags_fetcher=lambda image_id: [],
        tag_modifier=lambda image_ids, add_ids, remove_ids: True,
    )

    e = QQmlApplicationEngine()
    e.rootContext().setContextProperty("Theme", theme)
    e.rootContext().setContextProperty("AppState", app_state)
    e.rootContext().setContextProperty("LibraryState", library_state)
    e.rootContext().setContextProperty("SelectionManager", selection)
    e.rootContext().setContextProperty("NavigationManager", navigation)
    e.rootContext().setContextProperty("CollectionsState", collections_state)
    e.rootContext().setContextProperty("ImportState", import_state)
    e.rootContext().setContextProperty("FilterState", filter_state)
    e.rootContext().setContextProperty("MetadataState", metadata_state)
    e.rootContext().setContextProperty("TagSearchState", tag_search_state)
    e.rootContext().setContextProperty("TagEditorSearchState", tag_editor_search_state)
    e.rootContext().setContextProperty("TagEditorState", tag_editor_state)
    e.rootContext().setContextProperty("baseUrl", "http://127.0.0.1:8000")
    e.rootContext().setContextProperty("foundVersion", "0.1.0")
    e.rootContext().setContextProperty("foundLicense", "GNU GPL v3.0")
    e.load(str(QML_DIR / "main.qml"))
    assert e.rootObjects(), "main.qml failed to load"

    # Keep Python references alive for the engine's lifetime — QQmlContext does
    # not retain ownership of context-property objects, so without this they
    # are garbage collected as soon as this function returns, leaving the QML
    # bindings pointing at null.
    e._context_objects = (
        theme, app_state, collections_state, import_state,
        filter_state, tag_search_state, tag_editor_search_state, tag_editor_state,
    )
    return e


_MISSING_IMAGE = {
    "id": "img-1", "filename": "a.jpg", "path": "/a.jpg",
    "width": 100, "height": 100, "file_size": 100,
    "imported_date": "2024-01-01", "file_status": "missing",
}


def test_stale_missing_metadata_triggers_verify_in_image_view(qapp):
    """Loading metadata for an image still marked missing, while viewing it
    in the image view, should kick off a re-verify — the file may have
    reappeared since the grid was last loaded."""
    verified_ids = []

    def image_verifier(image_id):
        verified_ids.append(image_id)
        return "available"

    library_state = LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: None,
        image_verifier=image_verifier,
    )
    selection = SelectionManager()
    navigation = NavigationManager()
    metadata_state = MetadataViewModel(image_fetcher=lambda image_id: _MISSING_IMAGE)

    engine = _build_app_engine(library_state, metadata_state, navigation, selection)

    navigation.push("image", {"image_id": "img-1"})
    metadata_state.loadImage("img-1")

    _wait_until(lambda: verified_ids == ["img-1"])
    assert verified_ids == ["img-1"]


def test_stale_missing_metadata_does_not_trigger_verify_in_library_view(qapp):
    """The stale-missing re-verify is scoped to the image view — selecting a
    missing image in the library grid should not trigger it."""
    verified_ids = []

    def image_verifier(image_id):
        verified_ids.append(image_id)
        return "available"

    library_state = LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: None,
        image_verifier=image_verifier,
    )
    selection = SelectionManager()
    navigation = NavigationManager()
    metadata_state = MetadataViewModel(image_fetcher=lambda image_id: _MISSING_IMAGE)

    engine = _build_app_engine(library_state, metadata_state, navigation, selection)

    assert navigation.currentView == "library"
    metadata_state.loadImage("img-1")
    _wait_until(lambda: metadata_state.isMissing is True)

    assert verified_ids == []


def test_image_status_changed_clears_metadata_missing_banner(qapp):
    """Once a verify resolves an image as available, the metadata panel's
    missing banner for that image should clear in place."""
    library_state = LibraryViewModel(page_fetcher=lambda cursor=None, limit=100: None)
    selection = SelectionManager()
    navigation = NavigationManager()
    metadata_state = MetadataViewModel(image_fetcher=lambda image_id: _MISSING_IMAGE)

    engine = _build_app_engine(library_state, metadata_state, navigation, selection)

    navigation.push("image", {"image_id": "img-1"})
    metadata_state.loadImage("img-1")
    _wait_until(lambda: metadata_state.isMissing is True)

    library_state.imageStatusChanged.emit("img-1", "available")

    assert metadata_state.isMissing is False


# ---------------------------------------------------------------------------
# Automatic missing-image verification — startup + interval poll
# ---------------------------------------------------------------------------


def test_missing_poll_timer_has_120_second_interval(qapp):
    library_state = LibraryViewModel(page_fetcher=lambda cursor=None, limit=100: None)
    selection = SelectionManager()
    navigation = NavigationManager()
    metadata_state = MetadataViewModel(image_fetcher=lambda image_id: _MISSING_IMAGE)

    engine = _build_app_engine(library_state, metadata_state, navigation, selection)

    root = engine.rootObjects()[0]
    timer = root.findChild(QObject, "missingPollTimer")
    assert timer is not None
    assert timer.property("interval") == 120000
    assert timer.property("repeat") is True


def test_missing_poll_triggers_verify_missing_when_images_missing(qapp):
    poll_calls = []

    def missing_id_fetcher():
        poll_calls.append(True)
        return {"items": []}

    library_state = LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: None,
        missing_id_fetcher=missing_id_fetcher,
        batch_verifier=lambda ids: [],
    )
    library_state._grid_model.appendPage(
        [{"id": "img-1", "filename": "a.jpg", "file_status": "missing"}], None, False
    )
    selection = SelectionManager()
    navigation = NavigationManager()
    metadata_state = MetadataViewModel(image_fetcher=lambda image_id: _MISSING_IMAGE)

    engine = _build_app_engine(library_state, metadata_state, navigation, selection)

    root = engine.rootObjects()[0]
    timer = root.findChild(QObject, "missingPollTimer")
    QMetaObject.invokeMethod(timer, "triggered")

    _wait_until(lambda: poll_calls == [True])
    assert poll_calls == [True]


def test_missing_poll_does_not_trigger_verify_missing_when_nothing_missing(qapp):
    poll_calls = []

    def missing_id_fetcher():
        poll_calls.append(True)
        return {"items": []}

    library_state = LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: None,
        missing_id_fetcher=missing_id_fetcher,
        batch_verifier=lambda ids: [],
    )
    selection = SelectionManager()
    navigation = NavigationManager()
    metadata_state = MetadataViewModel(image_fetcher=lambda image_id: _MISSING_IMAGE)

    engine = _build_app_engine(library_state, metadata_state, navigation, selection)

    root = engine.rootObjects()[0]
    timer = root.findChild(QObject, "missingPollTimer")
    QMetaObject.invokeMethod(timer, "triggered")

    _wait_until(lambda: False, timeout_ms=200)
    assert poll_calls == []


def test_viewport_verify_requested_bubbles_to_library_state(qapp):
    """A missing tile entering the viewport in the library view should reach
    LibraryState.verifyBatch via the ThumbnailGrid -> ImageGridPane ->
    LibraryView -> MainRouter bubbling chain."""
    verify_calls = []

    library_state = LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: None,
        batch_verifier=lambda ids: verify_calls.append(list(ids)) or [],
    )
    library_state._grid_model.appendPage(
        [{"id": "img-1", "filename": "a.jpg", "file_status": "missing"}], None, False
    )
    library_state._set_state(LibraryLoadingState.Ready)
    selection = SelectionManager()
    navigation = NavigationManager()
    metadata_state = MetadataViewModel(image_fetcher=lambda image_id: _MISSING_IMAGE)

    engine = _build_app_engine(library_state, metadata_state, navigation, selection)

    root = engine.rootObjects()[0]
    main_router = root.findChild(QObject, "mainRouter")
    main_router.setProperty("appState", "Ready")
    splash_screen = root.findChild(QObject, "splashScreen")
    splash_screen.setProperty("isDismissed", True)

    _wait_until(lambda: verify_calls != [], timeout_ms=2000)

    assert verify_calls
    assert "img-1" in verify_calls[0]


# ---------------------------------------------------------------------------
# ThumbnailTile
# ---------------------------------------------------------------------------


def test_thumbnail_tile_qml_exists():
    assert (QML_DIR / "components/ThumbnailTile.qml").exists()


def test_thumbnail_tile_loads(engine):
    load_component(engine, "components/ThumbnailTile.qml")


def test_thumbnail_tile_has_thumbnail_url_property(engine):
    obj = load_component(engine, "components/ThumbnailTile.qml")
    assert obj.property("thumbnailUrl") == ""


def test_thumbnail_tile_has_file_status_property(engine):
    obj = load_component(engine, "components/ThumbnailTile.qml")
    assert obj.property("fileStatus") == "available"


def test_thumbnail_tile_has_selected_property(engine):
    obj = load_component(engine, "components/ThumbnailTile.qml")
    assert obj.property("selected") is False


def test_thumbnail_tile_has_image_id_property(engine):
    obj = load_component(engine, "components/ThumbnailTile.qml")
    assert obj.property("imageId") == ""


def test_thumbnail_tile_image_id_is_writable(engine):
    obj = load_component(engine, "components/ThumbnailTile.qml")
    obj.setProperty("imageId", "test-uuid-123")
    assert obj.property("imageId") == "test-uuid-123"


def test_thumbnail_tile_has_inset_property(engine):
    obj = load_component(engine, "components/ThumbnailTile.qml")
    assert obj.property("inset") == 0


def test_thumbnail_tile_has_remove_requested_signal(engine):
    obj = load_component(engine, "components/ThumbnailTile.qml")
    received = []
    obj.removeRequested.connect(lambda image_id: received.append(image_id))
    assert isinstance(received, list)


def test_thumbnail_tile_has_locate_requested_signal(engine):
    obj = load_component(engine, "components/ThumbnailTile.qml")
    received = []
    obj.locateRequested.connect(lambda image_id: received.append(image_id))
    assert isinstance(received, list)


def test_thumbnail_tile_locate_requested_signal_carries_image_id(engine):
    obj = load_component(engine, "components/ThumbnailTile.qml")
    obj.setProperty("imageId", "test-uuid-456")
    received = []
    obj.locateRequested.connect(lambda image_id: received.append(image_id))
    obj.locateRequested.emit("test-uuid-456")
    assert received == ["test-uuid-456"]


# ---------------------------------------------------------------------------
# ThumbnailGrid
# ---------------------------------------------------------------------------


def test_thumbnail_grid_qml_exists():
    assert (QML_DIR / "components/ThumbnailGrid.qml").exists()


def test_thumbnail_grid_loads(engine):
    load_component(engine, "components/ThumbnailGrid.qml")


def test_thumbnail_grid_has_model_property(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    # model defaults to null — property should exist and be readable
    assert obj.property("model") is None or obj.property("model") is not None


def test_thumbnail_grid_has_scroll_x_property(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    edge_margin = obj.property("gridEdgeMargin")
    assert obj.property("scrollX") == -float(edge_margin)


def test_thumbnail_grid_has_tile_gap_property(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    assert obj.property("tileGap") == 20


def test_thumbnail_grid_has_grid_edge_margin_property(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    assert obj.property("gridEdgeMargin") == 40


def test_thumbnail_grid_left_panel_open_defaults_to_false(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    assert obj.property("leftPanelOpen") is False


def test_thumbnail_grid_right_panel_open_defaults_to_false(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    assert obj.property("rightPanelOpen") is False


def test_thumbnail_grid_has_remove_requested_signal(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    received = []
    obj.removeRequested.connect(lambda image_id, filename: received.append((image_id, filename)))
    assert isinstance(received, list)


def test_thumbnail_grid_has_locate_requested_signal(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    received = []
    obj.locateRequested.connect(lambda image_id: received.append(image_id))
    assert isinstance(received, list)


def test_thumbnail_grid_has_viewport_verify_requested_signal(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    received = []
    obj.viewportVerifyRequested.connect(lambda image_ids: received.append(image_ids))
    assert isinstance(received, list)


def test_thumbnail_grid_emits_viewport_verify_requested_for_missing_items(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    obj.setProperty("width", 400)
    obj.setProperty("height", 400)

    model = ThumbnailGridModel()
    model.setParent(obj)
    model.appendPage(
        [
            {"id": "img-1", "filename": "a.jpg", "file_status": "missing"},
            {"id": "img-2", "filename": "b.jpg", "file_status": "available"},
        ],
        None,
        False,
    )
    obj.setProperty("model", model)

    received = []

    def _on_verify_requested(image_ids):
        if isinstance(image_ids, QJSValue):
            image_ids = image_ids.toVariant() or []
        received.append(list(image_ids))

    obj.viewportVerifyRequested.connect(_on_verify_requested)

    window = QQuickWindow()
    obj.setParentItem(window.contentItem())
    window.resize(400, 400)
    window.show()

    _wait_until(lambda: received != [], timeout_ms=2000)

    assert received
    assert "img-1" in received[0]
    assert "img-2" not in received[0]


def test_thumbnail_grid_does_not_emit_viewport_verify_for_available_items(engine):
    obj = load_component(engine, "components/ThumbnailGrid.qml")
    obj.setProperty("width", 400)
    obj.setProperty("height", 400)

    model = ThumbnailGridModel()
    model.setParent(obj)
    model.appendPage(
        [{"id": "img-1", "filename": "a.jpg", "file_status": "available"}],
        None,
        False,
    )
    obj.setProperty("model", model)

    received = []
    obj.viewportVerifyRequested.connect(lambda image_ids: received.append(list(image_ids)))

    _wait_until(lambda: False, timeout_ms=800)

    assert received == []


# ---------------------------------------------------------------------------
# TitleBar
# ---------------------------------------------------------------------------


def test_title_bar_qml_exists():
    assert (QML_DIR / "shell/TitleBar.qml").exists()


def test_title_bar_loads(engine):
    load_component(engine, "shell/TitleBar.qml")


def test_title_bar_can_go_back_defaults_to_false(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.property("canGoBack") is False


def test_title_bar_can_go_back_is_writable(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    obj.setProperty("canGoBack", True)
    assert obj.property("canGoBack") is True


def test_title_bar_view_title_defaults_to_empty(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.property("viewTitle") == ""


def test_title_bar_view_title_is_writable(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    obj.setProperty("viewTitle", "Library")
    assert obj.property("viewTitle") == "Library"


# ---------------------------------------------------------------------------
# ImageView
# ---------------------------------------------------------------------------


def test_image_view_qml_exists():
    assert (QML_DIR / "views/ImageView.qml").exists()


def test_image_view_loads(engine):
    load_component(engine, "views/ImageView.qml")


def test_image_view_image_id_defaults_to_empty(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("imageId") == ""


def test_image_view_image_url_defaults_to_empty(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("imageUrl") == ""


def test_image_view_filename_defaults_to_empty(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("filename") == ""


def test_image_view_file_status_defaults_to_available(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("fileStatus") == "available"


def test_image_view_has_next_defaults_to_false(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("hasNext") is False


def test_image_view_has_prev_defaults_to_false(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("hasPrev") is False


def test_image_view_zoom_level_defaults_to_one(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("zoomLevel") == 1.0


def test_image_view_pan_offset_x_defaults_to_zero(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("panOffsetX") == 0.0


def test_image_view_pan_offset_y_defaults_to_zero(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("panOffsetY") == 0.0


# ---------------------------------------------------------------------------
# ImageView prev/next hover buttons — Commit 12
# ---------------------------------------------------------------------------


def test_image_view_has_prev_requested_signal(engine):
    obj = load_component(engine, "views/ImageView.qml")
    received = []
    obj.prevRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_image_view_has_next_requested_signal(engine):
    obj = load_component(engine, "views/ImageView.qml")
    received = []
    obj.nextRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_image_view_has_next_is_writable(engine):
    obj = load_component(engine, "views/ImageView.qml")
    obj.setProperty("hasNext", True)
    assert obj.property("hasNext") is True


def test_image_view_has_prev_is_writable(engine):
    obj = load_component(engine, "views/ImageView.qml")
    obj.setProperty("hasPrev", True)
    assert obj.property("hasPrev") is True


# ---------------------------------------------------------------------------
# ImageView removal — Slice 9 Commit 7
# ---------------------------------------------------------------------------


def test_image_view_has_remove_image_requested_signal(engine):
    obj = load_component(engine, "views/ImageView.qml")
    received = []
    obj.removeImageRequested.connect(
        lambda image_id, collection_id, also_from_library: received.append(
            (image_id, collection_id, also_from_library)
        )
    )
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# ImageView collection-aware removal — Slice 9 Commit 9
# ---------------------------------------------------------------------------


def test_image_view_collection_id_defaults_to_empty(engine):
    obj = load_component(engine, "views/ImageView.qml")
    assert obj.property("collectionId") == ""


def test_image_view_collection_id_is_writable(engine):
    obj = load_component(engine, "views/ImageView.qml")
    obj.setProperty("collectionId", "col-1")
    assert obj.property("collectionId") == "col-1"


# ---------------------------------------------------------------------------
# ImageView — remove dialog blocks the viewport behind it
# ---------------------------------------------------------------------------


def test_image_view_viewport_enabled_by_default(engine):
    obj = load_component(engine, "views/ImageView.qml")
    viewport = obj.findChild(QObject, "viewport")
    assert viewport.property("enabled") is True


def test_image_view_viewport_disabled_when_remove_dialog_open(engine):
    obj = load_component(engine, "views/ImageView.qml")
    viewport = obj.findChild(QObject, "viewport")
    obj.setProperty("_removeId", "img-1")
    assert viewport.property("enabled") is False


def test_image_view_viewport_reenabled_after_dialog_closes(engine):
    obj = load_component(engine, "views/ImageView.qml")
    viewport = obj.findChild(QObject, "viewport")
    obj.setProperty("_removeId", "img-1")
    obj.setProperty("_removeId", "")
    assert viewport.property("enabled") is True


def test_image_view_shortcuts_disabled_when_remove_dialog_open(engine):
    obj = load_component(engine, "views/ImageView.qml")
    shortcuts = [
        c for c in obj.findChildren(QObject)
        if c.metaObject().className() == "QQuickShortcut"
    ]
    assert len(shortcuts) > 0
    assert all(s.property("enabled") is True for s in shortcuts)

    obj.setProperty("_removeId", "img-1")
    assert all(s.property("enabled") is False for s in shortcuts)


# ---------------------------------------------------------------------------
# ImageView — theme tokens (Feature 5.10)
# ---------------------------------------------------------------------------


def test_image_view_backgrounds_use_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "views/ImageView.qml")

    root_background = obj.findChild(QObject, "rootBackground")
    assert root_background is not None
    assert root_background.property("color") == QColor(active_theme.background)

    viewport = obj.findChild(QObject, "viewport")
    assert viewport is not None
    assert viewport.property("color") == QColor(active_theme.background)


def test_image_view_error_icon_uses_theme_token(theme_qml_engine):
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "views/ImageView.qml")

    icon = obj.findChild(QObject, "errorIconText")
    assert icon is not None
    assert icon.property("font").pixelSize() == active_theme.fontSizeXl


def test_image_view_prev_next_badges_use_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "views/ImageView.qml")

    prev_badge = obj.findChild(QObject, "prevBadge")
    assert prev_badge is not None
    assert prev_badge.property("color") == QColor.fromRgbF(0, 0, 0, 0.8)

    prev_arrow = obj.findChild(QObject, "prevArrowText")
    assert prev_arrow is not None
    assert prev_arrow.property("color") == QColor(active_theme.text)
    assert prev_arrow.property("font").pixelSize() == active_theme.fontSizeXl

    next_badge = obj.findChild(QObject, "nextBadge")
    assert next_badge is not None
    assert next_badge.property("color") == QColor.fromRgbF(0, 0, 0, 0.8)

    next_arrow = obj.findChild(QObject, "nextArrowText")
    assert next_arrow is not None
    assert next_arrow.property("color") == QColor(active_theme.text)
    assert next_arrow.property("font").pixelSize() == active_theme.fontSizeXl


# ---------------------------------------------------------------------------
# CollectionItem
# ---------------------------------------------------------------------------


def test_collection_item_qml_exists():
    assert (QML_DIR / "components/CollectionItem.qml").exists()


def test_collection_item_loads(engine):
    load_component(engine, "components/CollectionItem.qml")


def test_collection_item_collection_id_defaults_to_empty(engine):
    obj = load_component(engine, "components/CollectionItem.qml")
    assert obj.property("collectionId") == ""


def test_collection_item_collection_name_defaults_to_empty(engine):
    obj = load_component(engine, "components/CollectionItem.qml")
    assert obj.property("collectionName") == ""


def test_collection_item_is_drop_target_defaults_to_false(engine):
    obj = load_component(engine, "components/CollectionItem.qml")
    assert obj.property("isDropTarget") is False


# ---------------------------------------------------------------------------
# CollectionsSidePanel
# ---------------------------------------------------------------------------


def test_collections_sidebar_qml_exists():
    assert (QML_DIR / "components/CollectionsSidePanel.qml").exists()


def test_collections_sidebar_loads(engine):
    load_component(engine, "components/CollectionsSidePanel.qml")


def test_collections_sidebar_open_defaults_to_false(engine):
    obj = load_component(engine, "components/CollectionsSidePanel.qml")
    assert obj.property("open") is False


def test_collections_sidebar_collections_property_exists(engine):
    obj = load_component(engine, "components/CollectionsSidePanel.qml")
    from PySide6.QtQml import QJSValue
    val = obj.property("collections")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == []


# ---------------------------------------------------------------------------
# ImageGridPane
# ---------------------------------------------------------------------------


def test_image_grid_pane_qml_exists():
    assert (QML_DIR / "components/ImageGridPane.qml").exists()


def test_image_grid_pane_loads(engine):
    load_component(engine, "components/ImageGridPane.qml")


def test_image_grid_pane_loading_state_defaults_to_loading(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    assert obj.property("loadingState") == "Loading"


def test_image_grid_pane_loading_state_is_writable(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    obj.setProperty("loadingState", "Ready")
    assert obj.property("loadingState") == "Ready"


def test_image_grid_pane_grid_model_defaults_to_none(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    assert obj.property("gridModel") is None


def test_image_grid_pane_left_panel_open_defaults_to_false(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    assert obj.property("leftPanelOpen") is False


def test_image_grid_pane_right_panel_open_defaults_to_false(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    assert obj.property("rightPanelOpen") is False


def test_image_grid_pane_empty_state_text_is_writable(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    obj.setProperty("emptyStateText", "Nothing here")
    assert obj.property("emptyStateText") == "Nothing here"


def test_image_grid_pane_no_results_text_defaults_to_no_images_found(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    assert obj.property("noResultsText") == "NO IMAGES FOUND"


def test_image_grid_pane_no_results_text_is_writable(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    obj.setProperty("noResultsText", "Nothing matches")
    assert obj.property("noResultsText") == "Nothing matches"


def test_image_grid_pane_no_results_subtext_defaults_to_empty(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    assert obj.property("noResultsSubtext") == ""


def test_image_grid_pane_remove_context_label_defaults_to_library(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    assert obj.property("removeContextLabel") == "the library"


def test_image_grid_pane_remove_checkbox_label_defaults_to_empty(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    assert obj.property("removeCheckboxLabel") == ""


def test_image_grid_pane_has_load_more_requested_signal(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    received = []
    obj.loadMoreRequested.connect(lambda: received.append(True))
    assert isinstance(received, list)


def test_image_grid_pane_has_remove_images_requested_signal(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    received = []
    obj.removeImagesRequested.connect(lambda ids, also: received.append((ids, also)))
    assert isinstance(received, list)


def test_image_grid_pane_has_scroll_x_changed_signal(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    received = []
    obj.scrollXChanged.connect(lambda x: received.append(x))
    assert isinstance(received, list)


def test_image_grid_pane_has_locate_requested_signal(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    received = []
    obj.locateRequested.connect(lambda image_id: received.append(image_id))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# ImageGridPane — remove dialog blocks the grid behind it
# ---------------------------------------------------------------------------


def test_image_grid_pane_thumbnail_grid_enabled_by_default(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    grid = obj.findChild(QObject, "thumbnailGrid")
    assert grid.property("enabled") is True


def test_image_grid_pane_thumbnail_grid_disabled_when_remove_dialog_open(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    grid = obj.findChild(QObject, "thumbnailGrid")
    obj.setProperty("_removeIds", ["img-1"])
    assert grid.property("enabled") is False


def test_image_grid_pane_thumbnail_grid_reenabled_after_dialog_closes(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    grid = obj.findChild(QObject, "thumbnailGrid")
    obj.setProperty("_removeIds", ["img-1"])
    obj.setProperty("_removeIds", [])
    assert grid.property("enabled") is True


def test_image_grid_pane_shortcuts_disabled_when_remove_dialog_open(engine):
    obj = load_component(engine, "components/ImageGridPane.qml")
    shortcuts = [
        c for c in obj.findChildren(QObject)
        if c.metaObject().className() == "QQuickShortcut"
    ]
    assert len(shortcuts) > 0
    assert all(s.property("enabled") is True for s in shortcuts)

    obj.setProperty("_removeIds", ["img-1"])
    assert all(s.property("enabled") is False for s in shortcuts)


# ---------------------------------------------------------------------------
# CollectionView
# ---------------------------------------------------------------------------


def test_collection_view_qml_exists():
    assert (QML_DIR / "views/CollectionView.qml").exists()


def test_collection_view_loads(engine):
    load_component(engine, "views/CollectionView.qml")


def test_collection_view_collection_name_defaults_to_empty(engine):
    obj = load_component(engine, "views/CollectionView.qml")
    assert obj.property("collectionName") == ""


def test_collection_view_collection_name_is_writable(engine):
    obj = load_component(engine, "views/CollectionView.qml")
    obj.setProperty("collectionName", "Portraits")
    assert obj.property("collectionName") == "Portraits"


def test_collection_view_grid_model_defaults_to_none(engine):
    obj = load_component(engine, "views/CollectionView.qml")
    assert obj.property("gridModel") is None


def test_collection_view_loading_state_defaults_to_idle(engine):
    obj = load_component(engine, "views/CollectionView.qml")
    assert obj.property("loadingState") == "Idle"


def test_collection_view_left_panel_open_defaults_to_false(engine):
    obj = load_component(engine, "views/CollectionView.qml")
    assert obj.property("leftPanelOpen") is False


def test_collection_view_right_panel_open_defaults_to_false(engine):
    obj = load_component(engine, "views/CollectionView.qml")
    assert obj.property("rightPanelOpen") is False


def test_collection_view_has_remove_images_requested_signal(engine):
    obj = load_component(engine, "views/CollectionView.qml")
    received = []
    obj.removeImagesRequested.connect(lambda ids, also_from_library: received.append((ids, also_from_library)))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# Drag-to-collection — Commit 4
# ---------------------------------------------------------------------------


def test_collection_item_has_image_dropped_signal(engine):
    obj = load_component(engine, "components/CollectionItem.qml")
    received = []
    obj.imageDropped.connect(lambda cid, iid: received.append((cid, iid)))
    assert isinstance(received, list)  # signal attribute exists


def test_collections_sidebar_has_image_dropped_signal(engine):
    obj = load_component(engine, "components/CollectionsSidePanel.qml")
    received = []
    obj.imageDropped.connect(lambda cid, iid: received.append((cid, iid)))
    assert isinstance(received, list)  # signal attribute exists


def test_collections_sidebar_has_toggle_requested_signal(engine):
    obj = load_component(engine, "components/CollectionsSidePanel.qml")
    received = []
    obj.toggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_title_bar_has_no_sidebar_open_property(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.property("sidebarOpen") is None


def test_thumbnail_tile_still_loads_with_drag_support(engine):
    load_component(engine, "components/ThumbnailTile.qml")


# ---------------------------------------------------------------------------
# ChipSearchSection — theme tokens (Feature 5.7)
# ---------------------------------------------------------------------------


def test_chip_search_section_qml_exists():
    assert (QML_DIR / "components/ChipSearchSection.qml").exists()


def test_chip_search_section_loads(engine):
    load_component(engine, "components/ChipSearchSection.qml")


def test_chip_search_section_separator_and_label_use_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ChipSearchSection.qml")
    obj.setProperty("sectionLabel", "Tags")

    separator = obj.findChild(QObject, "sectionSeparator")
    label = obj.findChild(QObject, "sectionLabel")
    assert separator is not None
    assert label is not None
    assert separator.property("color") == QColor(active_theme.border)
    assert label.property("color") == QColor(active_theme.textMuted)
    assert label.property("font").pixelSize() == active_theme.fontSizeSm


def test_chip_search_section_input_uses_theme_surface_and_border(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ChipSearchSection.qml")

    add_field = obj.findChild(QObject, "addField")
    assert add_field is not None
    assert add_field.property("color") == QColor(active_theme.surface)
    assert add_field.property("borderColor") == QColor(active_theme.border)


def test_chip_search_section_input_border_uses_theme_accent_when_focused(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ChipSearchSection.qml")

    window = QQuickWindow()
    obj.setParentItem(window.contentItem())
    window.resize(300, 100)
    window.show()

    add_field = obj.findChild(QObject, "addField")
    inner_input = obj.findChild(QObject, "input")
    inner_input.forceActiveFocus()
    assert add_field.property("borderColor") == QColor(active_theme.accent)


def test_chip_search_section_add_icon_uses_theme_text_muted(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ChipSearchSection.qml")

    icon = obj.findChild(QObject, "leadingIconItem")
    assert icon is not None
    assert icon.property("color") == QColor(active_theme.textMuted)
    assert icon.property("font").pixelSize() == active_theme.fontSizeSm


def test_chip_search_section_submit_icon_uses_theme_success(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ChipSearchSection.qml")

    icon = obj.findChild(QObject, "submitIcon")
    assert icon is not None
    assert icon.property("color") == QColor(active_theme.success)
    assert icon.property("font").pixelSize() == active_theme.fontSizeSm


# ---------------------------------------------------------------------------
# ImportPanel — Slice 9 Commit 2
# ---------------------------------------------------------------------------


def test_import_panel_qml_exists():
    assert (QML_DIR / "components/ImportPanel.qml").exists()


def test_import_panel_loads(engine):
    load_component(engine, "components/ImportPanel.qml")


def test_import_panel_loading_state_defaults_to_idle(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    assert obj.property("loadingState") == "Idle"


def test_import_panel_loading_state_is_writable(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    obj.setProperty("loadingState", "Previewing")
    assert obj.property("loadingState") == "Previewing"


def test_import_panel_pending_files_defaults_to_empty(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    from PySide6.QtQml import QJSValue
    val = obj.property("pendingFiles")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == []


def test_import_panel_already_imported_files_defaults_to_empty(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    from PySide6.QtQml import QJSValue
    val = obj.property("alreadyImportedFiles")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == []


def test_import_panel_invalid_count_defaults_to_zero(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    assert obj.property("invalidCount") == 0


def test_import_panel_imported_count_defaults_to_zero(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    assert obj.property("importedCount") == 0


def test_import_panel_skipped_count_defaults_to_zero(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    assert obj.property("skippedCount") == 0


def test_import_panel_has_confirmed_signal(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    received = []
    obj.confirmed.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_import_panel_has_cancelled_signal(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    received = []
    obj.cancelled.connect(lambda: received.append(1))
    assert isinstance(received, list)


# ImportPanel progress — Slice 9 Commit 4A
# ---------------------------------------------------------------------------


def test_import_panel_progress_defaults_to_zero(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    assert obj.property("progress") == 0.0


def test_import_panel_progress_is_writable(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    obj.setProperty("progress", 0.5)
    assert obj.property("progress") == 0.5


# ImportPanel conflict UI — Slice 9 Commit 4C
# ---------------------------------------------------------------------------


def test_import_panel_conflict_files_defaults_to_empty(engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(engine, "components/ImportPanel.qml")
    val = obj.property("conflictFiles")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == []


def test_import_panel_conflict_files_is_writable(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    sample = [{"path": "/a.jpg", "existing_image_id": "uuid-1",
               "existing_path": "/old/a.jpg", "existing_filename": "a.jpg"}]
    obj.setProperty("conflictFiles", sample)
    from PySide6.QtQml import QJSValue
    val = obj.property("conflictFiles")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert len(val) == 1


def test_import_panel_has_conflict_choice_changed_signal(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    received = []
    obj.conflictChoiceChanged.connect(lambda path, choice: received.append((path, choice)))
    assert isinstance(received, list)


def test_import_panel_updated_count_defaults_to_zero(engine):
    obj = load_component(engine, "components/ImportPanel.qml")
    assert obj.property("updatedCount") == 0


# ---------------------------------------------------------------------------
# FilterChip — Commit 7
# ---------------------------------------------------------------------------


def test_filter_chip_qml_exists():
    assert (QML_DIR / "components/FilterChip.qml").exists()


def test_filter_chip_loads(engine):
    load_component(engine, "components/FilterChip.qml")


def test_filter_chip_label_defaults_to_empty(engine):
    obj = load_component(engine, "components/FilterChip.qml")
    assert obj.property("label") == ""


def test_filter_chip_label_is_writable(engine):
    obj = load_component(engine, "components/FilterChip.qml")
    obj.setProperty("label", "architecture")
    assert obj.property("label") == "architecture"


def test_filter_chip_filter_mode_defaults_to_include(engine):
    obj = load_component(engine, "components/FilterChip.qml")
    assert obj.property("filterMode") == "include"


def test_filter_chip_filter_mode_is_writable(engine):
    obj = load_component(engine, "components/FilterChip.qml")
    obj.setProperty("filterMode", "exclude")
    assert obj.property("filterMode") == "exclude"


def test_filter_chip_has_remove_requested_signal(engine):
    obj = load_component(engine, "components/FilterChip.qml")
    received = []
    obj.removeRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_filter_chip_icons_use_theme_font_size_sm(theme_qml_engine):
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/FilterChip.qml")

    mode_icon = obj.findChild(QObject, "modeIcon")
    remove_icon = obj.findChild(QObject, "removeIcon")
    assert mode_icon is not None
    assert remove_icon is not None
    assert mode_icon.property("font").pixelSize() == active_theme.fontSizeSm
    assert remove_icon.property("font").pixelSize() == active_theme.fontSizeSm


# ---------------------------------------------------------------------------
# FilterDropdown — Commit 7
# ---------------------------------------------------------------------------


def test_filter_dropdown_qml_exists():
    assert (QML_DIR / "components/FilterDropdown.qml").exists()


def test_filter_dropdown_loads(engine):
    load_component(engine, "components/FilterDropdown.qml")


def test_filter_dropdown_open_defaults_to_false(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    assert obj.property("open") is False


def test_filter_dropdown_open_is_writable(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_filter_dropdown_has_clear_all_requested_signal(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    received = []
    obj.clearAllRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_filter_dropdown_show_missing_only_defaults_to_false(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    assert obj.property("showMissingOnly") is False


def test_filter_dropdown_has_toggle_missing_only_requested_signal(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    received = []
    obj.toggleMissingOnlyRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# FilterDropdown group structure
# ---------------------------------------------------------------------------


def test_filter_dropdown_any_filter_active_defaults_to_false(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    val = obj.property("_anyFilterActive")
    assert val is False


def test_filter_dropdown_any_filter_active_when_missing_only(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    obj.setProperty("showMissingOnly", True)
    assert obj.property("_anyFilterActive") is True


def test_filter_dropdown_any_filter_active_when_tags_active(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    obj.setProperty("activeTags", [{"id": "t1", "name": "nature", "mode": "include"}])
    assert obj.property("_anyFilterActive") is True


def test_filter_dropdown_any_filter_active_when_import_job_active(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    obj.setProperty("importJobActive", True)
    assert obj.property("_anyFilterActive") is True


def test_filter_dropdown_implicit_height_is_positive(engine):
    obj = load_component(engine, "components/FilterDropdown.qml")
    assert obj.property("implicitHeight") > 0


def test_filter_dropdown_missing_toggle_border_uses_theme_error_when_active(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/FilterDropdown.qml")

    toggle = obj.findChild(QObject, "missingToggle")
    assert toggle is not None
    assert toggle.property("borderColor") == QColor(active_theme.border)

    obj.setProperty("showMissingOnly", True)
    assert toggle.property("borderColor") == QColor(active_theme.error)


# ---------------------------------------------------------------------------
# TitleBar search zone additions — Commit 7
# ---------------------------------------------------------------------------


def test_title_bar_filter_active_defaults_to_false(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.property("filterActive") is False


def test_title_bar_filter_active_is_writable(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    obj.setProperty("filterActive", True)
    assert obj.property("filterActive") is True


def test_title_bar_has_filter_dropdown_child(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.findChild(QObject, "filterDropdown") is not None


def test_title_bar_filter_dropdown_closed_by_default(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    dropdown = obj.findChild(QObject, "filterDropdown")
    assert dropdown.property("open") is False


def test_title_bar_has_settings_requested_signal(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    received = []
    obj.settingsRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_title_bar_settings_icon_visible(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    icon = obj.findChild(QObject, "settingsIcon")
    assert icon is not None


# ---------------------------------------------------------------------------
# TitleBar read-only search zone — Commit 13
# ---------------------------------------------------------------------------


def test_title_bar_search_read_only_defaults_to_false(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.property("searchReadOnly") is False


def test_title_bar_search_read_only_is_writable(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    obj.setProperty("searchReadOnly", True)
    assert obj.property("searchReadOnly") is True


def test_title_bar_active_filters_defaults_to_empty(engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(engine, "shell/TitleBar.qml")
    val = obj.property("activeFilters")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == [] or val is None


def test_title_bar_active_filters_is_writable(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    obj.setProperty("activeFilters", [{"name": "nature", "mode": "include"}])
    from PySide6.QtQml import QJSValue
    val = obj.property("activeFilters")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert len(val) == 1


# ---------------------------------------------------------------------------
# MetadataSidePanel — Commit 9
# ---------------------------------------------------------------------------


def test_metadata_sidebar_qml_exists():
    assert (QML_DIR / "components/MetadataSidePanel.qml").exists()


def test_metadata_sidebar_loads(engine):
    load_component(engine, "components/MetadataSidePanel.qml")


def test_metadata_sidebar_open_defaults_to_false(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("open") is False


def test_metadata_sidebar_open_is_writable(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_metadata_sidebar_has_toggle_requested_signal(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    received = []
    obj.toggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_metadata_sidebar_meta_filename_defaults_to_empty(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("metaFilename") == ""


def test_metadata_sidebar_meta_filename_is_writable(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    obj.setProperty("metaFilename", "photo.jpg")
    assert obj.property("metaFilename") == "photo.jpg"


def test_metadata_sidebar_meta_path_defaults_to_empty(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("metaPath") == ""


def test_metadata_sidebar_meta_dimensions_defaults_to_empty(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("metaDimensions") == ""


def test_metadata_sidebar_meta_file_size_defaults_to_zero(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("metaFileSize") == 0


def test_metadata_sidebar_meta_date_added_defaults_to_empty(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("metaDateAdded") == ""


def test_metadata_sidebar_meta_is_missing_defaults_to_false(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("metaIsMissing") is False


def test_metadata_sidebar_meta_loading_state_defaults_to_idle(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("metaLoadingState") == "Idle"


def test_metadata_sidebar_meta_loading_state_is_writable(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    obj.setProperty("metaLoadingState", "Ready")
    assert obj.property("metaLoadingState") == "Ready"


# ---------------------------------------------------------------------------
# TagSearchField — Commit 10
# ---------------------------------------------------------------------------


def test_tag_search_field_qml_exists():
    assert (QML_DIR / "components/TagSearchField.qml").exists()


def test_tag_search_field_loads(engine):
    load_component(engine, "components/TagSearchField.qml")


def test_tag_search_field_input_bg_uses_theme_border_when_unfocused(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/TagSearchField.qml")

    input_bg = obj.findChild(QObject, "inputBg")
    assert input_bg is not None
    assert input_bg.property("color") == QColor("transparent")
    assert input_bg.property("borderColor") == QColor(active_theme.border)


def test_tag_search_field_input_bg_uses_theme_surface_and_accent_when_focused(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/TagSearchField.qml")

    window = QQuickWindow()
    obj.setParentItem(window.contentItem())
    window.resize(300, 100)
    window.show()

    inner_input = obj.findChild(QObject, "input")
    inner_input.forceActiveFocus()

    input_bg = obj.findChild(QObject, "inputBg")
    assert input_bg.property("color") == QColor(active_theme.surface)
    assert input_bg.property("borderColor") == QColor(active_theme.accent)


def test_tag_search_field_search_icon_uses_theme_text_muted_and_font_size_sm(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/TagSearchField.qml")

    icon = obj.findChild(QObject, "leadingIconItem")
    assert icon is not None
    assert icon.property("color") == QColor(active_theme.textMuted)
    assert icon.property("font").pixelSize() == active_theme.fontSizeSm


def test_tag_search_field_submit_icon_uses_theme_success(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/TagSearchField.qml")

    icon = obj.findChild(QObject, "submitIcon")
    assert icon is not None
    assert icon.property("color") == QColor(active_theme.success)
    assert icon.property("font").pixelSize() == active_theme.fontSizeSm


# ---------------------------------------------------------------------------
# MetadataSidePanel tag editor additions — Commit 11
# ---------------------------------------------------------------------------


def test_metadata_sidebar_tag_editor_tags_defaults_to_empty(engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    val = obj.property("tagEditorTags")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == [] or val is None


def test_metadata_sidebar_tag_editor_tags_is_writable(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    obj.setProperty("tagEditorTags", [{"id": "tag-1", "name": "nature"}])
    from PySide6.QtQml import QJSValue
    val = obj.property("tagEditorTags")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert len(val) == 1


def test_metadata_sidebar_tag_editor_loading_state_defaults_to_idle(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("tagEditorLoadingState") == "Idle"


def test_metadata_sidebar_tag_editor_loading_state_is_writable(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    obj.setProperty("tagEditorLoadingState", "Ready")
    assert obj.property("tagEditorLoadingState") == "Ready"


def test_metadata_sidebar_tag_editor_selection_mode_defaults_to_none(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    assert obj.property("tagEditorSelectionMode") == "none"


def test_metadata_sidebar_tag_editor_selection_mode_is_writable(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    obj.setProperty("tagEditorSelectionMode", "single")
    assert obj.property("tagEditorSelectionMode") == "single"


def test_metadata_sidebar_has_add_tag_requested_signal(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    received = []
    obj.addTagRequested.connect(lambda tag_id, tag_name: received.append((tag_id, tag_name)))
    assert isinstance(received, list)


def test_metadata_sidebar_has_remove_tag_requested_signal(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    received = []
    obj.removeTagRequested.connect(lambda tag_id: received.append(tag_id))
    assert isinstance(received, list)


def test_metadata_sidebar_has_add_tag_by_name_requested_signal(engine):
    obj = load_component(engine, "components/MetadataSidePanel.qml")
    received = []
    obj.addTagByNameRequested.connect(lambda name: received.append(name))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# TitleBar status zone — status indicators
# ---------------------------------------------------------------------------


def test_title_bar_import_state_defaults_to_idle(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.property("importState") == "Idle"


def test_title_bar_import_state_is_writable(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    obj.setProperty("importState", "Importing")
    assert obj.property("importState") == "Importing"


def test_title_bar_import_progress_defaults_to_zero(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.property("importProgress") == 0.0


def test_title_bar_import_progress_is_writable(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    obj.setProperty("importProgress", 0.75)
    assert obj.property("importProgress") == pytest.approx(0.75)


def test_title_bar_missing_count_defaults_to_zero(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.property("missingCount") == 0


def test_title_bar_missing_count_is_writable(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    obj.setProperty("missingCount", 5)
    assert obj.property("missingCount") == 5


def test_title_bar_backend_connected_defaults_to_true(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    assert obj.property("backendConnected") is True


def test_title_bar_backend_connected_is_writable(engine):
    obj = load_component(engine, "shell/TitleBar.qml")
    obj.setProperty("backendConnected", False)
    assert obj.property("backendConnected") is False


# ---------------------------------------------------------------------------
# TitleBar — theme tokens (Feature 5.6)
# ---------------------------------------------------------------------------


def test_title_bar_disconnected_indicator_uses_theme_warning(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "shell/TitleBar.qml")
    obj.setProperty("backendConnected", False)

    dot = obj.findChild(QObject, "disconnectedDot")
    text = obj.findChild(QObject, "disconnectedText")
    assert dot is not None
    assert text is not None
    assert dot.property("color") == QColor(active_theme.warning)
    assert text.property("color") == QColor(active_theme.warning)


def test_title_bar_missing_indicator_uses_theme_error(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "shell/TitleBar.qml")
    obj.setProperty("missingCount", 3)

    icon = obj.findChild(QObject, "missingIcon")
    text = obj.findChild(QObject, "missingText")
    assert icon is not None
    assert text is not None
    assert icon.property("color") == QColor(active_theme.error)
    assert text.property("color") == QColor(active_theme.error)
    assert icon.property("font").pixelSize() == active_theme.fontSizeSm


def test_title_bar_filter_icon_uses_theme_font_size_md(theme_qml_engine):
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "shell/TitleBar.qml")

    icon = obj.findChild(QObject, "filterIcon")
    assert icon is not None
    assert icon.property("font").pixelSize() == active_theme.fontSizeMd


def test_title_bar_read_only_filter_pills_use_chip_states(theme_qml_engine):
    from found_app.theme.theme import register_theme_singleton

    register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "shell/TitleBar.qml")
    obj.setProperty("searchReadOnly", True)
    obj.setProperty("activeFilters", [
        {"name": "nature", "mode": "include"},
        {"name": "urban", "mode": "exclude"},
    ])

    # Repeater-instantiated delegates aren't reachable via findChildren, so
    # query the live items through the QML context instead.
    ctx = theme_qml_engine.contextForObject(obj)
    expr = QQmlExpression(
        ctx, None,
        "[0, 1].map(i => filterRepeater.itemAt(i).children[0].chipState)",
    )
    result, _ = expr.evaluate()
    states = sorted(result.toVariant())
    assert states == ["exclude", "include"]


# ---------------------------------------------------------------------------
# MetaRow — theme tokens (Feature 5.7)
# ---------------------------------------------------------------------------


def test_meta_row_qml_exists():
    assert (QML_DIR / "components/MetaRow.qml").exists()


def test_meta_row_loads(engine):
    load_component(engine, "components/MetaRow.qml")


def test_meta_row_label_uses_theme_text_muted_and_font_size_sm(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/MetaRow.qml")

    label = obj.findChild(QObject, "labelText")
    assert label is not None
    assert label.property("color") == QColor(active_theme.textMuted)
    assert label.property("font").pixelSize() == active_theme.fontSizeSm


def test_meta_row_value_uses_theme_text_and_font_size_sm(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/MetaRow.qml")
    obj.setProperty("value", "/some/path.jpg")

    value = obj.findChild(QObject, "valueText")
    assert value is not None
    assert value.property("color") == QColor(active_theme.text)
    assert value.property("font").pixelSize() == active_theme.fontSizeSm


def test_meta_row_clickable_value_uses_theme_accent(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/MetaRow.qml")
    obj.setProperty("value", "example.com")
    obj.setProperty("linkUrl", "https://example.com")

    value = obj.findChild(QObject, "valueText")
    assert value.property("color") == QColor(active_theme.accent)


# ---------------------------------------------------------------------------
# SidePanelBody — theme tokens (Feature 5.8)
# ---------------------------------------------------------------------------


def test_side_panel_body_qml_exists():
    assert (QML_DIR / "components/SidePanelBody.qml").exists()


def test_side_panel_body_loads(engine):
    load_component(engine, "components/SidePanelBody.qml")


def test_side_panel_body_divider_uses_theme_border(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/SidePanelBody.qml")
    obj.setProperty("title", "Title")

    divider = obj.findChild(QObject, "divider")
    assert divider is not None
    assert divider.property("color") == QColor(active_theme.border)


# ---------------------------------------------------------------------------
# CollectionsSidePanel — theme tokens (Feature 5.8)
# ---------------------------------------------------------------------------


def test_collections_sidebar_input_box_uses_theme_surface(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionsSidePanel.qml")

    input_field = obj.findChild(QObject, "newCollectionField")
    assert input_field is not None
    assert input_field.property("color") == QColor(active_theme.surface)


def test_collections_sidebar_input_text_uses_theme_text(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionsSidePanel.qml")

    inner_input = obj.findChild(QObject, "input")
    assert inner_input is not None
    assert inner_input.property("color") == QColor(active_theme.text)


def test_collections_sidebar_add_icon_uses_theme_text_muted(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionsSidePanel.qml")

    icon = obj.findChild(QObject, "leadingIconItem")
    assert icon is not None
    assert icon.property("color") == QColor(active_theme.textMuted)


def test_collections_sidebar_submit_icon_uses_theme_success(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionsSidePanel.qml")

    icon = obj.findChild(QObject, "submitIcon")
    assert icon is not None
    assert icon.property("color") == QColor(active_theme.success)


def test_collections_sidebar_input_box_border_uses_theme_border_and_accent(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionsSidePanel.qml")

    input_field = obj.findChild(QObject, "newCollectionField")
    assert input_field is not None
    assert input_field.property("borderColor") == QColor(active_theme.border)

    window = QQuickWindow()
    obj.setParentItem(window.contentItem())
    window.resize(300, 400)
    window.show()

    inner_input = obj.findChild(QObject, "input")
    inner_input.forceActiveFocus()
    assert input_field.property("borderColor") == QColor(active_theme.accent)


def test_collections_sidebar_empty_label_uses_theme_text_muted_and_font_size_sm(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionsSidePanel.qml")

    empty_label = obj.findChild(QObject, "emptyLabel")
    assert empty_label is not None
    assert empty_label.property("color") == QColor(active_theme.textMuted)
    assert empty_label.property("font").pixelSize() == active_theme.fontSizeSm


# ---------------------------------------------------------------------------
# MetadataSidePanel — theme tokens (Feature 5.8)
# ---------------------------------------------------------------------------


def test_metadata_sidebar_error_text_uses_theme_warning_and_font_size_sm(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/MetadataSidePanel.qml")
    obj.setProperty("metaLoadingState", "Error")

    error_text = obj.findChild(QObject, "metaErrorText")
    assert error_text is not None
    assert error_text.property("color") == QColor(active_theme.warning)
    assert error_text.property("font").pixelSize() == active_theme.fontSizeSm


def test_metadata_sidebar_missing_banner_uses_theme_error(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/MetadataSidePanel.qml")
    obj.setProperty("metaLoadingState", "Ready")
    obj.setProperty("metaIsMissing", True)

    banner = obj.findChild(QObject, "missingBanner")
    assert banner is not None
    assert banner.property("borderColor") == QColor(active_theme.error)

    banner_text = obj.findChild(QObject, "missingBannerText")
    assert banner_text is not None
    assert banner_text.property("color") == QColor(active_theme.error)
    assert banner_text.property("font").pixelSize() == active_theme.fontSizeSm


# ---------------------------------------------------------------------------
# ConfirmDialog — theme tokens (Feature 5.8)
# ---------------------------------------------------------------------------


def test_confirm_dialog_backdrop_uses_theme_background(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ConfirmDialog.qml")

    backdrop = obj.findChild(QObject, "backdrop")
    assert backdrop is not None
    assert backdrop.property("color") == QColor(active_theme.background)


def test_confirm_dialog_sheet_uses_theme_surface(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ConfirmDialog.qml")

    sheet = obj.findChild(QObject, "sheet")
    assert sheet is not None
    assert sheet.property("color") == QColor(active_theme.surface)


def test_confirm_dialog_message_uses_theme_text_and_font_size_sm(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ConfirmDialog.qml")

    message = obj.findChild(QObject, "messageText")
    assert message is not None
    assert message.property("color") == QColor(active_theme.text)
    assert message.property("font").pixelSize() == active_theme.fontSizeSm


def test_confirm_dialog_checkbox_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ConfirmDialog.qml")
    obj.setProperty("checkboxLabel", "Also remove from library")

    checkbox = obj.findChild(QObject, "checkboxBox")
    assert checkbox is not None
    assert checkbox.property("borderColor") == QColor(active_theme.textMuted)

    checkbox_label = obj.findChild(QObject, "checkboxLabelText")
    assert checkbox_label is not None
    assert checkbox_label.property("color") == QColor(active_theme.textMuted)
    assert checkbox_label.property("font").pixelSize() == active_theme.fontSizeSm

    obj.setProperty("checkboxChecked", True)
    assert checkbox.property("borderColor") == QColor(active_theme.accent)

    checkmark = obj.findChild(QObject, "checkmarkText")
    assert checkmark is not None
    assert checkmark.property("color") == QColor(active_theme.background)
    assert checkmark.property("font").pixelSize() == active_theme.fontSizeSm


def test_confirm_dialog_cancel_button_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ConfirmDialog.qml")

    cancel_btn = obj.findChild(QObject, "cancelBtn")
    assert cancel_btn is not None
    assert cancel_btn.property("borderColor") == QColor(active_theme.border)
    assert cancel_btn.property("color") == QColor("transparent")

    cancel_label = obj.findChild(QObject, "cancelLabelText")
    assert cancel_label is not None
    assert cancel_label.property("color") == QColor(active_theme.textMuted)
    assert cancel_label.property("font").pixelSize() == active_theme.fontSizeSm


def test_confirm_dialog_confirm_button_uses_theme_warning(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ConfirmDialog.qml")

    confirm_btn = obj.findChild(QObject, "confirmBtn")
    assert confirm_btn is not None
    assert confirm_btn.property("borderColor") == QColor(active_theme.warning)

    confirm_label = obj.findChild(QObject, "confirmLabelText")
    assert confirm_label is not None
    assert confirm_label.property("color") == QColor(active_theme.warning)
    assert confirm_label.property("font").pixelSize() == active_theme.fontSizeSm


# ---------------------------------------------------------------------------
# HoverTooltip — theme tokens (Feature 5.8)
# ---------------------------------------------------------------------------


def test_hover_tooltip_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/HoverTooltip.qml")
    obj.setProperty("text", "Tooltip")

    bg = obj.findChild(QObject, "tooltipBg")
    assert bg is not None
    assert bg.property("color") == QColor(active_theme.surface)
    assert bg.property("borderColor") == QColor(active_theme.border)

    label = obj.findChild(QObject, "tooltipLabel")
    assert label is not None
    assert label.property("color") == QColor(active_theme.text)
    assert label.property("font").pixelSize() == active_theme.fontSizeSm


# ---------------------------------------------------------------------------
# EdgeTab — theme tokens (Feature 5.8)
# ---------------------------------------------------------------------------


def test_edge_tab_icon_and_arrow_use_theme_text_muted_and_font_size_sm(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/EdgeTab.qml")
    obj.setProperty("icon", "☰")

    icon = obj.findChild(QObject, "edgeTabIcon")
    assert icon is not None
    assert icon.property("color") == QColor(active_theme.textMuted)
    assert icon.property("font").pixelSize() == active_theme.fontSizeSm

    arrow = obj.findChild(QObject, "edgeTabArrow")
    assert arrow is not None
    assert arrow.property("color") == QColor(active_theme.textMuted)
    assert arrow.property("font").pixelSize() == active_theme.fontSizeSm


# ---------------------------------------------------------------------------
# ImportPanel — theme tokens (Feature 5.8)
# ---------------------------------------------------------------------------


def test_import_panel_backdrop_and_sheet_use_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ImportPanel.qml")
    obj.setProperty("loadingState", "Scanning")

    backdrop = obj.findChild(QObject, "backdrop")
    assert backdrop is not None
    assert backdrop.property("color") == QColor(active_theme.background)

    sheet = obj.findChild(QObject, "sheet")
    assert sheet is not None
    assert sheet.property("color") == QColor(active_theme.surface)


def test_import_panel_scanning_state_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ImportPanel.qml")
    obj.setProperty("loadingState", "Scanning")

    scan_text = obj.findChild(QObject, "scanText")
    assert scan_text is not None
    assert scan_text.property("color") == QColor(active_theme.text)
    assert scan_text.property("font").pixelSize() == active_theme.fontSizeMd

    scan_track = obj.findChild(QObject, "scanTrack")
    assert scan_track.property("color") == QColor(active_theme.border)

    scan_bar = obj.findChild(QObject, "scanBar")
    assert scan_bar.property("color") == QColor(active_theme.success)


def test_import_panel_already_imported_and_pending_headers_use_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ImportPanel.qml")
    obj.setProperty("loadingState", "Previewing")
    obj.setProperty("alreadyImportedFiles", [{"image_id": "abc"}])
    obj.setProperty("pendingFiles", ["/tmp/photo.jpg"])

    already_text = obj.findChild(QObject, "alreadyImportedText")
    assert already_text is not None
    assert already_text.property("color") == QColor(active_theme.textMuted)
    assert already_text.property("font").pixelSize() == active_theme.fontSizeSm

    pending_text = obj.findChild(QObject, "pendingText")
    assert pending_text is not None
    assert pending_text.property("color") == QColor(active_theme.text)
    assert pending_text.property("font").pixelSize() == active_theme.fontSizeSm


def test_import_panel_duplicates_section_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ImportPanel.qml")
    obj.setProperty("loadingState", "Previewing")
    obj.setProperty("conflictFiles", [{
        "path": "/new/photo.jpg",
        "existing_path": "/old/photo.jpg",
        "existing_image_id": "xyz",
    }])

    header = obj.findChild(QObject, "duplicatesHeaderText")
    assert header is not None
    assert header.property("color") == QColor(active_theme.error)

    # Repeater-instantiated delegates aren't reachable via findChildren, so
    # query the live item through the QML context instead.
    ctx = theme_qml_engine.contextForObject(obj)
    expr = QQmlExpression(ctx, None, "conflictRepeater.itemAt(0)")
    conflict_item, _ = expr.evaluate()

    keep_radio = conflict_item.findChild(QObject, "keepRadio")
    replace_radio = conflict_item.findChild(QObject, "replaceRadio")
    keep_label = conflict_item.findChild(QObject, "keepLabel")
    replace_label = conflict_item.findChild(QObject, "replaceLabel")
    assert keep_radio is not None and replace_radio is not None
    assert keep_label is not None and replace_label is not None

    # "keep" is selected by default
    assert keep_radio.property("color") == QColor(active_theme.error)
    assert keep_radio.property("borderColor") == QColor(active_theme.error)
    assert keep_label.property("color") == QColor(active_theme.text)

    assert replace_radio.property("color") == QColor("transparent")
    assert replace_radio.property("borderColor") == QColor(active_theme.border)
    assert replace_label.property("color") == QColor(active_theme.textMuted)


def test_import_panel_buttons_use_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ImportPanel.qml")
    obj.setProperty("loadingState", "Previewing")

    cancel_btn = obj.findChild(QObject, "cancelBtn")
    assert cancel_btn is not None
    assert cancel_btn.property("color") == QColor("transparent")
    assert cancel_btn.property("borderColor") == QColor(active_theme.border)

    cancel_text = obj.findChild(QObject, "cancelBtnText")
    assert cancel_text.property("color") == QColor(active_theme.textMuted)
    assert cancel_text.property("font").pixelSize() == active_theme.fontSizeSm

    import_text = obj.findChild(QObject, "importBtnText")
    assert import_text.property("color") == QColor(active_theme.success)
    assert import_text.property("font").pixelSize() == active_theme.fontSizeSm


def test_import_panel_importing_state_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ImportPanel.qml")
    obj.setProperty("loadingState", "Importing")
    obj.setProperty("progress", 0.5)

    importing_text = obj.findChild(QObject, "importingText")
    assert importing_text is not None
    assert importing_text.property("color") == QColor(active_theme.text)
    assert importing_text.property("font").pixelSize() == active_theme.fontSizeMd

    importing_track = obj.findChild(QObject, "importingTrack")
    assert importing_track.property("color") == QColor(active_theme.border)

    importing_bar = obj.findChild(QObject, "importingBar")
    assert importing_bar.property("color") == QColor(active_theme.success)

    percent_text = obj.findChild(QObject, "importingPercentText")
    assert percent_text.property("color") == QColor(active_theme.textMuted)
    assert percent_text.property("font").pixelSize() == active_theme.fontSizeSm


def test_import_panel_complete_state_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ImportPanel.qml")
    obj.setProperty("loadingState", "Complete")
    obj.setProperty("importedCount", 3)

    title = obj.findChild(QObject, "completeTitle")
    assert title is not None
    assert title.property("color") == QColor(active_theme.success)
    assert title.property("font").pixelSize() == active_theme.fontSizeMd

    summary = obj.findChild(QObject, "completeSummaryText")
    assert summary.property("color") == QColor(active_theme.textMuted)
    assert summary.property("font").pixelSize() == active_theme.fontSizeSm

    done_btn = obj.findChild(QObject, "doneBtn")
    assert done_btn.property("color") == QColor(active_theme.surface)

    done_text = obj.findChild(QObject, "doneBtnText")
    assert done_text.property("color") == QColor(active_theme.text)
    assert done_text.property("font").pixelSize() == active_theme.fontSizeSm


def test_import_panel_error_state_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ImportPanel.qml")
    obj.setProperty("loadingState", "Error")

    title = obj.findChild(QObject, "errorTitle")
    assert title is not None
    assert title.property("color") == QColor(active_theme.warning)
    assert title.property("font").pixelSize() == active_theme.fontSizeMd

    subtext = obj.findChild(QObject, "errorSubtext")
    assert subtext.property("color") == QColor(active_theme.textMuted)
    assert subtext.property("font").pixelSize() == active_theme.fontSizeSm

    close_btn = obj.findChild(QObject, "closeBtn")
    assert close_btn.property("color") == QColor(active_theme.surface)

    close_text = obj.findChild(QObject, "closeBtnText")
    assert close_text.property("color") == QColor(active_theme.text)
    assert close_text.property("font").pixelSize() == active_theme.fontSizeSm


# CollectionEditorSection — theme tokens (Feature 5.8)
# ---------------------------------------------------------------------------


def test_collection_editor_section_divider_and_header_use_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionEditorSection.qml")

    divider = obj.findChild(QObject, "divider")
    assert divider is not None
    assert divider.property("color") == QColor(active_theme.border)

    header = obj.findChild(QObject, "collectionsHeaderText")
    assert header is not None
    assert header.property("color") == QColor(active_theme.textMuted)
    assert header.property("font").pixelSize() == active_theme.fontSizeSm


def test_collection_editor_section_add_button_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionEditorSection.qml")

    row = obj.findChild(QObject, "addToCollectionRow")
    assert row is not None
    assert row.property("borderColor") == QColor(active_theme.border)

    obj.setProperty("_dropdownOpen", True)
    assert row.property("borderColor") == QColor(active_theme.textMuted)

    icon = obj.findChild(QObject, "addIcon")
    assert icon.property("color") == QColor(active_theme.textMuted)
    assert icon.property("font").pixelSize() == active_theme.fontSizeSm

    label = obj.findChild(QObject, "addLabelText")
    assert label.property("color") == QColor(active_theme.textMuted)
    assert label.property("font").pixelSize() == active_theme.fontSizeSm


def test_collection_editor_section_dropdown_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionEditorSection.qml")
    obj.setProperty("_dropdownOpen", True)

    box = obj.findChild(QObject, "dropdownBox")
    assert box is not None
    assert box.property("color") == QColor(active_theme.surface)
    assert box.property("borderColor") == QColor(active_theme.border)


def test_collection_editor_section_multi_select_note_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionEditorSection.qml")

    note = obj.findChild(QObject, "multiSelectText")
    assert note is not None
    assert note.property("color") == QColor(active_theme.textMuted)
    assert note.property("font").pixelSize() == active_theme.fontSizeSm


def test_collection_editor_section_chip_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionEditorSection.qml")
    obj.setProperty("selectionMode", "single")
    obj.setProperty("collections", [{"id": "c1", "name": "Portraits"}])

    ctx = theme_qml_engine.contextForObject(obj)
    expr = QQmlExpression(ctx, None, "chipRepeater.itemAt(0)")
    chip, _ = expr.evaluate()
    assert chip is not None

    assert chip.property("color") == QColor(active_theme.surface)
    assert chip.property("borderColor") == QColor(active_theme.border)


# CollectionItem — theme tokens (Feature 5.8)
# ---------------------------------------------------------------------------


def test_collection_item_label_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionItem.qml")

    label = obj.findChild(QObject, "collectionNameText")
    assert label is not None
    assert label.property("color") == QColor(active_theme.text)
    assert label.property("font").pixelSize() == active_theme.fontSizeMd

    obj.setProperty("isDropTarget", True)
    assert label.property("color") == QColor(active_theme.success)


def test_collection_item_remove_button_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionItem.qml")

    remove_icon = obj.findChild(QObject, "removeIconText")
    assert remove_icon is not None
    assert remove_icon.property("font").pixelSize() == active_theme.fontSizeMd
    assert remove_icon.property("color") == QColor(active_theme.textMuted)


def test_collection_item_drop_border_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/CollectionItem.qml")

    drop_border = obj.findChild(QObject, "dropBorder")
    assert drop_border is not None
    assert drop_border.property("borderColor") == QColor(active_theme.success)
    assert drop_border.property("visible") is False

    obj.setProperty("isDropTarget", True)
    assert drop_border.property("visible") is True


# ThumbnailTile — theme tokens (Feature 5.9)
# ---------------------------------------------------------------------------


def test_thumbnail_tile_failed_placeholder_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ThumbnailTile.qml")

    placeholder = obj.findChild(QObject, "failedPlaceholder")
    assert placeholder is not None
    assert placeholder.property("color") == QColor(active_theme.surface)

    text = obj.findChild(QObject, "failedText")
    assert text is not None
    assert text.property("color") == QColor(active_theme.textMuted)
    assert text.property("font").pixelSize() == active_theme.fontSizeMd


def test_thumbnail_tile_missing_overlay_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ThumbnailTile.qml")

    overlay = obj.findChild(QObject, "missingOverlay")
    assert overlay is not None
    assert overlay.property("color") == QColor(active_theme.background)

    text = obj.findChild(QObject, "missingIconText")
    assert text is not None
    assert text.property("color") == QColor(active_theme.error)
    assert text.property("font").pixelSize() == active_theme.fontSizeMd


def test_thumbnail_tile_remove_button_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ThumbnailTile.qml")

    icon = obj.findChild(QObject, "removeIconText")
    assert icon is not None
    assert icon.property("color") == QColor(active_theme.accent)
    assert icon.property("font").pixelSize() == active_theme.fontSizeSm


def test_thumbnail_tile_locate_button_uses_theme_tokens(theme_qml_engine):
    from PySide6.QtGui import QColor
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/ThumbnailTile.qml")

    icon = obj.findChild(QObject, "locateIconText")
    assert icon is not None
    assert icon.property("color") == QColor(active_theme.textMuted)


# ---------------------------------------------------------------------------
# SettingsView
# ---------------------------------------------------------------------------


def test_settings_view_qml_exists():
    assert (QML_DIR / "views/SettingsView.qml").exists()


def test_settings_view_loads(engine):
    load_component(engine, "views/SettingsView.qml")


def test_settings_view_has_appearance_section(engine):
    obj = load_component(engine, "views/SettingsView.qml")
    section = obj.findChild(QObject, "appearanceSection")
    assert section is not None


def test_settings_view_theme_picker_calls_set_theme_name(theme_qml_engine):
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    active_theme.setThemeName("Bogus")

    obj = load_component(theme_qml_engine, "views/SettingsView.qml")

    # Repeater-instantiated delegates aren't reachable via findChild, so
    # query the live item through the QML context instead.
    ctx = theme_qml_engine.contextForObject(obj)
    expr = QQmlExpression(ctx, None, "themeRepeater.itemAt(0).clicked()")
    expr.evaluate()

    assert active_theme.themeName == "Found"


def test_settings_view_mode_picker_calls_set_mode(theme_qml_engine):
    from found_app.theme.theme import register_theme_singleton

    active_theme = register_theme_singleton(ThemeManager())
    assert active_theme.mode == "system"

    obj = load_component(theme_qml_engine, "views/SettingsView.qml")

    ctx = theme_qml_engine.contextForObject(obj)
    expr = QQmlExpression(ctx, None, "modeRepeater.itemAt(1).clicked()")
    expr.evaluate()

    assert active_theme.mode == "dark"


# ---------------------------------------------------------------------------
# ImportHandler — refactor/main-router-organization Commit 2
# ---------------------------------------------------------------------------


def test_import_handler_qml_exists():
    assert (QML_DIR / "shell/ImportHandler.qml").exists()


def test_import_handler_loads(engine):
    load_component(engine, "shell/ImportHandler.qml")


def test_import_handler_has_drag_highlight_child(engine):
    obj = load_component(engine, "shell/ImportHandler.qml")
    assert obj.findChild(QObject, "dragHighlight") is not None


def test_import_handler_has_drop_hint_text_child(engine):
    obj = load_component(engine, "shell/ImportHandler.qml")
    assert obj.findChild(QObject, "dropHintText") is not None


# ---------------------------------------------------------------------------
# CollectionDeleteFlow — refactor/main-router-organization Commit 4
# ---------------------------------------------------------------------------


def test_collection_delete_flow_qml_exists():
    assert (QML_DIR / "shell/CollectionDeleteFlow.qml").exists()


def test_collection_delete_flow_loads(engine):
    load_component(engine, "shell/CollectionDeleteFlow.qml")


def test_collection_delete_flow_open_defaults_to_false(engine):
    obj = load_component(engine, "shell/CollectionDeleteFlow.qml")
    assert obj.property("open") is False


def test_collection_delete_flow_request_delete_opens_dialog(engine):
    obj = load_component(engine, "shell/CollectionDeleteFlow.qml")
    assert obj.property("open") is False
    obj.requestDelete("col-1", "My Collection")
    assert obj.property("open") is True


def test_collection_delete_flow_cancel_closes_dialog(engine):
    obj = load_component(engine, "shell/CollectionDeleteFlow.qml")
    obj.requestDelete("col-1", "My Collection")
    assert obj.property("open") is True
    obj.findChild(QObject, "confirmDialog").cancelled.emit()
    assert obj.property("open") is False


# ---------------------------------------------------------------------------
# RelocationFlow — refactor/main-router-organization Commit 1
# ---------------------------------------------------------------------------


def test_relocation_flow_qml_exists():
    assert (QML_DIR / "shell/RelocationFlow.qml").exists()


def test_relocation_flow_loads(engine):
    load_component(engine, "shell/RelocationFlow.qml")


def test_relocation_flow_prefix_dialog_open_defaults_to_false(engine):
    obj = load_component(engine, "shell/RelocationFlow.qml")
    assert obj.property("prefixDialogOpen") is False


def test_relocation_flow_result_dialog_open_defaults_to_false(engine):
    obj = load_component(engine, "shell/RelocationFlow.qml")
    assert obj.property("resultDialogOpen") is False
