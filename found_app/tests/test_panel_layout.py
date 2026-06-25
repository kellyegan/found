"""
Tests for PanelLayoutManager.

Covers:
- Default edge assignments and order when settings=None
- edges, order, openPanels properties return correct values
- tabIndex derivable from order filtered by edge
- setLayout moves panel to new edge at correct side-index
- setLayout with sideIndex past end of peers appends to that side
- setLayout on an open panel moving sides: stays open, displaces other side
- setLayout on a closed panel moving sides: target side open state unchanged
- setLayout reorder within same side: open state unchanged
- Signal emission rules for layoutChanged and openStateChanged
- togglePanel opens/closes panels with mutual exclusion on a side
- saveViewState / restoreViewState round-trip with available-panel filtering
- Edge and order persist across instances backed by the same AppSettings
- Open state is NOT persisted
"""

import pytest
from PySide6.QtCore import QSettings

from found_app.core.app_settings import AppSettings
from found_app.services.panel_layout import PanelLayoutManager


def _make_settings(tmp_path):
    return AppSettings(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))


def _tab_index(plm: PanelLayoutManager, panel_id: str) -> int:
    """Compute tabIndex in Python the same way QML would from order + edges."""
    edge = plm.edges[panel_id]
    peers = [p for p in plm.order if plm.edges[p] == edge]
    return peers.index(panel_id)


# ---------------------------------------------------------------------------
# Defaults (settings=None)
# ---------------------------------------------------------------------------


def test_default_collections_edge_is_left(qapp):
    plm = PanelLayoutManager()
    assert plm.edges["collections"] == "left"


def test_default_metadata_edge_is_right(qapp):
    plm = PanelLayoutManager()
    assert plm.edges["metadata"] == "right"


def test_default_order(qapp):
    plm = PanelLayoutManager()
    assert plm.order == ["collections", "metadata"]


def test_default_open_panels_all_empty(qapp):
    plm = PanelLayoutManager()
    assert plm.openPanels == {"left": "", "right": ""}


# ---------------------------------------------------------------------------
# tabIndex derivable from order + edges
# ---------------------------------------------------------------------------


def test_tab_index_collections_is_zero_on_left(qapp):
    plm = PanelLayoutManager()
    assert _tab_index(plm, "collections") == 0


def test_tab_index_metadata_is_zero_on_right(qapp):
    # metadata is the sole panel on the right — index 0 within its side
    plm = PanelLayoutManager()
    assert _tab_index(plm, "metadata") == 0


def test_tab_index_reflects_side_stack_not_global_position(qapp):
    # Move metadata to left at index 1; both on left now.
    # collections is index 0 on left, metadata is index 1 on left.
    plm = PanelLayoutManager()
    plm.setLayout("metadata", "left", 1)
    assert _tab_index(plm, "collections") == 0
    assert _tab_index(plm, "metadata") == 1


# ---------------------------------------------------------------------------
# setLayout — move to new edge
# ---------------------------------------------------------------------------


def test_set_layout_changes_panel_edge(qapp):
    plm = PanelLayoutManager()
    plm.setLayout("collections", "right", 0)
    assert plm.edges["collections"] == "right"


def test_set_layout_side_index_zero_inserts_before_existing_peer(qapp):
    plm = PanelLayoutManager()
    plm.setLayout("collections", "right", 0)
    assert _tab_index(plm, "collections") == 0
    assert _tab_index(plm, "metadata") == 1


def test_set_layout_side_index_one_inserts_after_existing_peer(qapp):
    plm = PanelLayoutManager()
    plm.setLayout("collections", "right", 1)
    assert _tab_index(plm, "metadata") == 0
    assert _tab_index(plm, "collections") == 1


def test_set_layout_side_index_past_end_appends(qapp):
    plm = PanelLayoutManager()
    plm.setLayout("collections", "right", 99)
    assert _tab_index(plm, "metadata") == 0
    assert _tab_index(plm, "collections") == 1


# ---------------------------------------------------------------------------
# setLayout — open state when moving sides
# ---------------------------------------------------------------------------


def test_set_layout_open_panel_stays_open_on_new_side(qapp):
    plm = PanelLayoutManager()
    plm.togglePanel("collections")
    plm.setLayout("collections", "right", 0)
    assert plm.openPanels["right"] == "collections"
    assert plm.openPanels["left"] == ""


def test_set_layout_open_panel_displaces_open_panel_on_target_side(qapp):
    plm = PanelLayoutManager()
    plm.togglePanel("collections")
    plm.togglePanel("metadata")
    plm.setLayout("collections", "right", 0)
    assert plm.openPanels["right"] == "collections"


def test_set_layout_closed_panel_moving_sides_leaves_target_open_state_unchanged(qapp):
    plm = PanelLayoutManager()
    plm.togglePanel("metadata")
    plm.setLayout("collections", "right", 0)  # collections is closed
    assert plm.openPanels["right"] == "metadata"


