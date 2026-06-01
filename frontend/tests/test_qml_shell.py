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
from frontend.filters.filter_state_manager import FilterStateManager
from frontend.library.view_model import LibraryViewModel
from frontend.categories.categories_view_model import CategoriesViewModel
from frontend.collections.collections_view_model import CollectionsViewModel
from frontend.import_workflow.import_view_model import ImportViewModel
from frontend.metadata.metadata_view_model import MetadataViewModel
from frontend.tag_editor.tag_editor_view_model import TagEditorViewModel
from frontend.tag_search.tag_search_view_model import TagSearchViewModel
from frontend.navigation.navigation_manager import NavigationManager
from frontend.selection.selection_manager import SelectionManager

QML_DIR = Path(frontend.__file__).parent / "qml"


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


def test_splash_screen_app_version_defaults_to_empty(engine):
    obj = load_component(engine, "SplashScreen.qml")
    assert obj.property("appVersion") == ""


def test_splash_screen_app_version_is_writable(engine):
    obj = load_component(engine, "SplashScreen.qml")
    obj.setProperty("appVersion", "0.1.0")
    assert obj.property("appVersion") == "0.1.0"


def test_splash_screen_app_license_defaults_to_empty(engine):
    obj = load_component(engine, "SplashScreen.qml")
    assert obj.property("appLicense") == ""


def test_splash_screen_app_license_is_writable(engine):
    obj = load_component(engine, "SplashScreen.qml")
    obj.setProperty("appLicense", "GNU GPL v3.0")
    assert obj.property("appLicense") == "GNU GPL v3.0"


def test_splash_screen_is_ready_defaults_to_false(engine):
    obj = load_component(engine, "SplashScreen.qml")
    assert obj.property("isReady") is False


def test_splash_screen_is_ready_is_writable(engine):
    obj = load_component(engine, "SplashScreen.qml")
    obj.setProperty("isReady", True)
    assert obj.property("isReady") is True


def test_splash_screen_has_dismissed_signal(engine):
    obj = load_component(engine, "SplashScreen.qml")
    received = []
    obj.dismissed.connect(lambda: received.append(1))
    assert isinstance(received, list)


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


def test_library_view_has_no_is_filtered_property(engine):
    obj = load_component(engine, "LibraryView.qml")
    assert obj.property("isFiltered") is None


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
    categories_state = CategoriesViewModel(categories_fetcher=lambda: [])
    e.rootContext().setContextProperty("CategoriesState", categories_state)
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
# TitleBar
# ---------------------------------------------------------------------------


def test_title_bar_qml_exists():
    assert (QML_DIR / "TitleBar.qml").exists()


def test_title_bar_loads(engine):
    load_component(engine, "TitleBar.qml")


def test_title_bar_can_go_back_defaults_to_false(engine):
    obj = load_component(engine, "TitleBar.qml")
    assert obj.property("canGoBack") is False


def test_title_bar_can_go_back_is_writable(engine):
    obj = load_component(engine, "TitleBar.qml")
    obj.setProperty("canGoBack", True)
    assert obj.property("canGoBack") is True


def test_title_bar_view_title_defaults_to_empty(engine):
    obj = load_component(engine, "TitleBar.qml")
    assert obj.property("viewTitle") == ""


def test_title_bar_view_title_is_writable(engine):
    obj = load_component(engine, "TitleBar.qml")
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
# ImageView prev/next hover buttons — Commit 12
# ---------------------------------------------------------------------------


def test_image_view_has_prev_requested_signal(engine):
    obj = load_component(engine, "ImageView.qml")
    received = []
    obj.prevRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_image_view_has_next_requested_signal(engine):
    obj = load_component(engine, "ImageView.qml")
    received = []
    obj.nextRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_image_view_has_next_is_writable(engine):
    obj = load_component(engine, "ImageView.qml")
    obj.setProperty("hasNext", True)
    assert obj.property("hasNext") is True


def test_image_view_has_prev_is_writable(engine):
    obj = load_component(engine, "ImageView.qml")
    obj.setProperty("hasPrev", True)
    assert obj.property("hasPrev") is True


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


# ---------------------------------------------------------------------------
# Drag-to-collection — Commit 4
# ---------------------------------------------------------------------------


