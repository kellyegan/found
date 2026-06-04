"""
Tests for BackendConnectionManager — Commit 8.

Covers:
- Initial state is Connected (backend assumed healthy when monitor is created)
- Transitions to Reconnecting on first health failure
- Returns to Connected when a retry succeeds
- Transitions to Disconnected after all retries exhausted
- Reconnecting is seen before Disconnected in a full failure sequence
- QML-accessible properties: stateName, isConnected
- isConnected is False during Reconnecting and Disconnected
"""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from found_app.backend.connection_monitor import (
    BackendConnectionManager,
    BackendConnectionState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def wait_for_state(manager, target_state, timeout_ms=2000):
    """Block the event loop until manager transitions to target_state."""
    if manager.state == target_state:
        return
    loop = QEventLoop()

    def check(s):
        if s == target_state:
            loop.quit()

    manager.stateChanged.connect(check)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


def make_monitor(health_checker=None, max_retries=0, retry_interval=0.0, poll_interval=0.0):
    return BackendConnectionManager(
        health_checker=health_checker or (lambda url: True),
        health_url="http://localhost:8000/health",
        poll_interval=poll_interval,
        max_retries=max_retries,
        retry_interval=retry_interval,
    )


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_initial_state_is_connected(qapp):
    manager = make_monitor()
    assert manager.state == BackendConnectionState.Connected


def test_state_name_is_connected_initially(qapp):
    manager = make_monitor()
    assert manager.stateName == "Connected"


def test_is_connected_true_initially(qapp):
    manager = make_monitor()
    assert manager.isConnected is True


# ---------------------------------------------------------------------------
# start / stop
# ---------------------------------------------------------------------------


def test_start_and_stop_does_not_crash(qapp):
    manager = make_monitor(health_checker=lambda url: True)
    manager.start()
    manager.stop()
    assert manager.state == BackendConnectionState.Connected


# ---------------------------------------------------------------------------
# State transitions — failure path
# ---------------------------------------------------------------------------


def test_transitions_to_reconnecting_when_health_fails(qapp):
    seen_states = []
    manager = make_monitor(health_checker=lambda url: False, max_retries=1)
    manager.stateChanged.connect(seen_states.append)
    manager.start()
    wait_for_state(manager, BackendConnectionState.Reconnecting)
    manager.stop()
    assert BackendConnectionState.Reconnecting in seen_states


def test_transitions_to_disconnected_after_retries_exhausted(qapp):
    manager = make_monitor(health_checker=lambda url: False, max_retries=0)
    manager.start()
    wait_for_state(manager, BackendConnectionState.Disconnected)
    manager.stop()
    assert manager.state == BackendConnectionState.Disconnected


def test_reconnecting_seen_before_disconnected(qapp):
    seen_states = []
    manager = make_monitor(health_checker=lambda url: False, max_retries=1)
    manager.stateChanged.connect(seen_states.append)
    manager.start()
    wait_for_state(manager, BackendConnectionState.Disconnected)
    manager.stop()
    assert BackendConnectionState.Reconnecting in seen_states
    assert BackendConnectionState.Disconnected in seen_states
    reconnecting_idx = seen_states.index(BackendConnectionState.Reconnecting)
    disconnected_idx = seen_states.index(BackendConnectionState.Disconnected)
    assert reconnecting_idx < disconnected_idx


# ---------------------------------------------------------------------------
# State transitions — recovery path
# ---------------------------------------------------------------------------


def test_returns_to_connected_after_reconnection(qapp):
    call_count = [0]

    def flaky_checker(url):
        call_count[0] += 1
        return call_count[0] != 1  # fail only the first call

    seen_states = []
    manager = make_monitor(health_checker=flaky_checker, max_retries=1)
    manager.stateChanged.connect(seen_states.append)
    manager.start()
    wait_for_state(manager, BackendConnectionState.Reconnecting)
    wait_for_state(manager, BackendConnectionState.Connected)
    manager.stop()

    assert BackendConnectionState.Reconnecting in seen_states
    assert manager.state == BackendConnectionState.Connected


# ---------------------------------------------------------------------------
# QML properties
# ---------------------------------------------------------------------------


def test_state_name_reflects_disconnected_state(qapp):
    manager = make_monitor(health_checker=lambda url: False, max_retries=0)
    manager.start()
    wait_for_state(manager, BackendConnectionState.Disconnected)
    manager.stop()
    assert manager.stateName == "Disconnected"


def test_is_connected_false_when_disconnected(qapp):
    manager = make_monitor(health_checker=lambda url: False, max_retries=0)
    manager.start()
    wait_for_state(manager, BackendConnectionState.Disconnected)
    manager.stop()
    assert manager.isConnected is False


def test_is_connected_false_when_reconnecting(qapp):
    is_connected_during_reconnecting = [None]

    def on_state(s):
        if s == BackendConnectionState.Reconnecting:
            is_connected_during_reconnecting[0] = manager.isConnected

    manager = make_monitor(health_checker=lambda url: False, max_retries=1)
    manager.stateChanged.connect(on_state)
    manager.start()
    wait_for_state(manager, BackendConnectionState.Disconnected)
    manager.stop()
    assert is_connected_during_reconnecting[0] is False
