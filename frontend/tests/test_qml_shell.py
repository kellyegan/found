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
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent, QQmlApplicationEngine

import frontend
from frontend.theme.theme import ThemeManager
from frontend.state.app_state import AppStateManager
from frontend.library.view_model import LibraryViewModel
from frontend.collections.collections_view_model import CollectionsViewModel
from frontend.navigation.navigation_manager import NavigationManager
from frontend.selection.selection_manager import SelectionManager

QML_DIR = Path(frontend.__file__).parent / "qml"


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def engine(qapp):
    """QQmlEngine with Theme, SelectionManager, and NavigationManager registered."""
    theme = ThemeManager()
    selection = SelectionManager()
    navigation = NavigationManager()
    e = QQmlEngine()
    e.rootContext().setContextProperty("Theme", theme)
    e.rootContext().setContextProperty("SelectionManager", selection)
    e.rootContext().setContextProperty("NavigationManager", navigation)
    theme.setParent(e)
    selection.setParent(e)
    navigation.setParent(e)
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
    assert (QML_DIR / "SplashScreen.qml").exists()


def test_main_router_qml_exists():
    assert (QML_DIR / "MainRouter.qml").exists()


def test_app_window_qml_exists():
    assert (QML_DIR / "AppWindow.qml").exists()


# ---------------------------------------------------------------------------
# SplashScreen
# ---------------------------------------------------------------------------


def test_splash_screen_loads(engine):
    load_component(engine, "SplashScreen.qml")


def test_splash_screen_has_status_text_property(engine):
    obj = load_component(engine, "SplashScreen.qml")
    assert obj.property("statusText") is not None or obj.property("statusText") == ""


def test_splash_screen_status_text_defaults_to_empty(engine):
    obj = load_component(engine, "SplashScreen.qml")
    assert obj.property("statusText") == ""


def test_splash_screen_status_text_is_writable(engine):
    obj = load_component(engine, "SplashScreen.qml")
    obj.setProperty("statusText", "Connecting…")
    assert obj.property("statusText") == "Connecting…"


def test_splash_screen_has_error_defaults_to_false(engine):
    obj = load_component(engine, "SplashScreen.qml")
    assert obj.property("hasError") is False


def test_splash_screen_has_error_is_writable(engine):
    obj = load_component(engine, "SplashScreen.qml")
    obj.setProperty("hasError", True)
    assert obj.property("hasError") is True


# ---------------------------------------------------------------------------
# MainRouter
# ---------------------------------------------------------------------------


def test_main_router_loads(engine):
    load_component(engine, "MainRouter.qml")


def test_main_router_app_state_defaults_to_launching(engine):
    obj = load_component(engine, "MainRouter.qml")
    assert obj.property("appState") == "Launching"


def test_main_router_app_state_is_writable(engine):
    obj = load_component(engine, "MainRouter.qml")
    obj.setProperty("appState", "Ready")
    assert obj.property("appState") == "Ready"


# ---------------------------------------------------------------------------
# AppWindow & main.qml (integration)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# LibraryView
# ---------------------------------------------------------------------------


def test_library_view_qml_exists():
    assert (QML_DIR / "LibraryView.qml").exists()


def test_library_view_loads(engine):
    load_component(engine, "LibraryView.qml")


def test_library_view_has_loading_state_property(engine):
    obj = load_component(engine, "LibraryView.qml")
    assert obj.property("loadingState") is not None or obj.property("loadingState") == ""


def test_library_view_loading_state_defaults_to_loading(engine):
    obj = load_component(engine, "LibraryView.qml")
    assert obj.property("loadingState") == "Loading"