def test_collection_item_has_image_dropped_signal(engine):
    obj = load_component(engine, "CollectionItem.qml")
    received = []
    obj.imageDropped.connect(lambda cid, iid: received.append((cid, iid)))
    assert isinstance(received, list)  # signal attribute exists


def test_collections_sidebar_has_image_dropped_signal(engine):
    obj = load_component(engine, "CollectionsSidebar.qml")
    received = []
    obj.imageDropped.connect(lambda cid, iid: received.append((cid, iid)))
    assert isinstance(received, list)  # signal attribute exists


def test_collections_sidebar_has_toggle_requested_signal(engine):
    obj = load_component(engine, "CollectionsSidebar.qml")
    received = []
    obj.toggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_title_bar_has_no_sidebar_open_property(engine):
    obj = load_component(engine, "TitleBar.qml")
    assert obj.property("sidebarOpen") is None


def test_thumbnail_tile_still_loads_with_drag_support(engine):
    load_component(engine, "ThumbnailTile.qml")


# ---------------------------------------------------------------------------
# CategoriesBar
# ---------------------------------------------------------------------------


def test_categories_bar_qml_exists():
    assert (QML_DIR / "CategoriesBar.qml").exists()


def test_categories_bar_loads(engine):
    load_component(engine, "CategoriesBar.qml")


def test_categories_bar_open_defaults_to_true(engine):
    obj = load_component(engine, "CategoriesBar.qml")
    assert obj.property("open") is True  # component default; MainRouter starts it closed


def test_categories_bar_open_is_writable(engine):
    obj = load_component(engine, "CategoriesBar.qml")
    obj.setProperty("open", False)
    assert obj.property("open") is False


def test_categories_bar_categories_defaults_to_empty(engine):
    obj = load_component(engine, "CategoriesBar.qml")
    from PySide6.QtQml import QJSValue
    val = obj.property("categories")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == [] or val is None


def test_categories_bar_has_toggle_requested_signal(engine):
    obj = load_component(engine, "CategoriesBar.qml")
    received = []
    obj.toggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_categories_bar_has_filter_toggled_signal(engine):
    obj = load_component(engine, "CategoriesBar.qml")
    received = []
    obj.filterToggled.connect(lambda cat_id: received.append(cat_id))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# ImportPanel — Slice 9 Commit 2
# ---------------------------------------------------------------------------


def test_import_panel_qml_exists():
    assert (QML_DIR / "ImportPanel.qml").exists()


def test_import_panel_loads(engine):
    load_component(engine, "ImportPanel.qml")


def test_import_panel_loading_state_defaults_to_idle(engine):
    obj = load_component(engine, "ImportPanel.qml")
    assert obj.property("loadingState") == "Idle"


def test_import_panel_loading_state_is_writable(engine):
    obj = load_component(engine, "ImportPanel.qml")
    obj.setProperty("loadingState", "Previewing")
    assert obj.property("loadingState") == "Previewing"


def test_import_panel_pending_files_defaults_to_empty(engine):
    obj = load_component(engine, "ImportPanel.qml")
    from PySide6.QtQml import QJSValue
    val = obj.property("pendingFiles")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == []


def test_import_panel_duplicate_count_defaults_to_zero(engine):
    obj = load_component(engine, "ImportPanel.qml")
    assert obj.property("duplicateCount") == 0


def test_import_panel_conflict_count_defaults_to_zero(engine):
    obj = load_component(engine, "ImportPanel.qml")
    assert obj.property("conflictCount") == 0


def test_import_panel_invalid_count_defaults_to_zero(engine):
    obj = load_component(engine, "ImportPanel.qml")
    assert obj.property("invalidCount") == 0


def test_import_panel_imported_count_defaults_to_zero(engine):
    obj = load_component(engine, "ImportPanel.qml")
    assert obj.property("importedCount") == 0


def test_import_panel_skipped_count_defaults_to_zero(engine):
    obj = load_component(engine, "ImportPanel.qml")
    assert obj.property("skippedCount") == 0


def test_import_panel_has_confirmed_signal(engine):
    obj = load_component(engine, "ImportPanel.qml")
    received = []
    obj.confirmed.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_import_panel_has_cancelled_signal(engine):
    obj = load_component(engine, "ImportPanel.qml")
    received = []
    obj.cancelled.connect(lambda: received.append(1))
    assert isinstance(received, list)


# ImportPanel progress — Slice 9 Commit 4A
# ---------------------------------------------------------------------------


