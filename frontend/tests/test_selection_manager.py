"""
Tests for SelectionManager — Commit 1.

Covers:
- Initial state: empty selection, empty primaryId
- select() sets single selection and becomes primary/anchor
- select() replaces previous selection
- toggle() adds an unselected image to selection
- toggle() removes an already-selected image
- toggle() deselects when the only selected image is toggled
- extendTo() selects a range from anchor to target
- extendTo() works in reverse (target before anchor)
- extendTo() falls back to select() when no anchor exists
- selectAll() selects every supplied ID
- clear() empties selection and primaryId
- isSelected() returns True/False correctly
- selectionCount reflects current set size
- selectionRevision increments on every mutation
- selectionChanged signal fires on every mutation
- requestOpen() emits openRequested signal with the image_id
"""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from frontend.selection.selection_manager import SelectionManager


IDS = ["a", "b", "c", "d", "e"]


def _sm():
    return SelectionManager()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_initial_selection_count_is_zero(qapp):
    assert _sm().selectionCount == 0


def test_initial_primary_id_is_empty(qapp):
    assert _sm().primaryId == ""


def test_initial_is_selected_returns_false(qapp):
    assert _sm().isSelected("a") is False


# ---------------------------------------------------------------------------
# select()
# ---------------------------------------------------------------------------


def test_select_adds_image_to_selection(qapp):
    sm = _sm()
    sm.select("a")
    assert sm.isSelected("a") is True


def test_select_sets_selection_count_to_one(qapp):
    sm = _sm()
    sm.select("a")
    assert sm.selectionCount == 1


def test_select_sets_primary_id(qapp):
    sm = _sm()
    sm.select("b")
    assert sm.primaryId == "b"


def test_select_replaces_previous_selection(qapp):
    sm = _sm()
    sm.select("a")
    sm.select("b")
    assert not sm.isSelected("a")
    assert sm.isSelected("b")
    assert sm.selectionCount == 1


# ---------------------------------------------------------------------------
# toggle()
# ---------------------------------------------------------------------------


def test_toggle_adds_unselected_image(qapp):
    sm = _sm()
    sm.select("a")
    sm.toggle("b")
    assert sm.isSelected("a")
    assert sm.isSelected("b")
    assert sm.selectionCount == 2


def test_toggle_removes_selected_image(qapp):
    sm = _sm()
    sm.select("a")
    sm.toggle("b")
    sm.toggle("b")
    assert not sm.isSelected("b")
    assert sm.selectionCount == 1


def test_toggle_deselects_when_only_item(qapp):
    sm = _sm()
    sm.select("a")
    sm.toggle("a")
    assert sm.selectionCount == 0
    assert sm.primaryId == ""


# ---------------------------------------------------------------------------
# extendTo()
# ---------------------------------------------------------------------------


def test_extend_to_selects_forward_range(qapp):
    sm = _sm()
    sm.select("b")
    sm.extendTo("d", IDS)
    assert sm.isSelected("b")
    assert sm.isSelected("c")
    assert sm.isSelected("d")
    assert not sm.isSelected("a")
    assert not sm.isSelected("e")


def test_extend_to_selects_backward_range(qapp):
    sm = _sm()
    sm.select("d")
    sm.extendTo("b", IDS)
    assert sm.isSelected("b")
    assert sm.isSelected("c")
    assert sm.isSelected("d")
    assert not sm.isSelected("a")
    assert not sm.isSelected("e")


def test_extend_to_same_item_selects_one(qapp):
    sm = _sm()
    sm.select("c")
    sm.extendTo("c", IDS)
    assert sm.selectionCount == 1
    assert sm.isSelected("c")


def test_extend_to_without_anchor_falls_back_to_select(qapp):
    sm = _sm()
    sm.extendTo("b", IDS)
    assert sm.selectionCount == 1
    assert sm.isSelected("b")


def test_extend_to_anchor_stays_fixed_on_second_extend(qapp):
    sm = _sm()
    sm.select("b")
    sm.extendTo("d", IDS)
    sm.extendTo("e", IDS)
    # anchor is still "b", so range is b→e
    assert sm.isSelected("b")
    assert sm.isSelected("e")
    assert not sm.isSelected("a")


# ---------------------------------------------------------------------------
# selectAll()
# ---------------------------------------------------------------------------


def test_select_all_selects_every_id(qapp):
    sm = _sm()
    sm.selectAll(IDS)
    assert all(sm.isSelected(i) for i in IDS)
    assert sm.selectionCount == len(IDS)


def test_select_all_empty_list_clears(qapp):
    sm = _sm()
    sm.select("a")
    sm.selectAll([])
    assert sm.selectionCount == 0


