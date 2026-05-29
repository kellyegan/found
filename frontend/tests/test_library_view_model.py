"""
Tests for LibraryViewModel — Commit 9.

Covers:
- Initial loadingState is "Loading" before load() is called
- load() transitions to "Empty" when fetcher returns 0
- load() transitions to "Ready" when fetcher returns > 0
- load() transitions to "Error" when fetcher returns None
- loadingStateChanged signal fires on each transition
- loadingState property name matches enum member name
"""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from frontend.library.view_model import LibraryViewModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def wait_for_loading_state(vm, target_name: str, timeout_ms=2000):
    """Block until vm.loadingState == target_name or timeout."""
    if vm.loadingState == target_name:
        return
    loop = QEventLoop()

    def check(name: str):
        if name == target_name:
            loop.quit()

    vm.loadingStateChanged.connect(check)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


def make_vm(fetcher=None):
    return LibraryViewModel(image_fetcher=fetcher or (lambda: 0))


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_initial_loading_state_is_loading(qapp):
    vm = make_vm()
    assert vm.loadingState == "Loading"


# ---------------------------------------------------------------------------
# load() — state transitions
# ---------------------------------------------------------------------------


def test_load_transitions_to_empty_when_no_images(qapp):
    vm = make_vm(fetcher=lambda: 0)
    vm.load()
    wait_for_loading_state(vm, "Empty")
    assert vm.loadingState == "Empty"


def test_load_transitions_to_ready_when_images_exist(qapp):
    vm = make_vm(fetcher=lambda: 5)
    vm.load()
    wait_for_loading_state(vm, "Ready")
    assert vm.loadingState == "Ready"


def test_load_transitions_to_error_when_fetcher_returns_none(qapp):
    vm = make_vm(fetcher=lambda: None)
    vm.load()
    wait_for_loading_state(vm, "Error")
    assert vm.loadingState == "Error"


def test_load_transitions_to_error_when_fetcher_raises(qapp):
    def failing_fetcher():
        raise RuntimeError("network down")

    vm = make_vm(fetcher=failing_fetcher)
    vm.load()
    wait_for_loading_state(vm, "Error")
    assert vm.loadingState == "Error"


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


def test_loading_state_changed_signal_fires_on_transition(qapp):
    received = []
    vm = make_vm(fetcher=lambda: 3)
    vm.loadingStateChanged.connect(received.append)
    vm.load()
    wait_for_loading_state(vm, "Ready")
    assert "Ready" in received


def test_loading_state_changed_fires_with_correct_name(qapp):
    received = []
    vm = make_vm(fetcher=lambda: 0)
    vm.loadingStateChanged.connect(received.append)
    vm.load()
    wait_for_loading_state(vm, "Empty")
    assert received == ["Empty"]
