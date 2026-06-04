"""
Tests for LibraryViewModel.

Covers:
- Initial loadingState is "Loading" before load() is called
- load() transitions to "Empty" when page_fetcher returns empty items
- load() transitions to "Ready" when page_fetcher returns images
- load() transitions to "Error" when page_fetcher returns None
- load() transitions to "Error" when page_fetcher raises
- loadingStateChanged signal fires on each transition
- gridModel property is a ThumbnailGridModel exposed to QML
- load() populates gridModel with returned items
- load_more() fetches next page and appends to gridModel
- load_more() is a no-op when hasMore is False
- reload() clears and refetches
- FilterStateManager integration: query params forwarded, filter change triggers reload
"""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from found_app.library.view_model import LibraryViewModel
from found_app.library.thumbnail_grid_model import ThumbnailGridModel
from found_app.services.filter_state import FilterStateManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_ITEMS = [
    {"id": "aaaa-0001", "filename": "a.jpg", "width": 100, "height": 80, "file_status": "available"},
    {"id": "bbbb-0002", "filename": "b.jpg", "width": 200, "height": 150, "file_status": "available"},
]


def _page(items=None, cursor=None, has_more=False):
    return {"items": items or [], "next_cursor": cursor, "has_more": has_more}


def _make_vm(fetcher=None):
    return LibraryViewModel(page_fetcher=fetcher or (lambda cursor=None, limit=100: _page()))


def wait_for_state(vm, target: str, timeout_ms=2000):
    if vm.loadingState == target:
        return
    loop = QEventLoop()

    def check(name: str):
        if name == target:
            loop.quit()

    vm.loadingStateChanged.connect(check)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_initial_loading_state_is_loading(qapp):
    vm = _make_vm()
    assert vm.loadingState == "Loading"


def test_grid_model_is_thumbnail_grid_model(qapp):
    vm = _make_vm()
    assert isinstance(vm.gridModel, ThumbnailGridModel)


def test_grid_model_is_initially_empty(qapp):
    vm = _make_vm()
    assert vm.gridModel.count == 0


# ---------------------------------------------------------------------------
# load() — state transitions
# ---------------------------------------------------------------------------


def test_load_transitions_to_empty_when_no_images(qapp):
    vm = _make_vm(fetcher=lambda cursor=None, limit=100: _page(items=[]))
    vm.load()
    wait_for_state(vm, "Empty")
    assert vm.loadingState == "Empty"


def test_load_transitions_to_ready_when_images_exist(qapp):
    vm = _make_vm(fetcher=lambda cursor=None, limit=100: _page(items=SAMPLE_ITEMS))
    vm.load()
    wait_for_state(vm, "Ready")
    assert vm.loadingState == "Ready"


def test_load_transitions_to_error_when_fetcher_returns_none(qapp):
    vm = _make_vm(fetcher=lambda cursor=None, limit=100: None)
    vm.load()
    wait_for_state(vm, "Error")
    assert vm.loadingState == "Error"


def test_load_transitions_to_error_when_fetcher_raises(qapp):
    def bad(cursor=None, limit=100):
        raise RuntimeError("network down")

    vm = _make_vm(fetcher=bad)
    vm.load()
    wait_for_state(vm, "Error")
    assert vm.loadingState == "Error"


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


def test_loading_state_changed_fires_on_transition(qapp):
    received = []
    vm = _make_vm(fetcher=lambda cursor=None, limit=100: _page(items=SAMPLE_ITEMS))
    vm.loadingStateChanged.connect(received.append)
    vm.load()
    wait_for_state(vm, "Ready")
    assert "Ready" in received


def test_loading_state_changed_fires_with_correct_name(qapp):
    received = []
    vm = _make_vm(fetcher=lambda cursor=None, limit=100: _page(items=[]))
    vm.loadingStateChanged.connect(received.append)
    vm.load()
    wait_for_state(vm, "Empty")
    assert received == ["Empty"]