def test_set_layout_reorder_same_side_leaves_open_state_unchanged(qapp):
    plm = PanelLayoutManager()
    plm.setLayout("metadata", "left", 1)
    plm.togglePanel("collections")
    plm.setLayout("metadata", "left", 0)  # reorder within left
    assert plm.openPanels["left"] == "collections"


# ---------------------------------------------------------------------------
# setLayout — signal emission
# ---------------------------------------------------------------------------


def test_set_layout_emits_layout_changed(qapp):
    plm = PanelLayoutManager()
    received = []
    plm.layoutChanged.connect(lambda: received.append(1))
    plm.setLayout("collections", "right", 0)
    assert len(received) == 1


def test_set_layout_open_panel_moving_sides_emits_open_state_changed(qapp):
    plm = PanelLayoutManager()
    plm.togglePanel("collections")
    signals = []
    plm.openStateChanged.connect(lambda: signals.append(1))
    plm.setLayout("collections", "right", 0)
    assert len(signals) == 1


def test_set_layout_closed_panel_moving_sides_does_not_emit_open_state_changed(qapp):
    plm = PanelLayoutManager()
    signals = []
    plm.openStateChanged.connect(lambda: signals.append(1))
    plm.setLayout("collections", "right", 0)
    assert len(signals) == 0


def test_set_layout_reorder_same_side_does_not_emit_open_state_changed(qapp):
    plm = PanelLayoutManager()
    plm.setLayout("metadata", "left", 1)
    signals = []
    plm.openStateChanged.connect(lambda: signals.append(1))
    plm.setLayout("metadata", "left", 0)
    assert len(signals) == 0


# ---------------------------------------------------------------------------
# togglePanel
# ---------------------------------------------------------------------------


def test_toggle_panel_opens_closed_panel(qapp):
    plm = PanelLayoutManager()
    plm.togglePanel("collections")
    assert plm.openPanels["left"] == "collections"


def test_toggle_panel_closes_open_panel(qapp):
    plm = PanelLayoutManager()
    plm.togglePanel("collections")
    plm.togglePanel("collections")
    assert plm.openPanels["left"] == ""


def test_toggle_panel_opening_second_on_same_side_closes_first(qapp):
    plm = PanelLayoutManager()
    plm.setLayout("metadata", "left", 1)
    plm.togglePanel("collections")
    plm.togglePanel("metadata")
    assert plm.openPanels["left"] == "metadata"


def test_toggle_panel_emits_open_state_changed(qapp):
    plm = PanelLayoutManager()
    signals = []
    plm.openStateChanged.connect(lambda: signals.append(1))
    plm.togglePanel("collections")
    assert len(signals) == 1


# ---------------------------------------------------------------------------
# saveViewState / restoreViewState
# ---------------------------------------------------------------------------


def test_restore_view_state_reopens_saved_panel(qapp):
    plm = PanelLayoutManager()
    plm.togglePanel("collections")
    plm.saveViewState("library")
    plm.togglePanel("collections")  # close it
    plm.restoreViewState("library", ["collections", "metadata"])
    assert plm.openPanels["left"] == "collections"


def test_restore_view_state_filters_unavailable_panels(qapp):
    plm = PanelLayoutManager()
    plm.togglePanel("collections")
    plm.saveViewState("library")
    plm.togglePanel("collections")
    plm.restoreViewState("library", ["metadata"])  # collections not available
    assert plm.openPanels["left"] == ""


def test_restore_unknown_view_does_not_crash_and_closes_all(qapp):
    plm = PanelLayoutManager()
    plm.togglePanel("metadata")
    plm.restoreViewState("nonexistent_view", ["collections", "metadata"])
    assert plm.openPanels == {"left": "", "right": ""}


# ---------------------------------------------------------------------------
# Persistence via AppSettings
# ---------------------------------------------------------------------------


def test_edge_persists_across_instances(qapp, tmp_path):
    settings = _make_settings(tmp_path)
    plm1 = PanelLayoutManager(settings=settings)
    plm1.setLayout("collections", "right", 0)

    plm2 = PanelLayoutManager(settings=settings)
    assert plm2.edges["collections"] == "right"


def test_order_persists_across_instances(qapp, tmp_path):
    settings = _make_settings(tmp_path)
    plm1 = PanelLayoutManager(settings=settings)
    plm1.setLayout("collections", "right", 1)

    plm2 = PanelLayoutManager(settings=settings)
    assert plm2.order == plm1.order


def test_open_state_not_persisted(qapp, tmp_path):
    settings = _make_settings(tmp_path)
    plm1 = PanelLayoutManager(settings=settings)
    plm1.togglePanel("collections")

    plm2 = PanelLayoutManager(settings=settings)
    assert plm2.openPanels == {"left": "", "right": ""}


def test_no_settings_mode_does_not_crash(qapp):
    plm = PanelLayoutManager(settings=None)
    plm.setLayout("collections", "right", 0)
    plm.togglePanel("metadata")
    assert plm.edges["collections"] == "right"
