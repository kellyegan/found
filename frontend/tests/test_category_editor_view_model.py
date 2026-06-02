"""Tests for CategoryEditorViewModel."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from frontend.category_editor.category_editor_view_model import CategoryEditorViewModel
from frontend.selection.selection_manager import SelectionManager


SAMPLE_CATEGORIES = [
    {"id": "cat-1", "name": "Architecture"},
    {"id": "cat-2", "name": "Nature"},
]


def _vm(fetcher=None, modifier=None, selection_manager=None):
    return CategoryEditorViewModel(
        image_categories_fetcher=fetcher or (lambda image_id: list(SAMPLE_CATEGORIES)),
        category_modifier=modifier or (lambda image_ids, add_ids, remove_ids: True),
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


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_categories_default_to_empty(qapp):
    assert _vm().categories == []


def test_loading_state_defaults_to_idle(qapp):
    assert _vm().loadingState == "Idle"


def test_selection_mode_defaults_to_none(qapp):
    assert _vm().selectionMode == "none"


# ---------------------------------------------------------------------------
# loadImage
# ---------------------------------------------------------------------------

def test_load_image_populates_categories(qapp):
    vm = _vm()
    _load(vm)
    assert len(vm.categories) == 2


def test_load_image_sets_ready_state(qapp):
    vm = _vm()
    _load(vm)
    assert vm.loadingState == "Ready"


def test_load_image_error_sets_error_state(qapp):
    vm = _vm(fetcher=lambda _: None)
    vm.loadImage("img-1")
    _wait_for_state(vm, "Error")
    assert vm.loadingState == "Error"


# ---------------------------------------------------------------------------
# addCategory
# ---------------------------------------------------------------------------

def test_add_category_appends_to_list(qapp):
    vm = _vm()
    _load(vm)
    vm.addCategory("cat-3", "Abstract")
    _spin()
    assert any(c["id"] == "cat-3" for c in vm.categories)


def test_add_category_calls_modifier(qapp):
    calls = []
    vm = _vm(modifier=lambda ids, add_ids, rem_ids: calls.append((ids, add_ids, rem_ids)) or True)
    _load(vm, "img-1")
    vm.addCategory("cat-3", "Abstract")
    _spin()
    assert any("cat-3" in c[1] for c in calls)


def test_add_category_not_duplicated(qapp):
    vm = _vm()
    _load(vm)
    vm.addCategory("cat-1", "Architecture")
    _spin()
    assert sum(1 for c in vm.categories if c["id"] == "cat-1") == 1


def test_add_category_not_added_on_modifier_failure(qapp):
    vm = _vm(modifier=lambda *_: False)
    _load(vm)
    initial = len(vm.categories)
    vm.addCategory("cat-3", "Abstract")
    _spin()
    assert len(vm.categories) == initial


# ---------------------------------------------------------------------------
# removeCategory
# ---------------------------------------------------------------------------

def test_remove_category_removes_from_list(qapp):
    vm = _vm()
    _load(vm)
    vm.removeCategory("cat-1")
    _spin()
    assert not any(c["id"] == "cat-1" for c in vm.categories)


def test_remove_category_calls_modifier(qapp):
    calls = []
    vm = _vm(modifier=lambda ids, add_ids, rem_ids: calls.append((ids, add_ids, rem_ids)) or True)
    _load(vm, "img-1")
    vm.removeCategory("cat-1")
    _spin()
    assert any("cat-1" in c[2] for c in calls)


def test_remove_category_not_removed_on_failure(qapp):
    vm = _vm(modifier=lambda *_: False)
    _load(vm)
    vm.removeCategory("cat-1")
    _spin()
    assert any(c["id"] == "cat-1" for c in vm.categories)


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

def test_clear_empties_categories(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.categories == []


def test_clear_sets_idle(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.loadingState == "Idle"


# ---------------------------------------------------------------------------
# SelectionManager integration
# ---------------------------------------------------------------------------

def test_single_selection_loads_categories(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _wait_for_state(vm, "Ready")
    assert len(vm.categories) == 2


def test_empty_selection_clears_categories(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _wait_for_state(vm, "Ready")
    sel.clear()
    _spin()
    assert vm.categories == []


def test_multi_selection_sets_multi_mode(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    sel.toggle("img-2")
    _spin()
    assert vm.selectionMode == "multi"


def test_add_category_uses_all_selected_ids_in_multi(qapp):
    calls = []
    sel = SelectionManager()
    vm = _vm(
        modifier=lambda ids, add_ids, rem_ids: calls.append(ids) or True,
        selection_manager=sel,
    )
    sel.select("img-1")
    sel.toggle("img-2")
    _spin()
    vm.addCategory("cat-3", "Abstract")
    _spin()
    assert len(calls) == 1
    assert set(calls[0]) == {"img-1", "img-2"}


# ---------------------------------------------------------------------------
# modified signal
# ---------------------------------------------------------------------------

def _collect_signal(signal):
    received = []
    signal.connect(lambda: received.append(1))
    return received


def test_modified_emitted_on_add_category_success(qapp):
    vm = _vm()
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.addCategory("cat-3", "Abstract")
    _spin()
    assert len(received) >= 1


def test_modified_not_emitted_on_add_category_failure(qapp):
    vm = _vm(modifier=lambda *_: False)
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.addCategory("cat-3", "Abstract")
    _spin()
    assert received == []


def test_modified_emitted_on_remove_category_success(qapp):
    vm = _vm()
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.removeCategory("cat-1")
    _spin()
    assert len(received) >= 1


def test_modified_not_emitted_on_remove_category_failure(qapp):
    vm = _vm(modifier=lambda *_: False)
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.removeCategory("cat-1")
    _spin()
    assert received == []


def test_modified_not_emitted_on_load(qapp):
    vm = _vm()
    received = _collect_signal(vm.modified)
    _load(vm)
    assert received == []
