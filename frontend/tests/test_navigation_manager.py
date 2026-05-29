"""
Tests for NavigationManager — Slice 4 Commit 1.

Covers:
- Initial state: currentView is "library", canGoBack is False
- currentEntry contains the expected fields
- push() changes currentView and adds to the stack
- push() carries params into the new entry (image_id, collection_id)
- canGoBack is True after push()
- goBack() after one push restores previous view
- goBack() when stack is empty is a no-op
- canGoBack is False after popping the last entry
- Multiple pushes produce a stack in LIFO order
- goBack() restores the full entry state (selection, scroll)
- updateScrollX() mutates current entry without pushing
- push() saves current selection from SelectionManager snapshot
- push() saves current scrollX into the outgoing entry
- Navigating back restores the previous entry's selection_ids, primary_id, anchor_id
- NavigationManager emits navigationChanged on push
- NavigationManager emits navigationChanged on goBack
"""

import pytest
from frontend.navigation.navigation_manager import NavigationManager


def _nm():
    return NavigationManager()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_initial_current_view_is_library(qapp):
    assert _nm().currentView == "library"


def test_initial_can_go_back_is_false(qapp):
    assert _nm().canGoBack is False


def test_initial_entry_has_view_field(qapp):
    entry = _nm().currentEntry
    assert entry["view"] == "library"


def test_initial_entry_has_scroll_x_zero(qapp):
    entry = _nm().currentEntry
    assert entry["scroll_x"] == 0.0


def test_initial_entry_selection_ids_empty(qapp):
    entry = _nm().currentEntry
    assert entry["selection_ids"] == []


def test_initial_entry_primary_id_empty(qapp):
    entry = _nm().currentEntry
    assert entry["primary_id"] == ""


def test_initial_entry_anchor_id_empty(qapp):
    entry = _nm().currentEntry
    assert entry["anchor_id"] == ""


def test_initial_entry_collection_id_is_none(qapp):
    entry = _nm().currentEntry
    assert entry["collection_id"] is None


def test_initial_entry_image_id_is_none(qapp):
    entry = _nm().currentEntry
    assert entry["image_id"] is None


def test_initial_entry_context_ids_empty(qapp):
    entry = _nm().currentEntry
    assert entry["context_ids"] == []


# ---------------------------------------------------------------------------
# push()
# ---------------------------------------------------------------------------


def test_push_changes_current_view(qapp):
    nm = _nm()
    nm.push("image", {"image_id": "img-1"})
    assert nm.currentView == "image"


def test_push_sets_can_go_back(qapp):
    nm = _nm()
    nm.push("image", {"image_id": "img-1"})
    assert nm.canGoBack is True


def test_push_carries_image_id_into_entry(qapp):
    nm = _nm()
    nm.push("image", {"image_id": "img-42"})
    assert nm.currentEntry["image_id"] == "img-42"


def test_push_carries_collection_id_into_entry(qapp):
    nm = _nm()
    nm.push("collection", {"collection_id": "col-7"})
    assert nm.currentEntry["collection_id"] == "col-7"


def test_push_unknown_params_are_ignored(qapp):
    nm = _nm()
    nm.push("image", {"image_id": "x", "nonsense": 99})
    assert nm.currentEntry["image_id"] == "x"


def test_push_stacks_multiple_views(qapp):
    nm = _nm()
    nm.push("collection", {"collection_id": "col-1"})
    nm.push("image", {"image_id": "img-1"})
    assert nm.currentView == "image"
    assert nm.canGoBack is True


def test_push_carries_context_ids_into_entry(qapp):
    nm = _nm()
    ids = ["a", "b", "c"]
    nm.push("image", {"image_id": "b", "context_ids": ids})
    assert nm.currentEntry["context_ids"] == ids


def test_push_context_ids_default_empty(qapp):
    nm = _nm()
    nm.push("image", {"image_id": "x"})
    assert nm.currentEntry["context_ids"] == []


# ---------------------------------------------------------------------------
# goBack()
# ---------------------------------------------------------------------------


def test_go_back_restores_previous_view(qapp):
    nm = _nm()
    nm.push("image", {"image_id": "img-1"})
    nm.goBack()
    assert nm.currentView == "library"


def test_go_back_clears_can_go_back_when_stack_empty(qapp):
    nm = _nm()
    nm.push("image", {"image_id": "img-1"})
    nm.goBack()
    assert nm.canGoBack is False


def test_go_back_noop_when_stack_empty(qapp):
    nm = _nm()
    nm.goBack()  # should not raise
    assert nm.currentView == "library"


def test_go_back_lifo_ordering(qapp):
    nm = _nm()
    nm.push("collection", {"collection_id": "col-1"})
    nm.push("image", {"image_id": "img-1"})
    nm.goBack()
    assert nm.currentView == "collection"
    nm.goBack()
    assert nm.currentView == "library"


def test_go_back_restores_full_entry(qapp):
    nm = _nm()
    nm.updateScrollX(250.0)
    nm.saveSelection(["a", "b"], "b", "a")
    nm.push("image", {"image_id": "img-1"})
    nm.goBack()
    entry = nm.currentEntry
    assert entry["scroll_x"] == 250.0
    assert entry["selection_ids"] == ["a", "b"]
    assert entry["primary_id"] == "b"
    assert entry["anchor_id"] == "a"


# ---------------------------------------------------------------------------
# updateScrollX()
# ---------------------------------------------------------------------------


def test_update_scroll_x_mutates_current_entry(qapp):
    nm = _nm()
    nm.updateScrollX(123.5)
    assert nm.currentEntry["scroll_x"] == 123.5


def test_update_scroll_x_does_not_push(qapp):
    nm = _nm()
    nm.updateScrollX(99.0)
    assert nm.canGoBack is False


def test_update_scroll_x_preserved_after_push_and_back(qapp):
    nm = _nm()
    nm.updateScrollX(400.0)
    nm.push("image", {"image_id": "img-1"})
    nm.goBack()
    assert nm.currentEntry["scroll_x"] == 400.0


# ---------------------------------------------------------------------------
# saveSelection()
# ---------------------------------------------------------------------------


def test_save_selection_updates_current_entry(qapp):
    nm = _nm()
    nm.saveSelection(["x", "y"], "y", "x")
    entry = nm.currentEntry
    assert entry["selection_ids"] == ["x", "y"]
    assert entry["primary_id"] == "y"
    assert entry["anchor_id"] == "x"


def test_save_selection_does_not_push(qapp):
    nm = _nm()
    nm.saveSelection(["x"], "x", "x")
    assert nm.canGoBack is False


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


def test_navigation_changed_fires_on_push(qapp):
    nm = _nm()
    received = []
    nm.navigationChanged.connect(lambda: received.append(1))
    nm.push("image", {"image_id": "img-1"})
    assert received


def test_navigation_changed_fires_on_go_back(qapp):
    nm = _nm()
    nm.push("image", {"image_id": "img-1"})
    received = []
    nm.navigationChanged.connect(lambda: received.append(1))
    nm.goBack()
    assert received


def test_navigation_changed_does_not_fire_on_noop_go_back(qapp):
    nm = _nm()
    received = []
    nm.navigationChanged.connect(lambda: received.append(1))
    nm.goBack()
    assert not received
