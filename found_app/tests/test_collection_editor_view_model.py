"""Tests for CollectionEditorViewModel."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from found_app.viewmodels.collection_editor_view_model import CollectionEditorViewModel
from found_app.services.selection import SelectionManager


SAMPLE_COLLECTIONS = [
    {"id": "col-1", "name": "Favourites"},
    {"id": "col-2", "name": "Moodboard"},
]


def _vm(fetcher=None, adder=None, remover=None, selection_manager=None):
    return CollectionEditorViewModel(
        image_collections_fetcher=fetcher or (lambda image_id: list(SAMPLE_COLLECTIONS)),
        collection_adder=adder or (lambda collection_id, image_ids: True),
        collection_remover=remover or (lambda collection_id, image_id: True),
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

def test_collections_default_to_empty(qapp):
    assert _vm().collections == []


def test_loading_state_defaults_to_idle(qapp):
    assert _vm().loadingState == "Idle"


def test_selection_mode_defaults_to_none(qapp):
    assert _vm().selectionMode == "none"


# ---------------------------------------------------------------------------
# loadImage
# ---------------------------------------------------------------------------

def test_load_image_populates_collections(qapp):
    vm = _vm()
    _load(vm)
    assert len(vm.collections) == 2


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
# addToCollection
# ---------------------------------------------------------------------------

def test_add_to_collection_appends_to_list(qapp):
    vm = _vm()
    _load(vm)
    vm.addToCollection("col-3", "References")
    _spin()
    assert any(c["id"] == "col-3" for c in vm.collections)


def test_add_to_collection_calls_adder(qapp):
    calls = []
    vm = _vm(adder=lambda col_id, image_ids: calls.append((col_id, image_ids)) or True)
    _load(vm, "img-1")
    vm.addToCollection("col-3", "References")
    _spin()
    assert any(c[0] == "col-3" for c in calls)


def test_add_to_collection_not_duplicated(qapp):
    vm = _vm()
    _load(vm)
    vm.addToCollection("col-1", "Favourites")
    _spin()
    assert sum(1 for c in vm.collections if c["id"] == "col-1") == 1


def test_add_to_collection_not_added_on_adder_failure(qapp):
    vm = _vm(adder=lambda *_: False)
    _load(vm)
    initial = len(vm.collections)
    vm.addToCollection("col-3", "References")
    _spin()
    assert len(vm.collections) == initial


# ---------------------------------------------------------------------------
# removeFromCollection
# ---------------------------------------------------------------------------

def test_remove_from_collection_removes_from_list(qapp):
    vm = _vm()
    _load(vm)
    vm.removeFromCollection("col-1")
    _spin()
    assert not any(c["id"] == "col-1" for c in vm.collections)


def test_remove_from_collection_calls_remover(qapp):
    calls = []
    vm = _vm(remover=lambda col_id, image_id: calls.append((col_id, image_id)) or True)
    _load(vm, "img-1")
    vm.removeFromCollection("col-1")
    _spin()
    assert any(c[0] == "col-1" and c[1] == "img-1" for c in calls)


def test_remove_from_collection_not_removed_on_failure(qapp):
    vm = _vm(remover=lambda *_: False)
    _load(vm)
    vm.removeFromCollection("col-1")
    _spin()
    assert any(c["id"] == "col-1" for c in vm.collections)


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

def test_clear_empties_collections(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.collections == []


def test_clear_sets_idle(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.loadingState == "Idle"


# ---------------------------------------------------------------------------
# SelectionManager integration
# ---------------------------------------------------------------------------

def test_single_selection_loads_collections(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _wait_for_state(vm, "Ready")
    assert len(vm.collections) == 2


def test_empty_selection_clears_collections(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    _wait_for_state(vm, "Ready")
    sel.clear()
    _spin()
    assert vm.collections == []


def test_multi_selection_sets_multi_mode(qapp):
    sel = SelectionManager()
    vm = _vm(selection_manager=sel)
    sel.select("img-1")
    sel.toggle("img-2")
    _spin()
    assert vm.selectionMode == "multi"


def test_add_to_collection_uses_all_selected_in_multi(qapp):
    calls = []
    sel = SelectionManager()
    vm = _vm(
        adder=lambda col_id, image_ids: calls.append((col_id, image_ids)) or True,
        selection_manager=sel,
    )
    sel.select("img-1")
    sel.toggle("img-2")
    _spin()
    vm.addToCollection("col-3", "References")
    _spin()
    assert len(calls) == 1
    assert set(calls[0][1]) == {"img-1", "img-2"}


# ---------------------------------------------------------------------------
# modified signal
# ---------------------------------------------------------------------------

def _collect_signal(signal):
    received = []
    signal.connect(lambda: received.append(1))
    return received


def test_modified_emitted_on_add_to_collection_success(qapp):
    vm = _vm()
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.addToCollection("col-3", "References")
    _spin()
    assert len(received) >= 1


def test_modified_not_emitted_on_add_to_collection_failure(qapp):
    vm = _vm(adder=lambda *_: False)
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.addToCollection("col-3", "References")
    _spin()
    assert received == []


def test_modified_emitted_on_remove_from_collection_success(qapp):
    vm = _vm()
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.removeFromCollection("col-1")
    _spin()
    assert len(received) >= 1


def test_modified_not_emitted_on_remove_from_collection_failure(qapp):
    vm = _vm(remover=lambda *_: False)
    _load(vm)
    received = _collect_signal(vm.modified)
    vm.removeFromCollection("col-1")
    _spin()
    assert received == []


def test_modified_not_emitted_on_load(qapp):
    vm = _vm()
    received = _collect_signal(vm.modified)
    _load(vm)
    assert received == []


# ---------------------------------------------------------------------------
# reload
# ---------------------------------------------------------------------------

def test_reload_re_fetches_for_primary_image(qapp):
    fetch_calls = []
    def fetcher(image_id):
        fetch_calls.append(image_id)
        return list(SAMPLE_COLLECTIONS)
    vm = _vm(fetcher=fetcher)
    _load(vm, "img-1")
    assert len(fetch_calls) == 1
    vm.reload()
    _wait_for_state(vm, "Ready")
    assert len(fetch_calls) == 2
    assert fetch_calls[1] == "img-1"


def test_reload_is_noop_without_primary_image(qapp):
    fetch_calls = []
    vm = _vm(fetcher=lambda image_id: fetch_calls.append(image_id) or list(SAMPLE_COLLECTIONS))
    vm.reload()
    _spin()
    assert fetch_calls == []


def test_reload_is_noop_in_multi_selection_mode(qapp):
    fetch_calls = []
    sel = SelectionManager()
    vm = _vm(
        fetcher=lambda image_id: fetch_calls.append(image_id) or list(SAMPLE_COLLECTIONS),
        selection_manager=sel,
    )
    sel.select("img-1")
    _wait_for_state(vm, "Ready")
    sel.toggle("img-2")
    _wait_for_state(vm, "Idle")
    assert vm.selectionMode == "multi"
    count_before = len(fetch_calls)
    vm.reload()
    _spin()
    assert len(fetch_calls) == count_before
