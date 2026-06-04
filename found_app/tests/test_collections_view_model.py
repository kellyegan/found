"""
Tests for CollectionsViewModel — Slice 8 Commit 1.

Covers:
- Initial state: loadingState "Idle", empty collections, empty collectionGridModel
- load() transitions: Loading → Ready, Empty, or Error
- load() sorts collections alphabetically by name
- load() emits loadingStateChanged and collectionsChanged
- createCollection() appends to sorted list on success, no-op on failure
- addImagesToCollection() delegates to images_adder with correct args
- loadCollectionImages() populates collectionGridModel
- loadCollectionImages() clears previous model before loading
"""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from found_app.collections.collections_view_model import CollectionsViewModel
from found_app.models.thumbnail_grid_model import ThumbnailGridModel


SAMPLE_COLLECTIONS = [
    {"id": "col-2", "name": "Portraits", "description": None, "cover_image_id": None},
    {"id": "col-1", "name": "Abstract", "description": "Abstract art", "cover_image_id": None},
    {"id": "col-3", "name": "Landscapes", "description": None, "cover_image_id": None},
]

SAMPLE_IMAGES = [
    {"id": "img-1", "filename": "a.jpg", "width": 100, "height": 80, "file_status": "available"},
    {"id": "img-2", "filename": "b.jpg", "width": 200, "height": 150, "file_status": "available"},
]


def _vm(
    collections_fetcher=None,
    collection_creator=None,
    images_adder=None,
    collection_images_fetcher=None,
):
    return CollectionsViewModel(
        collections_fetcher=collections_fetcher or (lambda: []),
        collection_creator=collection_creator or (lambda name: None),
        images_adder=images_adder or (lambda cid, iids: False),
        collection_images_fetcher=collection_images_fetcher or (lambda cid: []),
    )


def wait_for_state(vm, target: str, timeout_ms: int = 2000) -> None:
    if vm.loadingState == target:
        return
    loop = QEventLoop()

    def check(name: str):
        if name == target:
            loop.quit()

    vm.loadingStateChanged.connect(check)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


def wait_for_images(vm, timeout_ms: int = 2000) -> None:
    """Wait for collectionGridModel to be populated by the images thread."""
    thread = vm._images_thread
    if thread is None or not thread.isRunning():
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        return
    loop = QEventLoop()
    thread.finished.connect(loop.quit)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_loading_state_defaults_to_idle(qapp):
    assert _vm().loadingState == "Idle"


def test_collections_defaults_to_empty(qapp):
    assert _vm().collections == []


def test_collection_grid_model_is_thumbnail_grid_model(qapp):
    assert isinstance(_vm().collectionGridModel, ThumbnailGridModel)


def test_collection_grid_model_is_initially_empty(qapp):
    assert _vm().collectionGridModel.count == 0


# ---------------------------------------------------------------------------
# load() — state transitions
# ---------------------------------------------------------------------------


def test_load_transitions_to_ready(qapp):
    vm = _vm(collections_fetcher=lambda: SAMPLE_COLLECTIONS)
    vm.load()
    wait_for_state(vm, "Ready")
    assert vm.loadingState == "Ready"


def test_load_transitions_to_empty_when_no_collections(qapp):
    vm = _vm(collections_fetcher=lambda: [])
    vm.load()
    wait_for_state(vm, "Empty")
    assert vm.loadingState == "Empty"


def test_load_transitions_to_error_when_fetcher_returns_none(qapp):
    vm = _vm(collections_fetcher=lambda: None)
    vm.load()
    wait_for_state(vm, "Error")
    assert vm.loadingState == "Error"


def test_load_transitions_to_error_when_fetcher_raises(qapp):
    def bad():
        raise RuntimeError("network down")

    vm = _vm(collections_fetcher=bad)
    vm.load()
    wait_for_state(vm, "Error")
    assert vm.loadingState == "Error"


# ---------------------------------------------------------------------------
# load() — data
# ---------------------------------------------------------------------------


def test_load_populates_collections(qapp):
    vm = _vm(collections_fetcher=lambda: SAMPLE_COLLECTIONS)
    vm.load()
    wait_for_state(vm, "Ready")
    assert len(vm.collections) == 3


def test_load_sorts_collections_alphabetically(qapp):
    vm = _vm(collections_fetcher=lambda: SAMPLE_COLLECTIONS)
    vm.load()
    wait_for_state(vm, "Ready")
    names = [c["name"] for c in vm.collections]
    assert names == sorted(names, key=str.lower)


def test_load_sorts_case_insensitively(qapp):
    unsorted = [
        {"id": "a", "name": "zebra", "description": None, "cover_image_id": None},
        {"id": "b", "name": "Apple", "description": None, "cover_image_id": None},
        {"id": "c", "name": "mango", "description": None, "cover_image_id": None},
    ]
    vm = _vm(collections_fetcher=lambda: unsorted)
    vm.load()
    wait_for_state(vm, "Ready")
    names = [c["name"] for c in vm.collections]
    assert names == ["Apple", "mango", "zebra"]


# ---------------------------------------------------------------------------
# load() — signals
# ---------------------------------------------------------------------------


def test_load_emits_loading_state_changed(qapp):
    received = []
    vm = _vm(collections_fetcher=lambda: SAMPLE_COLLECTIONS)
    vm.loadingStateChanged.connect(received.append)
    vm.load()
    wait_for_state(vm, "Ready")
    assert "Ready" in received


