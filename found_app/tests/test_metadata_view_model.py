"""Tests for MetadataViewModel — Commit 8."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from found_app.metadata.metadata_view_model import MetadataViewModel
from found_app.selection.selection_manager import SelectionManager


SAMPLE_IMAGE = {
    "id": "img-001",
    "filename": "photo.jpg",
    "path": "/photos/photo.jpg",
    "width": 1920,
    "height": 1080,
    "file_size": 204800,
    "mime_type": "image/jpeg",
    "created_date": "2024-01-15T10:30:00",
    "modified_date": "2024-01-15T10:30:00",
    "imported_date": "2024-06-01T09:00:00",
    "sha256_hash": "abc123",
    "thumbnail_path": "thumbnails/ab/abc123.jpg",
    "file_status": "available",
    "import_job_id": None,
}

MISSING_IMAGE = {**SAMPLE_IMAGE, "file_status": "missing"}


def _vm(fetcher=None):
    return MetadataViewModel(
        image_fetcher=fetcher or (lambda image_id: SAMPLE_IMAGE)
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


def _load(vm, image_id="img-001"):
    vm.loadImage(image_id)
    _wait_for_state(vm, "Ready")
    _spin()


def _load_error(vm, image_id="img-001"):
    vm.loadImage(image_id)
    _wait_for_state(vm, "Error")
    _spin()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_loading_state_defaults_to_idle(qapp):
    assert _vm().loadingState == "Idle"


def test_image_id_defaults_to_empty(qapp):
    assert _vm().imageId == ""


def test_filename_defaults_to_empty(qapp):
    assert _vm().filename == ""


def test_path_defaults_to_empty(qapp):
    assert _vm().path == ""


def test_dimensions_defaults_to_empty(qapp):
    assert _vm().dimensions == ""


def test_file_size_defaults_to_zero(qapp):
    assert _vm().fileSize == 0


def test_date_added_defaults_to_empty(qapp):
    assert _vm().dateAdded == ""


def test_is_missing_defaults_to_false(qapp):
    assert _vm().isMissing is False


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def test_load_image_sets_state_to_ready(qapp):
    vm = _vm()
    _load(vm)
    assert vm.loadingState == "Ready"


def test_load_image_populates_image_id(qapp):
    vm = _vm()
    _load(vm)
    assert vm.imageId == "img-001"


def test_load_image_populates_filename(qapp):
    vm = _vm()
    _load(vm)
    assert vm.filename == "photo.jpg"


def test_load_image_populates_path(qapp):
    vm = _vm()
    _load(vm)
    assert vm.path == "/photos/photo.jpg"


def test_load_image_populates_dimensions(qapp):
    vm = _vm()
    _load(vm)
    assert vm.dimensions == "1920 × 1080"


def test_load_image_populates_file_size(qapp):
    vm = _vm()
    _load(vm)
    assert vm.fileSize == 204800


def test_load_image_populates_date_added(qapp):
    vm = _vm()
    _load(vm)
    assert vm.dateAdded == "2024-06-01T09:00:00"


def test_load_image_sets_is_missing_false_for_available(qapp):
    vm = _vm()
    _load(vm)
    assert vm.isMissing is False


def test_load_image_sets_is_missing_true_for_missing(qapp):
    vm = _vm(fetcher=lambda image_id: MISSING_IMAGE)
    _load(vm)
    assert vm.isMissing is True


def test_load_image_emits_metadata_changed(qapp):
    vm = _vm()
    received = []
    vm.metadataChanged.connect(lambda: received.append(1))
    _load(vm)
    assert len(received) >= 1


def test_fetcher_receives_correct_image_id(qapp):
    received_ids = []

    def fetcher(image_id):
        received_ids.append(image_id)
        return SAMPLE_IMAGE

    vm = MetadataViewModel(image_fetcher=fetcher)
    _load(vm, image_id="img-999")
    assert received_ids == ["img-999"]


# ---------------------------------------------------------------------------
# Error state
# ---------------------------------------------------------------------------

def test_load_image_sets_state_to_error_on_none(qapp):
    vm = _vm(fetcher=lambda image_id: None)
    _load_error(vm)
    assert vm.loadingState == "Error"


def test_load_image_sets_state_to_error_on_exception(qapp):
    def bad_fetcher(image_id):
        raise RuntimeError("Network failure")

    vm = _vm(fetcher=bad_fetcher)
    _load_error(vm)
    assert vm.loadingState == "Error"


def test_metadata_cleared_on_error(qapp):
    vm = _vm()
    _load(vm)
    assert vm.filename == "photo.jpg"

    vm2 = _vm(fetcher=lambda image_id: None)
    vm2.loadImage("img-001")
    _wait_for_state(vm2, "Error")
    _spin()
    assert vm2.filename == ""


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

def test_clear_resets_loading_state_to_idle(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.loadingState == "Idle"


def test_clear_resets_image_id(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.imageId == ""


def test_clear_resets_filename(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.filename == ""


def test_clear_resets_path(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.path == ""


def test_clear_resets_dimensions(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.dimensions == ""


def test_clear_resets_file_size(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.fileSize == 0


def test_clear_resets_date_added(qapp):
    vm = _vm()
    _load(vm)
    vm.clear()
    assert vm.dateAdded == ""


def test_clear_resets_is_missing(qapp):
    vm = _vm(fetcher=lambda image_id: MISSING_IMAGE)
    _load(vm)
    vm.clear()
    assert vm.isMissing is False


def test_clear_emits_metadata_changed(qapp):
    vm = _vm()
    _load(vm)
    received = []
    vm.metadataChanged.connect(lambda: received.append(1))
    vm.clear()
    assert len(received) == 1


def test_clear_emits_loading_state_changed(qapp):
    vm = _vm()
    _load(vm)
    received = []
    vm.loadingStateChanged.connect(lambda s: received.append(s))
    vm.clear()
    assert "Idle" in received


# ---------------------------------------------------------------------------
# SelectionManager integration
# ---------------------------------------------------------------------------

def test_single_selection_triggers_load(qapp):
    selection = SelectionManager()
    vm = MetadataViewModel(
        image_fetcher=lambda image_id: SAMPLE_IMAGE,
        selection_manager=selection,
    )
    selection.select("img-001")
    _wait_for_state(vm, "Ready")
    _spin()
    assert vm.imageId == "img-001"


def test_clear_selection_calls_clear(qapp):
    selection = SelectionManager()
    vm = MetadataViewModel(
        image_fetcher=lambda image_id: SAMPLE_IMAGE,
        selection_manager=selection,
    )
    selection.select("img-001")
    _wait_for_state(vm, "Ready")
    _spin()
    assert vm.imageId == "img-001"

    selection.clear()
    _spin()
    assert vm.loadingState == "Idle"
    assert vm.imageId == ""


def test_multi_selection_clears_metadata(qapp):
    selection = SelectionManager()
    vm = MetadataViewModel(
        image_fetcher=lambda image_id: SAMPLE_IMAGE,
        selection_manager=selection,
    )
    selection.select("img-001")
    _wait_for_state(vm, "Ready")
    _spin()

    selection.toggle("img-002")
    _spin()
    assert vm.loadingState == "Idle"
    assert vm.imageId == ""


def test_switching_selection_loads_new_image(qapp):
    images = {
        "img-001": {**SAMPLE_IMAGE, "id": "img-001", "filename": "first.jpg"},
        "img-002": {**SAMPLE_IMAGE, "id": "img-002", "filename": "second.jpg"},
    }

    selection = SelectionManager()
    vm = MetadataViewModel(
        image_fetcher=lambda image_id: images[image_id],
        selection_manager=selection,
    )

    selection.select("img-001")
    _wait_for_state(vm, "Ready")
    _spin()
    assert vm.filename == "first.jpg"

    selection.select("img-002")
    _wait_for_state(vm, "Ready")
    _spin()
    assert vm.filename == "second.jpg"
