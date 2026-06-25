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
from found_app.theme.theme import ThemeManager, register_theme_singleton
from found_app.viewmodels.tag_search_view_model import TagSearchViewModel
from found_app.viewmodels.tag_editor_view_model import TagEditorViewModel
from found_app.services.filter_state import FilterStateManager
from found_app.services.navigation import NavigationManager
from found_app.services.panel_layout import PanelLayoutManager
from found_app.services.selection import SelectionManager

QML_DIR = Path(found_app.__file__).parent / "qml"


@pytest.fixture
def engine(qapp):
    """Minimal engine for EdgeTab / SidePanelBody — Theme and PanelLayout required."""
    theme = ThemeManager()
    panel_layout = PanelLayoutManager()
    e = QQmlEngine()
    e.rootContext().setContextProperty("Theme", theme)
    e.rootContext().setContextProperty("PanelLayout", panel_layout)
    theme.setParent(e)
    panel_layout.setParent(e)
    yield e
    e.clearComponentCache()


@pytest.fixture
def full_engine(qapp):
    """Richer engine for sidebar components that depend on view-model context properties."""
    theme = ThemeManager()
    panel_layout = PanelLayoutManager()
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
    e.rootContext().setContextProperty("PanelLayout", panel_layout)
    e.rootContext().setContextProperty("SelectionManager", selection)
    e.rootContext().setContextProperty("NavigationManager", navigation)
    e.rootContext().setContextProperty("FilterState", filter_state)
    e.rootContext().setContextProperty("TagSearchState", tag_search)
    e.rootContext().setContextProperty("TagEditorSearchState", tag_editor_search)
    e.rootContext().setContextProperty("TagEditorState", tag_editor)
    for obj in [theme, panel_layout, selection, navigation, filter_state,
                tag_search, tag_editor_search, tag_editor]:
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
# SidePanelBody — file existence
# ---------------------------------------------------------------------------


def test_side_panel_body_qml_exists():
    assert (QML_DIR / "components/SidePanelBody.qml").exists()


# ---------------------------------------------------------------------------
# SidePanelBody — loads and has correct properties
# ---------------------------------------------------------------------------


def test_side_panel_body_loads(engine):
    load_component(engine, "components/SidePanelBody.qml")


