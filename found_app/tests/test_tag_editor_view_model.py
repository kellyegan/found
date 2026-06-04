"""Tests for TagEditorViewModel — Commit 11."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from found_app.tag_editor.tag_editor_view_model import TagEditorViewModel
from found_app.selection.selection_manager import SelectionManager


SAMPLE_TAGS = [
    {"id": "tag-1", "name": "architecture"},
    {"id": "tag-2", "name": "nature"},
]


def _vm(
    fetcher=None,
    modifier=None,
    tag_creator=None,
    selection_manager=None,
):
    return TagEditorViewModel(
        image_tags_fetcher=fetcher or (lambda image_id: list(SAMPLE_TAGS)),
        tag_modifier=modifier or (lambda image_ids, add_ids, remove_ids: True),
        tag_creator=tag_creator,
        selection_manager=selection_manager,
    )


def _wait_for_state(vm, target: str, timeout_ms: int = 2000) -> None:
    if vm.loadingState == target:
        return
    loop = QEventLoop()

    def check(name: str):
        if name == target:
            loop.quit()

    vm.loadingStateChanged.connect(check)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


def _spin(ms: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _load(vm, image_id="img-1"):
    vm.loadImage(image_id)
    _wait_for_state(vm, "Ready")
    _spin()


def _load_error(vm, image_id="img-1"):
    vm.loadImage(image_id)
    _wait_for_state(vm, "Error")
    _spin()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_tags_default_to_empty(qapp):
    assert _vm().tags == []


def test_loading_state_defaults_to_idle(qapp):
    assert _vm().loadingState == "Idle"


def test_selection_mode_defaults_to_none(qapp):
    assert _vm().selectionMode == "none"


# ---------------------------------------------------------------------------
# loadImage — success
# ---------------------------------------------------------------------------

def test_load_image_populates_tags(qapp):
    vm = _vm()
    _load(vm)
    assert len(vm.tags) == 2


def test_load_image_sets_state_to_ready(qapp):
    vm = _vm()
    _load(vm)
    assert vm.loadingState == "Ready"


def test_load_image_emits_tags_changed(qapp):
    vm = _vm()
    received = []
    vm.tagsChanged.connect(lambda: received.append(1))
    _load(vm)
    assert len(received) >= 1


def test_load_image_passes_correct_id_to_fetcher(qapp):
    fetched = []
    vm = _vm(fetcher=lambda iid: fetched.append(iid) or SAMPLE_TAGS)
    _load(vm, "img-abc")
    assert fetched == ["img-abc"]


# ---------------------------------------------------------------------------
# loadImage — error cases
# ---------------------------------------------------------------------------

def test_load_image_sets_state_to_error_on_none(qapp):
    vm = _vm(fetcher=lambda iid: None)
    _load_error(vm)
    assert vm.loadingState == "Error"


def test_load_image_sets_state_to_error_on_exception(qapp):
    def bad(iid): raise RuntimeError("fail")
    vm = _vm(fetcher=bad)
    _load_error(vm)
    assert vm.loadingState == "Error"


def test_load_image_error_leaves_tags_empty(qapp):
    vm = _vm(fetcher=lambda iid: None)
    _load_error(vm)
    assert vm.tags == []


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

def test_clear_resets_tags(qapp):
    vm = _vm()
    _load(vm)
    assert len(vm.tags) == 2
    vm.clear()
    assert vm.tags == []


def test_clear_sets_state_to_idle(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.loadingState == "Idle"


def test_clear_emits_tags_changed(qapp):
    vm = _vm()
    _load(vm)
    received = []
    vm.tagsChanged.connect(lambda: received.append(1))
    vm.clear()
    assert len(received) == 1


# ---------------------------------------------------------------------------
# addTag — single mode (no selection_manager, primary_id set via loadImage)
# ---------------------------------------------------------------------------

def test_add_tag_calls_modifier_with_correct_args(qapp):
    calls = []
    def modifier(image_ids, add_ids, remove_ids):
        calls.append((image_ids, add_ids, remove_ids))
        return True
    vm = _vm(modifier=modifier)
    _load(vm, "img-1")
    vm.addTag("tag-3", "urban")
    _spin()
    assert len(calls) == 1
    assert "img-1" in calls[0][0]
    assert "tag-3" in calls[0][1]
    assert calls[0][2] == []


def test_add_tag_updates_local_tags_on_success(qapp):
    vm = _vm()
    _load(vm)
    initial_count = len(vm.tags)
    vm.addTag("tag-3", "urban")
    _spin()
    assert len(vm.tags) == initial_count + 1


def test_add_tag_does_not_duplicate_existing_tag(qapp):
    vm = _vm()
    _load(vm)
    initial_count = len(vm.tags)
    vm.addTag("tag-1", "architecture")  # tag-1 already in SAMPLE_TAGS
    _spin()
    assert len(vm.tags) == initial_count


def test_add_tag_emits_tags_changed_on_success(qapp):
    vm = _vm()
    _load(vm)
    received = []
    vm.tagsChanged.connect(lambda: received.append(1))
    vm.addTag("tag-3", "urban")
    _spin()
    assert len(received) >= 1


def test_add_tag_does_not_update_local_tags_on_failure(qapp):
    vm = _vm(modifier=lambda *a: False)
    _load(vm)
    initial_count = len(vm.tags)
    vm.addTag("tag-3", "urban")
    _spin()
    assert len(vm.tags) == initial_count


# ---------------------------------------------------------------------------
# removeTag — single mode
# ---------------------------------------------------------------------------

def test_remove_tag_calls_modifier_with_correct_args(qapp):
    calls = []
    def modifier(image_ids, add_ids, remove_ids):
        calls.append((image_ids, add_ids, remove_ids))
        return True
    vm = _vm(modifier=modifier)
    _load(vm, "img-1")
    vm.removeTag("tag-1")
    _spin()
    assert len(calls) == 1
    assert "img-1" in calls[0][0]
    assert calls[0][1] == []
    assert "tag-1" in calls[0][2]


def test_remove_tag_removes_from_local_tags_on_success(qapp):
    vm = _vm()
    _load(vm)
    assert any(t["id"] == "tag-1" for t in vm.tags)
    vm.removeTag("tag-1")
    _spin()
    assert not any(t["id"] == "tag-1" for t in vm.tags)


def test_remove_tag_does_not_remove_on_failure(qapp):
    vm = _vm(modifier=lambda *a: False)
    _load(vm)
    initial_count = len(vm.tags)
    vm.removeTag("tag-1")
    _spin()
    assert len(vm.tags) == initial_count


def test_remove_tag_emits_tags_changed_on_success(qapp):
    vm = _vm()
    _load(vm)
    received = []
    vm.tagsChanged.connect(lambda: received.append(1))
    vm.removeTag("tag-1")
    _spin()
    assert len(received) >= 1


# ---------------------------------------------------------------------------
# removeTag — no-op when no primary_id
# ---------------------------------------------------------------------------

def test_remove_tag_is_noop_without_primary_id(qapp):
    calls = []
    vm = _vm(modifier=lambda *a: calls.append(1) or True)
    vm.removeTag("tag-1")
    _spin()
    assert calls == []


# ---------------------------------------------------------------------------
# SelectionManager integration
# ---------------------------------------------------------------------------

def test_single_selection_loads_tags(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _wait_for_state(vm, "Ready")
    _spin()
    assert vm.loadingState == "Ready"
    assert len(vm.tags) == 2


def test_single_selection_sets_mode_to_single(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _spin()
    assert vm.selectionMode == "single"


def test_multiple_selection_clears_tags(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _wait_for_state(vm, "Ready")
    _spin()
    assert len(vm.tags) > 0
    sel.toggle("img-2")
    _spin()
    assert vm.tags == []


def test_multiple_selection_sets_mode_to_multi(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _spin()
    sel.toggle("img-2")
    _spin()
    assert vm.selectionMode == "multi"


def test_clear_selection_sets_mode_to_none(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _spin()
    sel.clear()
    _spin()
    assert vm.selectionMode == "none"


def test_clear_selection_clears_tags(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _wait_for_state(vm, "Ready")
    _spin()
    sel.clear()
    _spin()
    assert vm.tags == []


def test_selection_mode_emits_signal_on_change(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    received = []
    vm.selectionModeChanged.connect(lambda mode: received.append(mode))
    sel.select("img-1")
    _spin()
    assert "single" in received


def test_add_tag_with_selection_manager_uses_all_selected_ids(qapp):
    calls = []
    def modifier(image_ids, add_ids, remove_ids):
        calls.append((list(image_ids), add_ids, remove_ids))
        return True
    sel = SelectionManager()
    vm = _vm(modifier=modifier, selection_manager=sel)
    sel.select("img-1")
    sel.toggle("img-2")
    _spin()
    vm.addTag("tag-3", "urban")
    _spin()
    assert len(calls) == 1
    assert set(calls[0][0]) == {"img-1", "img-2"}
    assert "tag-3" in calls[0][1]


def test_remove_tag_uses_primary_id_only(qapp):
    calls = []
    def modifier(image_ids, add_ids, remove_ids):
        calls.append((list(image_ids), add_ids, remove_ids))
        return True
    sel = SelectionManager()
    vm = _vm(modifier=modifier, selection_manager=sel)
    sel.select("img-1")
    _wait_for_state(vm, "Ready")
    _spin()
    vm.removeTag("tag-1")
    _spin()
    assert len(calls) == 1
    assert calls[0][0] == ["img-1"]
    assert "tag-1" in calls[0][2]


# ---------------------------------------------------------------------------
# addTagByName — find-or-create
# ---------------------------------------------------------------------------

def test_add_tag_by_name_calls_creator(qapp):
    received = []
    vm = _vm(tag_creator=lambda name: received.append(name) or {"id": "tag-new", "name": name})
    _load(vm, "img-1")
    vm.addTagByName("urban")
    _spin()
    assert received == ["urban"]


def test_add_tag_by_name_lowercases_and_strips(qapp):
    received = []
    vm = _vm(tag_creator=lambda name: received.append(name) or {"id": "tag-new", "name": name})
    _load(vm, "img-1")
    vm.addTagByName("  Urban  ")
    _spin()
    assert received == ["urban"]


def test_add_tag_by_name_adds_to_local_tags_on_success(qapp):
    vm = _vm(tag_creator=lambda name: {"id": "tag-new", "name": name})
    _load(vm)
    initial_count = len(vm.tags)
    vm.addTagByName("urban")
    _spin()
    assert len(vm.tags) == initial_count + 1
    assert any(t["name"] == "urban" for t in vm.tags)


def test_add_tag_by_name_calls_modifier_with_new_tag_id(qapp):
    calls = []
    def modifier(image_ids, add_ids, remove_ids):
        calls.append((image_ids, add_ids, remove_ids))
        return True
    vm = _vm(
        modifier=modifier,
        tag_creator=lambda name: {"id": "tag-new", "name": name},
    )
    _load(vm, "img-1")
    vm.addTagByName("urban")
    _spin()
    assert len(calls) == 1
    assert "tag-new" in calls[0][1]
    assert "img-1" in calls[0][0]


def test_add_tag_by_name_noop_if_no_creator(qapp):
    calls = []
    vm = _vm(modifier=lambda *a: calls.append(1) or True)
    _load(vm, "img-1")
    vm.addTagByName("urban")
    _spin()
    assert calls == []


def test_add_tag_by_name_noop_on_creator_returning_none(qapp):
    vm = _vm(tag_creator=lambda name: None)
    _load(vm)
    initial_count = len(vm.tags)
    vm.addTagByName("urban")
    _spin()
    assert len(vm.tags) == initial_count


def test_add_tag_by_name_noop_on_empty_string(qapp):
    calls = []
    vm = _vm(tag_creator=lambda name: calls.append(name) or {"id": "x", "name": name})
    vm.addTagByName("   ")
    _spin()
    assert calls == []


def test_add_tag_by_name_emits_tags_changed_on_success(qapp):
    vm = _vm(tag_creator=lambda name: {"id": "tag-new", "name": name})
    _load(vm)
    received = []
    vm.tagsChanged.connect(lambda: received.append(1))
    vm.addTagByName("urban")
    _spin()
    assert len(received) >= 1


# ---------------------------------------------------------------------------
# modified signal
# ---------------------------------------------------------------------------

def _collect_signal(signal):
    received = []
    signal.connect(lambda: received.append(1))
    return received


def test_modified_emitted_on_add_tag_success(qapp):
    vm = _vm()
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.addTag("tag-3", "urban")
    _spin()
    assert len(received) >= 1


def test_modified_not_emitted_on_add_tag_failure(qapp):
    vm = _vm(modifier=lambda *_: False)
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.addTag("tag-3", "urban")
    _spin()
    assert received == []


def test_modified_emitted_on_remove_tag_success(qapp):
    vm = _vm()
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.removeTag("tag-1")
    _spin()
    assert len(received) >= 1


def test_modified_not_emitted_on_remove_tag_failure(qapp):
    vm = _vm(modifier=lambda *_: False)
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.removeTag("tag-1")
    _spin()
    assert received == []


def test_modified_not_emitted_on_load(qapp):
    vm = _vm()
    received = _collect_signal(vm.modified)
    _load(vm)
    assert received == []
