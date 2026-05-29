"""
Tests for LibraryViewModel — Commit 5 (updated for ThumbnailGridModel integration).

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
"""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from frontend.library.view_model import LibraryViewModel
from frontend.library.thumbnail_grid_model import ThumbnailGridModel


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
    # Wait briefly for the thread to finish
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