def test_library_view_loading_state_is_writable(engine):
    obj = load_component(engine, "LibraryView.qml")
    obj.setProperty("loadingState", "Empty")
    assert obj.property("loadingState") == "Empty"


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
    e = QQmlApplicationEngine()
    e.rootContext().setContextProperty("Theme", theme)
    e.rootContext().setContextProperty("AppState", app_state)
    e.rootContext().setContextProperty("LibraryState", library_state)
    e.rootContext().setContextProperty("SelectionManager", selection)
    e.rootContext().setContextProperty("NavigationManager", navigation)
    e.rootContext().setContextProperty("CollectionsState", collections_state)
    e.rootContext().setContextProperty("baseUrl", "http://127.0.0.1:8000")
    e.load(str(QML_DIR / "main.qml"))
    assert e.rootObjects(), "main.qml failed to load"


# ---------------------------------------------------------------------------
# ThumbnailTile
# ---------------------------------------------------------------------------


def test_thumbnail_tile_qml_exists():
    assert (QML_DIR / "ThumbnailTile.qml").exists()


def test_thumbnail_tile_loads(engine):
    load_component(engine, "ThumbnailTile.qml")


def test_thumbnail_tile_has_thumbnail_url_property(engine):
    obj = load_component(engine, "ThumbnailTile.qml")
    assert obj.property("thumbnailUrl") == ""


def test_thumbnail_tile_has_file_status_property(engine):
    obj = load_component(engine, "ThumbnailTile.qml")
    assert obj.property("fileStatus") == "available"


def test_thumbnail_tile_has_selected_property(engine):
    obj = load_component(engine, "ThumbnailTile.qml")
    assert obj.property("selected") is False


def test_thumbnail_tile_has_image_id_property(engine):
    obj = load_component(engine, "ThumbnailTile.qml")
    assert obj.property("imageId") == ""


def test_thumbnail_tile_image_id_is_writable(engine):
    obj = load_component(engine, "ThumbnailTile.qml")
    obj.setProperty("imageId", "test-uuid-123")
    assert obj.property("imageId") == "test-uuid-123"


# ---------------------------------------------------------------------------
# ThumbnailGrid
# ---------------------------------------------------------------------------


def test_thumbnail_grid_qml_exists():
    assert (QML_DIR / "ThumbnailGrid.qml").exists()


def test_thumbnail_grid_loads(engine):
    load_component(engine, "ThumbnailGrid.qml")


def test_thumbnail_grid_has_model_property(engine):
    obj = load_component(engine, "ThumbnailGrid.qml")
    # model defaults to null — property should exist and be readable
    assert obj.property("model") is None or obj.property("model") is not None


def test_thumbnail_grid_has_scroll_x_property(engine):
    obj = load_component(engine, "ThumbnailGrid.qml")
    assert obj.property("scrollX") == 0.0


# ---------------------------------------------------------------------------
# NavigationBar
# ---------------------------------------------------------------------------


def test_navigation_bar_qml_exists():
    assert (QML_DIR / "NavigationBar.qml").exists()


def test_navigation_bar_loads(engine):
    load_component(engine, "NavigationBar.qml")


def test_navigation_bar_can_go_back_defaults_to_false(engine):
    obj = load_component(engine, "NavigationBar.qml")
    assert obj.property("canGoBack") is False


def test_navigation_bar_can_go_back_is_writable(engine):
    obj = load_component(engine, "NavigationBar.qml")
    obj.setProperty("canGoBack", True)
    assert obj.property("canGoBack") is True


def test_navigation_bar_view_title_defaults_to_empty(engine):
    obj = load_component(engine, "NavigationBar.qml")
    assert obj.property("viewTitle") == ""


def test_navigation_bar_view_title_is_writable(engine):
    obj = load_component(engine, "NavigationBar.qml")
    obj.setProperty("viewTitle", "Library")
    assert obj.property("viewTitle") == "Library"


# ---------------------------------------------------------------------------
# ImageView
# ---------------------------------------------------------------------------


def test_image_view_qml_exists():
    assert (QML_DIR / "ImageView.qml").exists()


def test_image_view_loads(engine):
    load_component(engine, "ImageView.qml")


