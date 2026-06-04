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
from found_app.services.navigation import NavigationManager


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


# ---------------------------------------------------------------------------
# goNext() / goPrev()
# ---------------------------------------------------------------------------

CONTEXT = ["img-a", "img-b", "img-c", "img-d"]


def _nm_image(image_id="img-b"):
    nm = NavigationManager()
    nm.push("image", {"image_id": image_id, "context_ids": CONTEXT})
    return nm


def test_has_next_true_when_not_at_end(qapp):
    assert _nm_image("img-b").hasNext is True


def test_has_next_false_at_last_item(qapp):
    assert _nm_image("img-d").hasNext is False


def test_has_prev_true_when_not_at_start(qapp):
    assert _nm_image("img-b").hasPrev is True


def test_has_prev_false_at_first_item(qapp):
    assert _nm_image("img-a").hasPrev is False


def test_go_next_advances_image_id(qapp):
    nm = _nm_image("img-b")
    nm.goNext()
    assert nm.currentEntry["image_id"] == "img-c"


def test_go_prev_retreats_image_id(qapp):
    nm = _nm_image("img-c")
    nm.goPrev()
    assert nm.currentEntry["image_id"] == "img-b"


def test_go_next_noop_at_last(qapp):
    nm = _nm_image("img-d")
    nm.goNext()
    assert nm.currentEntry["image_id"] == "img-d"


def test_go_prev_noop_at_first(qapp):
    nm = _nm_image("img-a")
    nm.goPrev()
    assert nm.currentEntry["image_id"] == "img-a"


def test_go_next_does_not_push(qapp):
    nm = _nm_image("img-b")
    stack_len_before = len(nm._stack)
    nm.goNext()
    assert len(nm._stack) == stack_len_before


def test_go_next_emits_navigation_changed(qapp):
    nm = _nm_image("img-b")
    received = []
    nm.navigationChanged.connect(lambda: received.append(1))
    nm.goNext()
    assert received


def test_go_next_updates_has_next_has_prev(qapp):
    nm = _nm_image("img-a")
    assert nm.hasPrev is False
    nm.goNext()
    assert nm.hasPrev is True


def test_go_next_when_no_context_is_noop(qapp):
    nm = NavigationManager()
    nm.push("image", {"image_id": "img-x"})
    nm.goNext()  # no context_ids — should not raise
    assert nm.currentEntry["image_id"] == "img-x"


def test_has_next_has_prev_false_outside_image_view(qapp):
    nm = NavigationManager()
    assert nm.hasNext is False
    assert nm.hasPrev is False


# ---------------------------------------------------------------------------
# immersiveMode / toggleImmersive()
# ---------------------------------------------------------------------------


def test_immersive_mode_defaults_to_false(qapp):
    assert NavigationManager().immersiveMode is False


def test_toggle_immersive_enables(qapp):
    nm = NavigationManager()
    nm.toggleImmersive()
    assert nm.immersiveMode is True


def test_toggle_immersive_disables(qapp):
    nm = NavigationManager()
    nm.toggleImmersive()
    nm.toggleImmersive()
    assert nm.immersiveMode is False


def test_set_immersive_true(qapp):
    nm = NavigationManager()
    nm.setImmersive(True)
    assert nm.immersiveMode is True


def test_set_immersive_false(qapp):
    nm = NavigationManager()
    nm.toggleImmersive()
    nm.setImmersive(False)
    assert nm.immersiveMode is False


def test_immersive_clears_on_go_back(qapp):
    nm = NavigationManager()
    nm.push("image", {"image_id": "img-1"})
    nm.toggleImmersive()
    nm.goBack()
    assert nm.immersiveMode is False


def test_immersive_changed_fires_on_toggle(qapp):
    nm = NavigationManager()
    received = []
    nm.navigationChanged.connect(lambda: received.append(1))
    nm.toggleImmersive()
    assert received
