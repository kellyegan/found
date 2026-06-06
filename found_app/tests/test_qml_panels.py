"""
Tests for EdgeTab and SidePanel QML components.

Covers:
- EdgeTab.qml exists and loads cleanly
- EdgeTab exposes edge, open, icon, tooltip properties and clicked signal
- SidePanel.qml exists and loads cleanly
- SidePanel exposes edge, open, title, panelIcon, tabIndex properties
- SidePanel exposes toggleRequested signal
- CollectionsSidePanel and MetadataSidePanel public APIs are unchanged after refactor
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent

import found_app
from found_app.theme.theme import ThemeManager
from found_app.viewmodels.tag_search_view_model import TagSearchViewModel
from found_app.viewmodels.tag_editor_view_model import TagEditorViewModel
from found_app.services.filter_state import FilterStateManager
from found_app.services.navigation import NavigationManager
from found_app.services.selection import SelectionManager

QML_DIR = Path(found_app.__file__).parent / "qml"


@pytest.fixture
def engine(qapp):
    """Minimal engine for EdgeTab / SidePanel — only Theme required."""
    theme = ThemeManager()
    e = QQmlEngine()
    e.rootContext().setContextProperty("Theme", theme)
    theme.setParent(e)
    yield e
    e.clearComponentCache()


@pytest.fixture
def full_engine(qapp):
    """Richer engine for sidebar components that depend on view-model context properties."""
    theme = ThemeManager()
    selection = SelectionManager()
    navigation = NavigationManager()
    filter_state = FilterStateManager()
    tag_search = TagSearchViewModel(tags_fetcher=lambda term: [])
    tag_editor_search = TagSearchViewModel(tags_fetcher=lambda term: [])
    tag_editor = TagEditorViewModel(
        image_tags_fetcher=lambda image_id: [],
        tag_modifier=lambda image_ids, add_ids, remove_ids: True,
    )
    e = QQmlEngine()
    e.rootContext().setContextProperty("Theme", theme)
    e.rootContext().setContextProperty("SelectionManager", selection)
    e.rootContext().setContextProperty("NavigationManager", navigation)
    e.rootContext().setContextProperty("FilterState", filter_state)
    e.rootContext().setContextProperty("TagSearchState", tag_search)
    e.rootContext().setContextProperty("TagEditorSearchState", tag_editor_search)
    e.rootContext().setContextProperty("TagEditorState", tag_editor)
    for obj in [theme, selection, navigation, filter_state, tag_search, tag_editor_search, tag_editor]:
        obj.setParent(e)
    yield e
    e.clearComponentCache()


def load_component(engine, filename: str):
    path = QML_DIR / filename
    assert path.exists(), f"{filename} not found at {path}"
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(path)))
    errors = [err.toString() for err in component.errors()]
    assert not errors, f"{filename} load errors: {errors}"
    assert component.status() == QQmlComponent.Status.Ready, (
        f"{filename} status: {component.status()}"
    )
    obj = component.create(engine.rootContext())
    assert obj is not None, f"{filename} create() returned None"
    obj.setParent(engine)
    return obj


# ---------------------------------------------------------------------------
# EdgeTab — file existence
# ---------------------------------------------------------------------------


def test_edge_tab_qml_exists():
    assert (QML_DIR / "components/EdgeTab.qml").exists()


# ---------------------------------------------------------------------------
# EdgeTab — loads and has correct properties
# ---------------------------------------------------------------------------


def test_edge_tab_loads(engine):
    load_component(engine, "components/EdgeTab.qml")


def test_edge_tab_edge_defaults_to_right(engine):
    obj = load_component(engine, "components/EdgeTab.qml")
    assert obj.property("edge") == "right"


def test_edge_tab_edge_is_writable(engine):
    obj = load_component(engine, "components/EdgeTab.qml")
    obj.setProperty("edge", "left")
    assert obj.property("edge") == "left"


def test_edge_tab_open_defaults_to_false(engine):
    obj = load_component(engine, "components/EdgeTab.qml")
    assert obj.property("open") is False


def test_edge_tab_open_is_writable(engine):
    obj = load_component(engine, "components/EdgeTab.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_edge_tab_icon_defaults_to_empty(engine):
    obj = load_component(engine, "components/EdgeTab.qml")
    assert obj.property("icon") == ""


def test_edge_tab_icon_is_writable(engine):
    obj = load_component(engine, "components/EdgeTab.qml")
    obj.setProperty("icon", "☰")
    assert obj.property("icon") == "☰"


def test_edge_tab_tooltip_defaults_to_empty(engine):
    obj = load_component(engine, "components/EdgeTab.qml")
    assert obj.property("tooltip") == ""


def test_edge_tab_tooltip_is_writable(engine):
    obj = load_component(engine, "components/EdgeTab.qml")
    obj.setProperty("tooltip", "Collections")
    assert obj.property("tooltip") == "Collections"


def test_edge_tab_has_clicked_signal(engine):
    obj = load_component(engine, "components/EdgeTab.qml")
    received = []
    obj.clicked.connect(lambda: received.append(1))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# SidePanel — file existence
# ---------------------------------------------------------------------------


def test_side_panel_qml_exists():
    assert (QML_DIR / "components/SidePanel.qml").exists()


# ---------------------------------------------------------------------------
# SidePanel — loads and has correct properties
# ---------------------------------------------------------------------------


def test_side_panel_loads(engine):
    load_component(engine, "components/SidePanel.qml")


def test_side_panel_edge_defaults_to_right(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    assert obj.property("edge") == "right"


def test_side_panel_edge_is_writable(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    obj.setProperty("edge", "left")
    assert obj.property("edge") == "left"


def test_side_panel_open_defaults_to_false(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    assert obj.property("open") is False


def test_side_panel_open_is_writable(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_side_panel_title_defaults_to_empty(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    assert obj.property("title") == ""


def test_side_panel_title_is_writable(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    obj.setProperty("title", "Collections")
    assert obj.property("title") == "Collections"


def test_side_panel_panel_icon_defaults_to_empty(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    assert obj.property("panelIcon") == ""


def test_side_panel_panel_icon_is_writable(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    obj.setProperty("panelIcon", "☰")
    assert obj.property("panelIcon") == "☰"


def test_side_panel_tab_index_defaults_to_zero(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    assert obj.property("tabIndex") == 0


def test_side_panel_tab_index_is_writable(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    obj.setProperty("tabIndex", 1)
    assert obj.property("tabIndex") == 1


def test_side_panel_has_toggle_requested_signal(engine):
    obj = load_component(engine, "components/SidePanel.qml")
    received = []
    obj.toggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# CollectionsSidePanel — public API preserved after refactor
# ---------------------------------------------------------------------------


def test_collections_sidebar_still_loads(full_engine):
    load_component(full_engine, "components/CollectionsSidePanel.qml")


def test_collections_sidebar_open_still_defaults_to_false(full_engine):
    obj = load_component(full_engine, "components/CollectionsSidePanel.qml")
    assert obj.property("open") is False


def test_collections_sidebar_open_still_writable(full_engine):
    obj = load_component(full_engine, "components/CollectionsSidePanel.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_collections_sidebar_toggle_requested_signal_preserved(full_engine):
    obj = load_component(full_engine, "components/CollectionsSidePanel.qml")
    received = []
    obj.toggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_collections_sidebar_image_dropped_signal_preserved(full_engine):
    obj = load_component(full_engine, "components/CollectionsSidePanel.qml")
    received = []
    obj.imageDropped.connect(lambda cid, iid: received.append((cid, iid)))
    assert isinstance(received, list)


def test_collections_sidebar_collection_clicked_signal_preserved(full_engine):
    obj = load_component(full_engine, "components/CollectionsSidePanel.qml")
    received = []
    obj.collectionClicked.connect(lambda cid, cname: received.append((cid, cname)))
    assert isinstance(received, list)


def test_collections_sidebar_create_collection_requested_signal_preserved(full_engine):
    obj = load_component(full_engine, "components/CollectionsSidePanel.qml")
    received = []
    obj.createCollectionRequested.connect(lambda name: received.append(name))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# MetadataSidePanel — public API preserved after refactor
# ---------------------------------------------------------------------------


def test_metadata_sidebar_still_loads(full_engine):
    load_component(full_engine, "components/MetadataSidePanel.qml")


def test_metadata_sidebar_open_still_defaults_to_false(full_engine):
    obj = load_component(full_engine, "components/MetadataSidePanel.qml")
    assert obj.property("open") is False


def test_metadata_sidebar_open_still_writable(full_engine):
    obj = load_component(full_engine, "components/MetadataSidePanel.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_metadata_sidebar_toggle_requested_signal_preserved(full_engine):
    obj = load_component(full_engine, "components/MetadataSidePanel.qml")
    received = []
    obj.toggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_metadata_sidebar_meta_loading_state_preserved(full_engine):
    obj = load_component(full_engine, "components/MetadataSidePanel.qml")
    assert obj.property("metaLoadingState") == "Idle"


def test_metadata_sidebar_add_tag_requested_signal_preserved(full_engine):
    obj = load_component(full_engine, "components/MetadataSidePanel.qml")
    received = []
    obj.addTagRequested.connect(lambda tid, tname: received.append((tid, tname)))
    assert isinstance(received, list)


def test_metadata_sidebar_add_category_requested_signal_preserved(full_engine):
    obj = load_component(full_engine, "components/MetadataSidePanel.qml")
    received = []
    obj.addCategoryRequested.connect(lambda cid, cname: received.append((cid, cname)))
    assert isinstance(received, list)


def test_metadata_sidebar_add_to_collection_requested_signal_preserved(full_engine):
    obj = load_component(full_engine, "components/MetadataSidePanel.qml")
    received = []
    obj.addToCollectionRequested.connect(lambda cid, cname: received.append((cid, cname)))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# MetaRow
# ---------------------------------------------------------------------------


def test_meta_row_qml_exists():
    assert (QML_DIR / "components/MetaRow.qml").exists()


def test_meta_row_loads(engine):
    load_component(engine, "components/MetaRow.qml")


def test_meta_row_label_defaults_to_empty(engine):
    obj = load_component(engine, "components/MetaRow.qml")
    assert obj.property("label") == ""


def test_meta_row_label_is_writable(engine):
    obj = load_component(engine, "components/MetaRow.qml")
    obj.setProperty("label", "Filename")
    assert obj.property("label") == "Filename"


def test_meta_row_value_defaults_to_empty(engine):
    obj = load_component(engine, "components/MetaRow.qml")
    assert obj.property("value") == ""


def test_meta_row_value_is_writable(engine):
    obj = load_component(engine, "components/MetaRow.qml")
    obj.setProperty("value", "photo.jpg")
    assert obj.property("value") == "photo.jpg"


def test_meta_row_wrap_defaults_to_false(engine):
    obj = load_component(engine, "components/MetaRow.qml")
    assert obj.property("wrap") is False


def test_meta_row_wrap_is_writable(engine):
    obj = load_component(engine, "components/MetaRow.qml")
    obj.setProperty("wrap", True)
    assert obj.property("wrap") is True


# ---------------------------------------------------------------------------
# ChipSearchSection
# ---------------------------------------------------------------------------


def test_chip_search_section_qml_exists():
    assert (QML_DIR / "components/ChipSearchSection.qml").exists()


def test_chip_search_section_loads(engine):
    load_component(engine, "components/ChipSearchSection.qml")


def test_chip_search_section_section_label_defaults_to_empty(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    assert obj.property("sectionLabel") == ""


def test_chip_search_section_section_label_is_writable(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    obj.setProperty("sectionLabel", "Tags")
    assert obj.property("sectionLabel") == "Tags"


def test_chip_search_section_selection_mode_defaults_to_none(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    assert obj.property("selectionMode") == "none"


def test_chip_search_section_selection_mode_is_writable(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    obj.setProperty("selectionMode", "single")
    assert obj.property("selectionMode") == "single"


def test_chip_search_section_items_defaults_to_empty(engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(engine, "components/ChipSearchSection.qml")
    val = obj.property("items")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == [] or val is None


def test_chip_search_section_search_state_defaults_to_none(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    assert obj.property("searchState") is None


def test_chip_search_section_allow_create_new_defaults_to_false(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    assert obj.property("allowCreateNew") is False


def test_chip_search_section_allow_create_new_is_writable(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    obj.setProperty("allowCreateNew", True)
    assert obj.property("allowCreateNew") is True


def test_chip_search_section_placeholder_defaults_to_empty(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    assert obj.property("placeholder") == ""


def test_chip_search_section_placeholder_is_writable(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    obj.setProperty("placeholder", "Add tag…")
    assert obj.property("placeholder") == "Add tag…"


def test_chip_search_section_multi_select_label_defaults_to_empty(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    assert obj.property("multiSelectLabel") == ""


def test_chip_search_section_multi_select_label_is_writable(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    obj.setProperty("multiSelectLabel", "Adding tags to all selected images")
    assert obj.property("multiSelectLabel") == "Adding tags to all selected images"


def test_chip_search_section_has_add_requested_signal(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    received = []
    obj.addRequested.connect(lambda id, name: received.append((id, name)))
    assert isinstance(received, list)


def test_chip_search_section_has_remove_requested_signal(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    received = []
    obj.removeRequested.connect(lambda id: received.append(id))
    assert isinstance(received, list)


def test_chip_search_section_has_add_by_name_requested_signal(engine):
    obj = load_component(engine, "components/ChipSearchSection.qml")
    received = []
    obj.addByNameRequested.connect(lambda name: received.append(name))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# CollectionEditorSection
# ---------------------------------------------------------------------------


def test_collection_editor_section_qml_exists():
    assert (QML_DIR / "components/CollectionEditorSection.qml").exists()


def test_collection_editor_section_loads(engine):
    load_component(engine, "components/CollectionEditorSection.qml")


def test_collection_editor_section_selection_mode_defaults_to_none(engine):
    obj = load_component(engine, "components/CollectionEditorSection.qml")
    assert obj.property("selectionMode") == "none"


def test_collection_editor_section_selection_mode_is_writable(engine):
    obj = load_component(engine, "components/CollectionEditorSection.qml")
    obj.setProperty("selectionMode", "single")
    assert obj.property("selectionMode") == "single"


def test_collection_editor_section_collections_defaults_to_empty(engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(engine, "components/CollectionEditorSection.qml")
    val = obj.property("collections")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == [] or val is None


def test_collection_editor_section_multi_select_label_defaults_to_empty(engine):
    obj = load_component(engine, "components/CollectionEditorSection.qml")
    assert obj.property("multiSelectLabel") == ""


def test_collection_editor_section_multi_select_label_is_writable(engine):
    obj = load_component(engine, "components/CollectionEditorSection.qml")
    obj.setProperty("multiSelectLabel", "Adding to all selected images")
    assert obj.property("multiSelectLabel") == "Adding to all selected images"


def test_collection_editor_section_has_add_to_collection_requested_signal(engine):
    obj = load_component(engine, "components/CollectionEditorSection.qml")
    received = []
    obj.addToCollectionRequested.connect(lambda cid, cname: received.append((cid, cname)))
    assert isinstance(received, list)


def test_collection_editor_section_has_remove_from_collection_requested_signal(engine):
    obj = load_component(engine, "components/CollectionEditorSection.qml")
    received = []
    obj.removeFromCollectionRequested.connect(lambda cid: received.append(cid))
    assert isinstance(received, list)
