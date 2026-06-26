"""
Tests for per-view side panel state persistence.

Panel open state is saved and restored by PanelLayout.saveViewState /
restoreViewState on every view navigation. Each view maintains its own
open-panel snapshot, and restoreViewState only applies panels that are
available in the entering view.
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QObject, QEventLoop, QTimer
from PySide6.QtQml import QQmlApplicationEngine

import found_app
from found_app.theme.theme import ThemeManager
from found_app.core.app_state import AppStateManager
from found_app.services.filter_state import FilterStateManager
from found_app.services.navigation import NavigationManager
from found_app.services.panel_layout import PanelLayoutManager
from found_app.services.selection import SelectionManager
from found_app.viewmodels.collections_view_model import CollectionsViewModel
from found_app.viewmodels.import_view_model import ImportViewModel
from found_app.viewmodels.library_view_model import LibraryViewModel
from found_app.viewmodels.metadata_view_model import MetadataViewModel
from found_app.viewmodels.tag_editor_view_model import TagEditorViewModel
from found_app.viewmodels.tag_search_view_model import TagSearchViewModel

QML_DIR = Path(found_app.__file__).parent / "qml"


@pytest.fixture
def app_engine(qapp):
    """Full QQmlApplicationEngine with PanelLayout and NavigationManager exposed."""
    navigation = NavigationManager()
    panel_layout = PanelLayoutManager()  # settings=None → default edges

    e = QQmlApplicationEngine()
    e.rootContext().setContextProperty("PanelLayout", panel_layout)
    e.rootContext().setContextProperty("Theme", ThemeManager())
    e.rootContext().setContextProperty("AppState", AppStateManager())
    e.rootContext().setContextProperty("LibraryState", LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: None,
    ))
    e.rootContext().setContextProperty("SelectionManager", SelectionManager())
    e.rootContext().setContextProperty("NavigationManager", navigation)
    e.rootContext().setContextProperty("CollectionsState", CollectionsViewModel(
        collections_fetcher=lambda: [],
        collection_creator=lambda name: None,
        images_adder=lambda cid, iids: False,
        collection_images_fetcher=lambda cid: [],
    ))
    e.rootContext().setContextProperty("ImportState", ImportViewModel(
        scanner=lambda paths: {
            "new": [], "already_imported": [], "conflicts": [], "invalid": []
        },
        importer=lambda paths: "job-id",
        job_fetcher=lambda jid: {
            "status": "completed", "total_files": 0, "processed_files": 0,
            "successful_imports": 0, "duplicate_paths": 0,
            "duplicate_hashes": 0, "failed_imports": 0,
        },
    ))
    e.rootContext().setContextProperty("FilterState", FilterStateManager())
    e.rootContext().setContextProperty("MetadataState", MetadataViewModel(
        image_fetcher=lambda image_id: None,
    ))
    e.rootContext().setContextProperty("TagSearchState", TagSearchViewModel(
        tags_fetcher=lambda term: [],
    ))
    e.rootContext().setContextProperty("TagEditorSearchState", TagSearchViewModel(
        tags_fetcher=lambda term: [],
    ))
    e.rootContext().setContextProperty("TagEditorState", TagEditorViewModel(
        image_tags_fetcher=lambda image_id: [],
        tag_modifier=lambda image_ids, add_ids, remove_ids: True,
    ))
    e.rootContext().setContextProperty("baseUrl", "http://127.0.0.1:8000")
    e.rootContext().setContextProperty("foundVersion", "0.1.0")
    e.rootContext().setContextProperty("foundLicense", "GNU GPL v3.0")
    e.load(str(QML_DIR / "main.qml"))
    assert e.rootObjects(), "main.qml failed to load"

    root = e.rootObjects()[0]
    container = root.findChild(QObject, "readyContainer")
    assert container is not None, "readyContainer not found"

    panel_layout.setParent(e)

    yield e, navigation, panel_layout, container
    e.clearComponentCache()


def _spin(ms: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


# ---------------------------------------------------------------------------
# Default state
# ---------------------------------------------------------------------------


def test_all_panels_closed_on_startup(app_engine):
    """All side panels are closed when the app starts."""
    _, _, panel_layout, _ = app_engine
    assert panel_layout.openPanels == {"left": "", "right": ""}


# ---------------------------------------------------------------------------
# Panel margin scoping — CollectionView is unaffected by left panel state
# ---------------------------------------------------------------------------


def test_collection_view_left_panel_open_false_when_collections_panel_open(app_engine):
    """CollectionView.leftPanelOpen is always False — collections panel is library-only."""
    engine, navigation, panel_layout, _ = app_engine
    panel_layout.togglePanel("collections")
    navigation.push("collection", {"collection_id": "col-1", "collection_name": "Test"})
    _spin()
    root = engine.rootObjects()[0]
    collection_view = root.findChild(QObject, "collectionView")
    assert collection_view is not None, "collectionView objectName not found"
    assert collection_view.property("leftPanelOpen") is False


# ---------------------------------------------------------------------------
# Library ↔ Collection
# ---------------------------------------------------------------------------


def test_library_sidebar_restored_after_collection(app_engine):
    """Collections panel open in library is restored when returning from collection."""
    _, navigation, panel_layout, _ = app_engine
    panel_layout.togglePanel("collections")
    navigation.push("collection", {"collection_id": "col-1", "collection_name": "Test"})
    navigation.goBack()
    assert panel_layout.openPanels["left"] == "collections"


def test_library_metadata_panel_restored_after_collection(app_engine):
    """Metadata panel open in library is restored when returning from collection."""
    _, navigation, panel_layout, _ = app_engine
    panel_layout.togglePanel("metadata")
    navigation.push("collection", {"collection_id": "col-1", "collection_name": "Test"})
    navigation.goBack()
    assert panel_layout.openPanels["right"] == "metadata"


def test_collection_metadata_panel_independent_from_library(app_engine):
    """Opening metadata panel in library does not carry over to collection view."""
    _, navigation, panel_layout, _ = app_engine
    panel_layout.togglePanel("metadata")
    navigation.push("collection", {"collection_id": "col-1", "collection_name": "Test"})
    assert panel_layout.openPanels["right"] == ""


def test_collection_metadata_panel_restored_after_image_view(app_engine):
    """Metadata panel opened in collection is restored when returning from image view."""
    _, navigation, panel_layout, _ = app_engine
    navigation.push("collection", {"collection_id": "col-1", "collection_name": "Test"})
    panel_layout.togglePanel("metadata")
    navigation.push("image", {"image_id": "img-1"})
    navigation.goBack()
    assert panel_layout.openPanels["right"] == "metadata"


# ---------------------------------------------------------------------------
# Library ↔ Image
# ---------------------------------------------------------------------------


def test_library_metadata_panel_restored_after_image_view(app_engine):
    """Metadata panel open in library is restored when returning from image view."""
    _, navigation, panel_layout, _ = app_engine
    panel_layout.togglePanel("metadata")
    navigation.push("image", {"image_id": "img-1"})
    navigation.goBack()
    assert panel_layout.openPanels["right"] == "metadata"


def test_image_view_metadata_panel_starts_closed(app_engine):
    """Image view's metadata panel is closed on first entry, independent of library state."""
    _, navigation, panel_layout, _ = app_engine
    panel_layout.togglePanel("metadata")
    navigation.push("image", {"image_id": "img-1"})
    assert panel_layout.openPanels["right"] == ""
