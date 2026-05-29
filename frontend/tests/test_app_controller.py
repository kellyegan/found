"""
Tests for AppController — wires AppStateManager to BackendProcessManager.

Covers:
- start() transitions AppState to BackendStarting then starts the process manager
- BackendProcessManager.ready → AppState transitions to Ready
- BackendProcessManager.failed → AppState transitions to BackendError
- BackendProcessManager.retrying → AppState transitions to BackendRetrying
- shutdown() transitions to ShuttingDown and stops the process manager
"""

import pytest
from unittest.mock import MagicMock

from PySide6.QtCore import QEventLoop, QTimer

from frontend.app.controller import AppController
from frontend.backend.process_manager import BackendProcessManager
from frontend.state.app_state import AppState, AppStateManager


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def wait_for_signal(signal, timeout_ms=2000):
    loop = QEventLoop()
    received = []

    def capture(*args):
        received.extend(args if args else [True])
        loop.quit()

    signal.connect(capture)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    return received


def make_process_manager(health_checker=None, max_retries=0):
    return BackendProcessManager(
        process_factory=lambda: MagicMock(),
        health_checker=health_checker or (lambda url: True),
        max_retries=max_retries,
        retry_interval=0.0,
        poll_interval=0.0,
        startup_timeout=0.0,
    )


# ---------------------------------------------------------------------------
# start()
# ---------------------------------------------------------------------------


def test_start_transitions_to_backend_starting(qapp):
    state = AppStateManager()
    pm = make_process_manager()
    controller = AppController(state, pm)
    controller.start()
    # State immediately transitions before thread runs
    assert state.state == AppState.BackendStarting
    pm.stop()


def test_start_transitions_to_ready_when_backend_healthy(qapp):
    state = AppStateManager()
    pm = make_process_manager(health_checker=lambda url: True)
    controller = AppController(state, pm)
    controller.start()
    wait_for_signal(state.stateChanged)
    assert state.state == AppState.Ready
    pm.stop()


def test_start_transitions_to_backend_error_when_backend_fails(qapp):
    state = AppStateManager()
    pm = make_process_manager(health_checker=lambda url: False, max_retries=0)
    controller = AppController(state, pm)
    controller.start()
    # Wait for the final state change (BackendStarting → BackendError)
    wait_for_signal(state.stateChanged)
    assert state.state == AppState.BackendError
    pm.stop()


def test_start_transitions_through_retrying_state(qapp):
    state = AppStateManager()
    pm = make_process_manager(health_checker=lambda url: False, max_retries=1)
    controller = AppController(state, pm)

    retrying_seen = []
    state.stateChanged.connect(
        lambda s: retrying_seen.append(s) if s == AppState.BackendRetrying else None
    )

    controller.start()
    wait_for_signal(state.stateChanged)  # Wait for final state
    pm.stop()

    assert AppState.BackendRetrying in retrying_seen


# ---------------------------------------------------------------------------
# shutdown()
# ---------------------------------------------------------------------------


def test_shutdown_transitions_to_shutting_down(qapp):
    state = AppStateManager()
    pm = make_process_manager()
    controller = AppController(state, pm)
    controller.start()
    wait_for_signal(state.stateChanged)  # Wait for Ready
    controller.shutdown()
    assert state.state == AppState.ShuttingDown


def test_shutdown_stops_process_manager(qapp):
    mock_proc = MagicMock()
    pm = BackendProcessManager(
        process_factory=lambda: mock_proc,
        health_checker=lambda url: True,
        max_retries=0,
        retry_interval=0.0,
        poll_interval=0.0,
        startup_timeout=0.0,
    )
    state = AppStateManager()
    controller = AppController(state, pm)
    controller.start()
    wait_for_signal(state.stateChanged)
    controller.shutdown()
    mock_proc.terminate.assert_called_once()