def test_side_panel_body_panel_id_defaults_to_empty(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    assert obj.property("panelId") == ""


def test_side_panel_body_panel_id_is_writable(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    obj.setProperty("panelId", "collections")
    assert obj.property("panelId") == "collections"


def test_side_panel_body_edge_defaults_to_right_when_no_panel_id(engine):
    # panelId="" → PanelLayout.edges[""] is undefined → falls back to "right"
    obj = load_component(engine, "components/SidePanelBody.qml")
    assert obj.property("edge") == "right"


def test_side_panel_body_edge_reflects_panel_layout_default(engine, qapp):
    obj = load_component(engine, "components/SidePanelBody.qml")
    obj.setProperty("panelId", "collections")
    qapp.processEvents()
    assert obj.property("edge") == "left"


def test_side_panel_body_edge_updates_when_layout_changes(engine, qapp):
    panel_layout = engine.rootContext().contextProperty("PanelLayout")
    obj = load_component(engine, "components/SidePanelBody.qml")
    obj.setProperty("panelId", "collections")
    qapp.processEvents()
    assert obj.property("edge") == "left"

    panel_layout.setLayout("collections", "right", 0)
    qapp.processEvents()
    assert obj.property("edge") == "right"


def test_side_panel_body_open_defaults_to_false(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    assert obj.property("open") is False


def test_side_panel_body_open_is_writable(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    obj.setProperty("open", True)
    assert obj.property("open") is True


def test_side_panel_body_is_open_defaults_to_false(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    assert obj.property("isOpen") is False


def test_side_panel_body_is_open_reflects_panel_layout(engine, qapp):
    panel_layout = engine.rootContext().contextProperty("PanelLayout")
    obj = load_component(engine, "components/SidePanelBody.qml")
    obj.setProperty("panelId", "collections")
    qapp.processEvents()
    assert obj.property("isOpen") is False

    panel_layout.togglePanel("collections")
    qapp.processEvents()
    assert obj.property("isOpen") is True


def test_side_panel_body_title_defaults_to_empty(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    assert obj.property("title") == ""


def test_side_panel_body_title_is_writable(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    obj.setProperty("title", "Collections")
    assert obj.property("title") == "Collections"


def test_side_panel_body_panel_icon_defaults_to_empty(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    assert obj.property("panelIcon") == ""


def test_side_panel_body_panel_icon_is_writable(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    obj.setProperty("panelIcon", "☰")
    assert obj.property("panelIcon") == "☰"


def test_side_panel_body_tab_index_defaults_to_zero(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    assert obj.property("tabIndex") == 0


def test_side_panel_body_has_toggle_requested_signal(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    received = []
    obj.toggleRequested.connect(lambda: received.append(1))
    assert isinstance(received, list)


# ---------------------------------------------------------------------------
# SidePanelBody — dragOpenKeys
# ---------------------------------------------------------------------------


def test_side_panel_body_drag_open_keys_defaults_to_empty(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    from PySide6.QtQml import QJSValue
    val = obj.property("dragOpenKeys")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == [] or val is None


def test_side_panel_body_drag_open_keys_is_writable(engine):
    obj = load_component(engine, "components/SidePanelBody.qml")
    obj.setProperty("dragOpenKeys", ["found/image"])
    from PySide6.QtQml import QJSValue
    val = obj.property("dragOpenKeys")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == ["found/image"]


# ---------------------------------------------------------------------------
# CollectionsSidePanel — public API preserved after refactor
# ---------------------------------------------------------------------------


def test_collections_sidebar_drag_open_keys_set_to_image(full_engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(full_engine, "components/CollectionsSidePanel.qml")
    val = obj.property("dragOpenKeys")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert "found/image" in (val or [])


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


# ---------------------------------------------------------------------------
# DropdownList
# ---------------------------------------------------------------------------


def test_dropdown_list_qml_exists():
    assert (QML_DIR / "components/DropdownList.qml").exists()


def test_dropdown_list_loads(engine):
    load_component(engine, "components/DropdownList.qml")


def test_dropdown_list_model_defaults_to_empty(engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(engine, "components/DropdownList.qml")
    val = obj.property("model")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val == [] or val is None


def test_dropdown_list_model_is_writable(engine):
    from PySide6.QtQml import QJSValue
    obj = load_component(engine, "components/DropdownList.qml")
    obj.setProperty("model", [{"id": "1", "name": "Landscape"}])
    val = obj.property("model")
    if isinstance(val, QJSValue):
        val = val.toVariant() or []
    assert val is not None


def test_dropdown_list_max_height_defaults_to_160(engine):
    obj = load_component(engine, "components/DropdownList.qml")
    assert obj.property("maxHeight") == 160


def test_dropdown_list_max_height_is_writable(engine):
    obj = load_component(engine, "components/DropdownList.qml")
    obj.setProperty("maxHeight", 240)
    assert obj.property("maxHeight") == 240


def test_dropdown_list_has_item_selected_signal(engine):
    obj = load_component(engine, "components/DropdownList.qml")
    received = []
    obj.itemSelected.connect(lambda id, name: received.append((id, name)))
    assert isinstance(received, list)


def test_dropdown_list_color_is_surface(theme_qml_engine):
    from PySide6.QtGui import QColor
    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/DropdownList.qml")
    assert obj.property("color") == QColor(active_theme.surface)


def test_dropdown_list_border_color_is_border_token(theme_qml_engine):
    from PySide6.QtGui import QColor
    active_theme = register_theme_singleton(ThemeManager())
    obj = load_component(theme_qml_engine, "components/DropdownList.qml")
    assert obj.property("borderColor") == QColor(active_theme.border)