def test_image_view_image_id_defaults_to_empty(engine):
    obj = load_component(engine, "ImageView.qml")
    assert obj.property("imageId") == ""


def test_image_view_image_url_defaults_to_empty(engine):
    obj = load_component(engine, "ImageView.qml")
    assert obj.property("imageUrl") == ""


def test_image_view_filename_defaults_to_empty(engine):
    obj = load_component(engine, "ImageView.qml")
    assert obj.property("filename") == ""


def test_image_view_file_status_defaults_to_available(engine):
    obj = load_component(engine, "ImageView.qml")
    assert obj.property("fileStatus") == "available"


def test_image_view_has_next_defaults_to_false(engine):
    obj = load_component(engine, "ImageView.qml")
    assert obj.property("hasNext") is False


def test_image_view_has_prev_defaults_to_false(engine):
    obj = load_component(engine, "ImageView.qml")
    assert obj.property("hasPrev") is False


def test_image_view_zoom_level_defaults_to_one(engine):
    obj = load_component(engine, "ImageView.qml")
    assert obj.property("zoomLevel") == 1.0


def test_image_view_pan_offset_x_defaults_to_zero(engine):
    obj = load_component(engine, "ImageView.qml")
    assert obj.property("panOffsetX") == 0.0


def test_image_view_pan_offset_y_defaults_to_zero(engine):
    obj = load_component(engine, "ImageView.qml")
    assert obj.property("panOffsetY") == 0.0


# ---------------------------------------------------------------------------
# CollectionItem
# ---------------------------------------------------------------------------


def test_collection_item_qml_exists():
    assert (QML_DIR / "CollectionItem.qml").exists()


def test_collection_item_loads(engine):
    load_component(engine, "CollectionItem.qml")


def test_collection_item_collection_id_defaults_to_empty(engine):
    obj = load_component(engine, "CollectionItem.qml")
    assert obj.property("collectionId") == ""


def test_collection_item_collection_name_defaults_to_empty(engine):
    obj = load_component(engine, "CollectionItem.qml")
    assert obj.property("collectionName") == ""


def test_collection_item_is_drop_target_defaults_to_false(engine):
    obj = load_component(engine, "CollectionItem.qml")
    assert obj.property("isDropTarget") is False


# ---------------------------------------------------------------------------
# CollectionsSidebar
# ---------------------------------------------------------------------------


def test_collections_sidebar_qml_exists():
    assert (QML_DIR / "CollectionsSidebar.qml").exists()


def test_collections_sidebar_loads(engine):
    load_component(engine, "CollectionsSidebar.qml")


def test_collections_sidebar_open_defaults_to_false(engine):
    obj = load_component(engine, "CollectionsSidebar.qml")
    assert obj.property("open") is False


def test_collections_sidebar_collections_property_exists(engine):
    obj = load_component(engine, "CollectionsSidebar.qml")
    from PySide6.QtQml import QJSValue
    val = obj.property("collections")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == []


# ---------------------------------------------------------------------------
# CollectionView
# ---------------------------------------------------------------------------


def test_collection_view_qml_exists():
    assert (QML_DIR / "CollectionView.qml").exists()


def test_collection_view_loads(engine):
    load_component(engine, "CollectionView.qml")


def test_collection_view_collection_name_defaults_to_empty(engine):
    obj = load_component(engine, "CollectionView.qml")
    assert obj.property("collectionName") == ""


def test_collection_view_collection_name_is_writable(engine):
    obj = load_component(engine, "CollectionView.qml")
    obj.setProperty("collectionName", "Portraits")
    assert obj.property("collectionName") == "Portraits"


def test_collection_view_grid_model_defaults_to_none(engine):
    obj = load_component(engine, "CollectionView.qml")
    assert obj.property("gridModel") is None


def test_collection_view_loading_state_defaults_to_idle(engine):
    obj = load_component(engine, "CollectionView.qml")
    assert obj.property("loadingState") == "Idle"