# ---------------------------------------------------------------------------
# Grid model population
# ---------------------------------------------------------------------------


def test_load_populates_grid_model(qapp):
    vm = _make_vm(fetcher=lambda cursor=None, limit=100: _page(items=SAMPLE_ITEMS))
    vm.load()
    wait_for_state(vm, "Ready")
    assert vm.gridModel.count == 2


def test_load_does_not_populate_grid_model_on_error(qapp):
    vm = _make_vm(fetcher=lambda cursor=None, limit=100: None)
    vm.load()
    wait_for_state(vm, "Error")
    assert vm.gridModel.count == 0


# ---------------------------------------------------------------------------
# load_more()
# ---------------------------------------------------------------------------


def _two_page_fetcher():
    """Returns page 1 on first call, page 2 on second."""
    calls = []

    def fetch(cursor=None, limit=100):
        calls.append(cursor)
        if cursor is None:
            return _page(items=SAMPLE_ITEMS, cursor="page2", has_more=True)
        return _page(items=SAMPLE_ITEMS, cursor=None, has_more=False)

    return fetch


def test_load_more_appends_next_page(qapp):
    vm = _make_vm(fetcher=_two_page_fetcher())
    vm.load()
    wait_for_state(vm, "Ready")
    assert vm.gridModel.count == 2

    vm.load_more()
    loop = QEventLoop()
    QTimer.singleShot(500, loop.quit)
    loop.exec()
    assert vm.gridModel.count == 4


def test_load_more_is_noop_when_no_more_pages(qapp):
    vm = _make_vm(fetcher=lambda cursor=None, limit=100: _page(items=SAMPLE_ITEMS, has_more=False))
    vm.load()
    wait_for_state(vm, "Ready")
    count_before = vm.gridModel.count
    vm.load_more()
    assert vm.gridModel.count == count_before


# ---------------------------------------------------------------------------
# reload()
# ---------------------------------------------------------------------------


def test_reload_clears_and_refetches(qapp):
    calls = []

    def fetcher(cursor=None, limit=100):
        calls.append(cursor)
        return _page(items=SAMPLE_ITEMS)

    vm = _make_vm(fetcher=fetcher)
    vm.load()
    wait_for_state(vm, "Ready")
    vm.reload()
    wait_for_state(vm, "Ready")
    assert len(calls) == 2


def test_reload_resets_grid_before_refetch(qapp):
    vm = _make_vm(fetcher=lambda cursor=None, limit=100: _page(items=SAMPLE_ITEMS))
    vm.load()
    wait_for_state(vm, "Ready")
    assert vm.gridModel.count == 2

    vm.reload()
    wait_for_state(vm, "Ready")
    assert vm.gridModel.count == 2  # still 2, not 4 — grid was cleared before reload


# ---------------------------------------------------------------------------
# FilterStateManager integration
# ---------------------------------------------------------------------------


def test_filter_state_triggers_reload_on_filter_change(qapp):
    fsm = FilterStateManager()
    calls = []

    def fetcher(cursor=None, limit=100, import_job=None):
        calls.append(import_job)
        return _page(items=SAMPLE_ITEMS)

    vm = LibraryViewModel(page_fetcher=fetcher, filter_state=fsm)
    vm.load()
    wait_for_state(vm, "Ready")
    count_before = len(calls)
    fsm.setImportJobFilter("job-123")
    wait_for_state(vm, "Ready")
    assert len(calls) > count_before


def test_filter_state_passes_import_job_to_fetcher(qapp):
    fsm = FilterStateManager()
    fsm.setImportJobFilter("job-xyz")
    captured = []

    def fetcher(cursor=None, limit=100, import_job=None):
        captured.append(import_job)
        return _page(items=SAMPLE_ITEMS)

    vm = LibraryViewModel(page_fetcher=fetcher, filter_state=fsm)
    vm.load()
    wait_for_state(vm, "Ready")
    assert "job-xyz" in captured