# ---------------------------------------------------------------------------
# clear()
# ---------------------------------------------------------------------------


def test_clear_empties_selection(qapp):
    sm = _sm()
    sm.selectAll(IDS)
    sm.clear()
    assert sm.selectionCount == 0


def test_clear_resets_primary_id(qapp):
    sm = _sm()
    sm.select("a")
    sm.clear()
    assert sm.primaryId == ""


def test_clear_makes_is_selected_return_false(qapp):
    sm = _sm()
    sm.select("a")
    sm.clear()
    assert not sm.isSelected("a")


# ---------------------------------------------------------------------------
# selectionRevision & selectionChanged signal
# ---------------------------------------------------------------------------


def test_selection_revision_increments_on_select(qapp):
    sm = _sm()
    rev = sm.selectionRevision
    sm.select("a")
    assert sm.selectionRevision == rev + 1


def test_selection_revision_increments_on_clear(qapp):
    sm = _sm()
    sm.select("a")
    rev = sm.selectionRevision
    sm.clear()
    assert sm.selectionRevision == rev + 1


def test_selection_changed_fires_on_select(qapp):
    sm = _sm()
    received = []
    sm.selectionChanged.connect(lambda: received.append(1))
    sm.select("a")
    assert received


def test_selection_changed_fires_on_clear(qapp):
    sm = _sm()
    sm.select("a")
    received = []
    sm.selectionChanged.connect(lambda: received.append(1))
    sm.clear()
    assert received


def test_selection_changed_fires_on_toggle(qapp):
    sm = _sm()
    received = []
    sm.selectionChanged.connect(lambda: received.append(1))
    sm.toggle("a")
    assert received


def test_selection_changed_fires_on_select_all(qapp):
    sm = _sm()
    received = []
    sm.selectionChanged.connect(lambda: received.append(1))
    sm.selectAll(IDS)
    assert received


# ---------------------------------------------------------------------------
# requestOpen / openRequested
# ---------------------------------------------------------------------------


def test_request_open_emits_open_requested(qapp):
    sm = _sm()
    received = []
    sm.openRequested.connect(received.append)
    sm.requestOpen("img-123")
    assert received == ["img-123"]


# ---------------------------------------------------------------------------
# restore()
# ---------------------------------------------------------------------------


def test_restore_sets_selection(qapp):
    sm = _sm()
    sm.restore(["a", "b"], "b", "a")
    assert sm.isSelected("a")
    assert sm.isSelected("b")
    assert sm.selectionCount == 2


def test_restore_sets_primary_id(qapp):
    sm = _sm()
    sm.restore(["a", "b"], "b", "a")
    assert sm.primaryId == "b"


def test_restore_clears_previous_selection(qapp):
    sm = _sm()
    sm.select("c")
    sm.restore(["a", "b"], "b", "a")
    assert not sm.isSelected("c")


def test_restore_fires_selection_changed(qapp):
    sm = _sm()
    received = []
    sm.selectionChanged.connect(lambda: received.append(1))
    sm.restore(["a"], "a", "a")
    assert received


def test_restore_empty_list_clears_selection(qapp):
    sm = _sm()
    sm.select("a")
    sm.restore([], "", "")
    assert sm.selectionCount == 0
    assert sm.primaryId == ""


# ---------------------------------------------------------------------------
# selectedIds / anchorId properties
# ---------------------------------------------------------------------------


def test_selected_ids_initially_empty(qapp):
    assert _sm().selectedIds == []


def test_selected_ids_contains_selected(qapp):
    sm = _sm()
    sm.select("a")
    assert "a" in sm.selectedIds
    assert len(sm.selectedIds) == 1


def test_selected_ids_reflects_multi_select(qapp):
    sm = _sm()
    sm.select("a")
    sm.toggle("b")
    assert set(sm.selectedIds) == {"a", "b"}


def test_selected_ids_empty_after_clear(qapp):
    sm = _sm()
    sm.select("a")
    sm.clear()
    assert sm.selectedIds == []


def test_anchor_id_initially_empty(qapp):
    assert _sm().anchorId == ""


def test_anchor_id_set_on_select(qapp):
    sm = _sm()
    sm.select("b")
    assert sm.anchorId == "b"


def test_anchor_id_set_on_toggle_add(qapp):
    sm = _sm()
    sm.select("a")
    sm.toggle("b")
    assert sm.anchorId == "b"


def test_anchor_id_unchanged_on_toggle_remove(qapp):
    sm = _sm()
    sm.select("a")
    sm.toggle("b")
    sm.toggle("b")  # remove b — anchor stays at b from the add
    assert sm.anchorId == "b"