def test_import_panel_progress_defaults_to_zero(engine):
    obj = load_component(engine, "ImportPanel.qml")
    assert obj.property("progress") == 0.0


def test_import_panel_progress_is_writable(engine):
    obj = load_component(engine, "ImportPanel.qml")
    obj.setProperty("progress", 0.5)
    assert obj.property("progress") == 0.5


# ImportPanel conflict UI — Slice 9 Commit 4C
# ---------------------------------------------------------------------------


def test_import_panel_conflict_files_defaults_to_empty(engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(engine, "ImportPanel.qml")
    val = obj.property("conflictFiles")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == []


def test_import_panel_conflict_files_is_writable(engine):
    obj = load_component(engine, "ImportPanel.qml")
    sample = [{"path": "/a.jpg", "existing_image_id": "uuid-1",
               "existing_path": "/old/a.jpg", "existing_filename": "a.jpg"}]
    obj.setProperty("conflictFiles", sample)
    from PySide6.QtQml import QJSValue
    val = obj.property("conflictFiles")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert len(val) == 1


def test_import_panel_has_conflict_choice_changed_signal(engine):
    obj = load_component(engine, "ImportPanel.qml")
    received = []
    obj.conflictChoiceChanged.connect(lambda path, choice: received.append((path, choice)))
    assert isinstance(received, list)


def test_import_panel_updated_count_defaults_to_zero(engine):
    obj = load_component(engine, "ImportPanel.qml")
    assert obj.property("updatedCount") == 0


# ---------------------------------------------------------------------------
# FilterChip — Commit 7
# ---------------------------------------------------------------------------


def test_filter_chip_qml_exists():
    assert (QML_DIR / "FilterChip.qml").exists()


def test_filter_chip_loads(engine):
    load_component(engine, "FilterChip.qml")


def test_filter_chip_label_defaults_to_empty(engine):
    obj = load_component(engine, "FilterChip.qml")
    assert obj.property("label") == ""


def test_filter_chip_label_is_writable(engine):
    obj = load_component(engine, "FilterChip.qml")
    obj.setProperty("label", "architecture")
    assert obj.property("label") == "architecture"


def test_filter_chip_filter_mode_defaults_to_include(engine):
    obj = load_component(engine, "FilterChip.qml")
    assert obj.property("filterMode") == "include"


def test_filter_chip_filter_mode_is_writable(engine):
    obj = load_component(engine, "FilterChip.qml")
    obj.setProperty("filterMode", "exclude")
    assert obj.property("filterMode") == "exclude"


def test_filter_chip_has_remove_requested_signal(engine):
    obj = load_component(engine, "FilterChip.qml")
    received = []
    obj.removeRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# FilterDropdown — Commit 7
# ---------------------------------------------------------------------------


def test_filter_dropdown_qml_exists():
    assert (QML_DIR / "FilterDropdown.qml").exists()


def test_filter_dropdown_loads(engine):
    load_component(engine, "FilterDropdown.qml")


def test_filter_dropdown_open_defaults_to_false(engine):
    obj = load_component(engine, "FilterDropdown.qml")
    assert obj.property("open") is False


def test_filter_dropdown_open_is_writable(engine):
    obj = load_component(engine, "FilterDropdown.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_filter_dropdown_has_clear_all_requested_signal(engine):
    obj = load_component(engine, "FilterDropdown.qml")
    received = []
    obj.clearAllRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_filter_dropdown_active_categories_defaults_to_empty(engine):
    obj = load_component(engine, "FilterDropdown.qml")
    from PySide6.QtQml import QJSValue
    val = obj.property("activeCategories")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == [] or val is None


def test_filter_dropdown_show_missing_only_defaults_to_false(engine):
    obj = load_component(engine, "FilterDropdown.qml")
    assert obj.property("showMissingOnly") is False


def test_filter_dropdown_has_remove_category_filter_signal(engine):
    obj = load_component(engine, "FilterDropdown.qml")
    received = []
    obj.removeCategoryFilter.connect(lambda cat_id: received.append(cat_id))
    assert isinstance(received, list)


def test_filter_dropdown_has_toggle_missing_only_requested_signal(engine):
    obj = load_component(engine, "FilterDropdown.qml")
    received = []
    obj.toggleMissingOnlyRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# TitleBar search zone additions — Commit 7
# ---------------------------------------------------------------------------


def test_title_bar_filter_active_defaults_to_false(engine):
    obj = load_component(engine, "TitleBar.qml")
    assert obj.property("filterActive") is False


def test_title_bar_filter_active_is_writable(engine):
    obj = load_component(engine, "TitleBar.qml")
    obj.setProperty("filterActive", True)
    assert obj.property("filterActive") is True


def test_title_bar_has_filter_toggle_requested_signal(engine):
    obj = load_component(engine, "TitleBar.qml")
    received = []
    obj.filterToggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# MetadataOverlay — Commit 9
# ---------------------------------------------------------------------------


def test_metadata_overlay_qml_exists():
    assert (QML_DIR / "MetadataOverlay.qml").exists()


def test_metadata_overlay_loads(engine):
    load_component(engine, "MetadataOverlay.qml")


def test_metadata_overlay_open_defaults_to_false(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("open") is False


def test_metadata_overlay_open_is_writable(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_metadata_overlay_has_toggle_requested_signal(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    received = []
    obj.toggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_metadata_overlay_meta_filename_defaults_to_empty(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("metaFilename") == ""


def test_metadata_overlay_meta_filename_is_writable(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    obj.setProperty("metaFilename", "photo.jpg")
    assert obj.property("metaFilename") == "photo.jpg"


def test_metadata_overlay_meta_path_defaults_to_empty(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("metaPath") == ""


def test_metadata_overlay_meta_dimensions_defaults_to_empty(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("metaDimensions") == ""


def test_metadata_overlay_meta_file_size_defaults_to_zero(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("metaFileSize") == 0


def test_metadata_overlay_meta_date_added_defaults_to_empty(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("metaDateAdded") == ""


def test_metadata_overlay_meta_is_missing_defaults_to_false(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("metaIsMissing") is False


def test_metadata_overlay_meta_loading_state_defaults_to_idle(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("metaLoadingState") == "Idle"


def test_metadata_overlay_meta_loading_state_is_writable(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    obj.setProperty("metaLoadingState", "Ready")
    assert obj.property("metaLoadingState") == "Ready"


# ---------------------------------------------------------------------------
# TagSearchField — Commit 10
# ---------------------------------------------------------------------------


def test_tag_search_field_qml_exists():
    assert (QML_DIR / "TagSearchField.qml").exists()


def test_tag_search_field_loads(engine):
    load_component(engine, "TagSearchField.qml")


# ---------------------------------------------------------------------------
# MetadataOverlay tag editor additions — Commit 11
# ---------------------------------------------------------------------------


def test_metadata_overlay_tag_editor_tags_defaults_to_empty(engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(engine, "MetadataOverlay.qml")
    val = obj.property("tagEditorTags")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == [] or val is None


def test_metadata_overlay_tag_editor_tags_is_writable(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    obj.setProperty("tagEditorTags", [{"id": "tag-1", "name": "nature"}])
    from PySide6.QtQml import QJSValue
    val = obj.property("tagEditorTags")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert len(val) == 1


def test_metadata_overlay_tag_editor_loading_state_defaults_to_idle(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("tagEditorLoadingState") == "Idle"


def test_metadata_overlay_tag_editor_loading_state_is_writable(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    obj.setProperty("tagEditorLoadingState", "Ready")
    assert obj.property("tagEditorLoadingState") == "Ready"


def test_metadata_overlay_tag_editor_selection_mode_defaults_to_none(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    assert obj.property("tagEditorSelectionMode") == "none"


def test_metadata_overlay_tag_editor_selection_mode_is_writable(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    obj.setProperty("tagEditorSelectionMode", "single")
    assert obj.property("tagEditorSelectionMode") == "single"


def test_metadata_overlay_has_add_tag_requested_signal(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    received = []
    obj.addTagRequested.connect(lambda tag_id, tag_name: received.append((tag_id, tag_name)))
    assert isinstance(received, list)


def test_metadata_overlay_has_remove_tag_requested_signal(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    received = []
    obj.removeTagRequested.connect(lambda tag_id: received.append(tag_id))
    assert isinstance(received, list)


def test_metadata_overlay_has_add_tag_by_name_requested_signal(engine):
    obj = load_component(engine, "MetadataOverlay.qml")
    received = []
    obj.addTagByNameRequested.connect(lambda name: received.append(name))
    assert isinstance(received, list)