def test_filter_state_passes_category_to_fetcher(qapp):
    fsm = FilterStateManager()
    fsm.setCategoryFilter("cat-1", "include")
    captured = []

    def fetcher(cursor=None, limit=100, category=None):
        captured.append(category)
        return _page(items=SAMPLE_ITEMS)

    vm = LibraryViewModel(page_fetcher=fetcher, filter_state=fsm)
    vm.load()
    wait_for_state(vm, "Ready")
    assert "cat-1" in captured


def test_no_filter_state_fetches_without_extra_params(qapp):
    captured_kwargs = []

    def fetcher(**kwargs):
        captured_kwargs.append(kwargs)
        return _page(items=SAMPLE_ITEMS)

    vm = LibraryViewModel(page_fetcher=fetcher)
    vm.load()
    wait_for_state(vm, "Ready")
    assert captured_kwargs[0] == {"cursor": None, "limit": 100}


# ---------------------------------------------------------------------------
# missingCount
# ---------------------------------------------------------------------------

MISSING_ITEMS = [
    {"id": "cc-0001", "filename": "c.jpg", "file_status": "missing"},
    {"id": "dd-0002", "filename": "d.jpg", "file_status": "available"},
]


def test_missing_count_defaults_to_zero(qapp):
    vm = _make_vm()
    assert vm.missingCount == 0


def test_missing_count_reflects_grid_model(qapp):
    vm = LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: _page(items=MISSING_ITEMS)
    )
    vm.load()
    wait_for_state(vm, "Ready")
    assert vm.missingCount == 1


def test_missing_count_resets_on_reload(qapp):
    vm = LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: _page(items=MISSING_ITEMS)
    )
    vm.load()
    wait_for_state(vm, "Ready")
    assert vm.missingCount == 1
    vm.reload()
    wait_for_state(vm, "Ready")
    assert vm.missingCount == 1  # reset + refilled, not doubled


def test_missing_count_changed_signal_fires(qapp):
    received = []
    vm = LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: _page(items=MISSING_ITEMS)
    )
    vm.missingCountChanged.connect(received.append)
    vm.load()
    wait_for_state(vm, "Ready")
    assert 1 in received


# ---------------------------------------------------------------------------
# verifyImage
# ---------------------------------------------------------------------------


def _make_vm_with_verifier(verifier=None):
    return LibraryViewModel(
        page_fetcher=lambda cursor=None, limit=100: _page(items=SAMPLE_ITEMS),
        image_verifier=verifier,
    )


def test_verify_image_calls_verifier(qapp):
    calls = []
    def verifier(image_id):
        calls.append(image_id)
        return "missing"

    vm = _make_vm_with_verifier(verifier)
    vm.load()
    wait_for_state(vm, "Ready")

    loop = QEventLoop()
    vm.gridModel.missingCountChanged.connect(lambda _: loop.quit())
    QTimer.singleShot(2000, loop.quit)
    vm.verifyImage("aaaa-0001")
    loop.exec()

    assert "aaaa-0001" in calls


def test_verify_image_updates_grid_model_status(qapp):
    def verifier(image_id):
        return "missing"

    vm = _make_vm_with_verifier(verifier)
    vm.load()
    wait_for_state(vm, "Ready")

    loop = QEventLoop()
    vm.gridModel.missingCountChanged.connect(lambda _: loop.quit())
    QTimer.singleShot(2000, loop.quit)
    vm.verifyImage("aaaa-0001")
    loop.exec()

    assert vm.missingCount == 1


def test_verify_image_no_op_when_no_verifier(qapp):
    vm = _make_vm_with_verifier(verifier=None)
    vm.load()
    wait_for_state(vm, "Ready")
    vm.verifyImage("aaaa-0001")  # must not raise
    assert vm.missingCount == 0