def test_load_emits_collections_changed(qapp):
    received = []
    vm = _vm(collections_fetcher=lambda: SAMPLE_COLLECTIONS)
    vm.collectionsChanged.connect(lambda: received.append(1))
    vm.load()
    wait_for_state(vm, "Ready")
    assert received


# ---------------------------------------------------------------------------
# createCollection()
# ---------------------------------------------------------------------------


def test_create_collection_appends_to_list(qapp):
    new_col = {"id": "col-new", "name": "New", "description": None, "cover_image_id": None}
    vm = _vm(
        collections_fetcher=lambda: SAMPLE_COLLECTIONS,
        collection_creator=lambda name: new_col,
    )
    vm.load()
    wait_for_state(vm, "Ready")
    count_before = len(vm.collections)
    vm.createCollection("New")
    assert len(vm.collections) == count_before + 1


def test_create_collection_inserts_in_sorted_position(qapp):
    existing = [
        {"id": "a", "name": "Alpha", "description": None, "cover_image_id": None},
        {"id": "c", "name": "Charlie", "description": None, "cover_image_id": None},
    ]
    new_col = {"id": "b", "name": "Bravo", "description": None, "cover_image_id": None}
    vm = _vm(
        collections_fetcher=lambda: existing,
        collection_creator=lambda name: new_col,
    )
    vm.load()
    wait_for_state(vm, "Ready")
    vm.createCollection("Bravo")
    names = [c["name"] for c in vm.collections]
    assert names == ["Alpha", "Bravo", "Charlie"]


def test_create_collection_noop_when_creator_returns_none(qapp):
    vm = _vm(
        collections_fetcher=lambda: SAMPLE_COLLECTIONS,
        collection_creator=lambda name: None,
    )
    vm.load()
    wait_for_state(vm, "Ready")
    count_before = len(vm.collections)
    vm.createCollection("Fail")
    assert len(vm.collections) == count_before


def test_create_collection_emits_collections_changed_on_success(qapp):
    new_col = {"id": "col-new", "name": "New", "description": None, "cover_image_id": None}
    received = []
    vm = _vm(
        collections_fetcher=lambda: [],
        collection_creator=lambda name: new_col,
    )
    vm.load()
    wait_for_state(vm, "Empty")
    vm.collectionsChanged.connect(lambda: received.append(1))
    vm.createCollection("New")
    assert received


# ---------------------------------------------------------------------------
# addImagesToCollection()
# ---------------------------------------------------------------------------


def test_add_images_calls_adder_with_correct_args(qapp):
    calls = []
    vm = _vm(images_adder=lambda cid, iids: calls.append((cid, iids)) or True)
    vm.addImagesToCollection("col-1", ["img-1", "img-2"])
    assert calls == [("col-1", ["img-1", "img-2"])]


def test_add_images_with_empty_list_is_noop(qapp):
    calls = []
    vm = _vm(images_adder=lambda cid, iids: calls.append((cid, iids)) or True)
    vm.addImagesToCollection("col-1", [])
    assert calls == []


# ---------------------------------------------------------------------------
# loadCollectionImages()
# ---------------------------------------------------------------------------


def test_load_collection_images_populates_grid_model(qapp):
    vm = _vm(collection_images_fetcher=lambda cid: SAMPLE_IMAGES)
    vm.loadCollectionImages("col-1")
    wait_for_images(vm)
    assert vm.collectionGridModel.count == 2


def test_load_collection_images_clears_previous_model(qapp):
    def fetcher(cid):
        return SAMPLE_IMAGES if cid == "col-1" else []

    vm = _vm(collection_images_fetcher=fetcher)
    vm.loadCollectionImages("col-1")
    wait_for_images(vm)
    assert vm.collectionGridModel.count == 2

    vm.loadCollectionImages("col-empty")
    wait_for_images(vm)
    assert vm.collectionGridModel.count == 0


def test_load_collection_images_empty_collection(qapp):
    vm = _vm(collection_images_fetcher=lambda cid: [])
    vm.loadCollectionImages("col-1")
    wait_for_images(vm)
    assert vm.collectionGridModel.count == 0


def test_load_collection_images_handles_fetcher_error(qapp):
    def bad(cid):
        raise RuntimeError("network error")

    vm = _vm(collection_images_fetcher=bad)
    vm.loadCollectionImages("col-1")
    wait_for_images(vm)
    assert vm.collectionGridModel.count == 0


# ---------------------------------------------------------------------------
# reloadCollectionImages()
# ---------------------------------------------------------------------------

def test_reload_collection_images_refetches_current_collection(qapp):
    fetcher_calls = []

    def fetcher(cid):
        fetcher_calls.append(cid)
        return SAMPLE_IMAGES if cid == "col-1" else []

    vm = _vm(collection_images_fetcher=fetcher)
    vm.loadCollectionImages("col-1")
    wait_for_images(vm)
    assert vm.collectionGridModel.count == 2

    fetcher_calls.clear()
    vm.reloadCollectionImages()
    wait_for_images(vm)
    assert fetcher_calls == ["col-1"]
    assert vm.collectionGridModel.count == 2


def test_reload_collection_images_noop_when_no_collection_loaded(qapp):
    fetcher_calls = []
    vm = _vm(collection_images_fetcher=lambda cid: fetcher_calls.append(cid) or [])
    vm.reloadCollectionImages()
    loop = QEventLoop()
    QTimer.singleShot(100, loop.quit)
    loop.exec()
    assert fetcher_calls == []
