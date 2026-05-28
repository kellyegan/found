"""
Tests for AppState enum and AppStateManager.

Covers:
- all required states are defined
- initial state is Launching
- every legal transition succeeds and updates state
- illegal transitions raise ValueError
- stateChanged signal fires on each transition
"""

import pytest
from frontend.state.app_state import AppState, AppStateManager


# ---------------------------------------------------------------------------
# Enum contract
# ---------------------------------------------------------------------------


def test_app_state_has_all_states():
    assert {s.name for s in AppState} == {
        "Launching",
        "BackendStarting",
        "BackendRetrying",
        "Ready",
        "BackendError",
        "ShuttingDown",
    }


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_initial_state_is_launching(qapp):
    manager = AppStateManager()
    assert manager.state == AppState.Launching


# ---------------------------------------------------------------------------
# Legal transitions
# ---------------------------------------------------------------------------


def test_launching_to_backend_starting(qapp):
    manager = AppStateManager()
    manager.transition_to(AppState.BackendStarting)
    assert manager.state == AppState.BackendStarting


def test_backend_starting_to_ready(qapp):
    manager = AppStateManager()
    manager.transition_to(AppState.BackendStarting)
    manager.transition_to(AppState.Ready)
    assert manager.state == AppState.Ready


def test_backend_starting_to_retrying(qapp):
    manager = AppStateManager()
    manager.transition_to(AppState.BackendStarting)
    manager.transition_to(AppState.BackendRetrying)
    assert manager.state == AppState.BackendRetrying


def test_backend_retrying_back_to_starting(qapp):
    manager = AppStateManager()
    manager.transition_to(AppState.BackendStarting)
    manager.transition_to(AppState.BackendRetrying)
    manager.transition_to(AppState.BackendStarting)
    assert manager.state == AppState.BackendStarting


def test_backend_retrying_to_error(qapp):
    manager = AppStateManager()
    manager.transition_to(AppState.BackendStarting)
    manager.transition_to(AppState.BackendRetrying)
    manager.transition_to(AppState.BackendError)
    assert manager.state == AppState.BackendError


@pytest.mark.parametrize("start", [
    AppState.Launching,
    AppState.BackendStarting,
    AppState.BackendRetrying,
    AppState.Ready,
    AppState.BackendError,
])
def test_any_state_can_shut_down(qapp, start):
    manager = AppStateManager()
    manager._state = start  # set directly to bypass intermediate transitions
    manager.transition_to(AppState.ShuttingDown)
    assert manager.state == AppState.ShuttingDown


# ---------------------------------------------------------------------------
# Illegal transitions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("start, target", [
    (AppState.Launching, AppState.Ready),
    (AppState.Launching, AppState.BackendRetrying),
    (AppState.Launching, AppState.BackendError),
    (AppState.BackendStarting, AppState.Launching),
    (AppState.Ready, AppState.BackendStarting),
    (AppState.BackendError, AppState.Ready),
    (AppState.ShuttingDown, AppState.Launching),
])
def test_invalid_transition_raises(qapp, start, target):
    manager = AppStateManager()
    manager._state = start
    with pytest.raises(ValueError, match=f"{start.name}"):
        manager.transition_to(target)


# ---------------------------------------------------------------------------
# Signal
# ---------------------------------------------------------------------------


def test_state_changed_signal_emits_new_state(qapp):
    manager = AppStateManager()
    received = []
    manager.stateChanged.connect(lambda s: received.append(s))
    manager.transition_to(AppState.BackendStarting)
    assert received == [AppState.BackendStarting]


def test_state_changed_signal_fires_for_each_transition(qapp):
    manager = AppStateManager()
    received = []
    manager.stateChanged.connect(lambda s: received.append(s))
    manager.transition_to(AppState.BackendStarting)
    manager.transition_to(AppState.BackendRetrying)
    manager.transition_to(AppState.BackendError)
    assert received == [
        AppState.BackendStarting,
        AppState.BackendRetrying,
        AppState.BackendError,
    ]
