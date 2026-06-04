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
from found_app.state.app_state import AppState, AppStateManager


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


# ---------------------------------------------------------------------------
# QML-accessible properties: stateName, statusMessage, hasError
# ---------------------------------------------------------------------------


def test_state_name_returns_current_state_name(qapp):
    manager = AppStateManager()
    assert manager.stateName == "Launching"


def test_state_name_updates_on_transition(qapp):
    manager = AppStateManager()
    manager.transition_to(AppState.BackendStarting)
    assert manager.stateName == "BackendStarting"


def test_state_name_changed_signal_fires_on_transition(qapp):
    manager = AppStateManager()
    received = []
    manager.stateNameChanged.connect(lambda s: received.append(s))
    manager.transition_to(AppState.BackendStarting)
    assert received == ["BackendStarting"]


def test_status_message_is_empty_in_launching_state(qapp):
    assert AppStateManager().statusMessage == ""


def test_status_message_is_non_empty_in_backend_starting(qapp):
    manager = AppStateManager()
    manager.transition_to(AppState.BackendStarting)
    assert len(manager.statusMessage) > 0


def test_status_message_is_non_empty_in_backend_retrying(qapp):
    manager = AppStateManager()
    manager._state = AppState.BackendRetrying
    assert len(manager.statusMessage) > 0


def test_status_message_changed_signal_fires_on_transition(qapp):
    manager = AppStateManager()
    received = []
    manager.statusMessageChanged.connect(lambda s: received.append(s))
    manager.transition_to(AppState.BackendStarting)
    assert received  # at least one emission


def test_has_error_is_false_by_default(qapp):
    assert AppStateManager().hasError is False


def test_has_error_is_true_in_backend_error_state(qapp):
    manager = AppStateManager()
    manager._state = AppState.BackendRetrying
    manager.transition_to(AppState.BackendError)
    assert manager.hasError is True


def test_has_error_is_false_in_ready_state(qapp):
    manager = AppStateManager()
    manager.transition_to(AppState.BackendStarting)
    manager.transition_to(AppState.Ready)
    assert manager.hasError is False


def test_has_error_changed_signal_fires_when_entering_error_state(qapp):
    manager = AppStateManager()
    manager._state = AppState.BackendRetrying
    received = []
    manager.hasErrorChanged.connect(lambda v: received.append(v))
    manager.transition_to(AppState.BackendError)
    assert received == [True]


# ---------------------------------------------------------------------------
# Updated valid transitions (gaps fixed for controller wiring)
# ---------------------------------------------------------------------------


def test_backend_starting_can_transition_to_backend_error(qapp):
    manager = AppStateManager()
    manager.transition_to(AppState.BackendStarting)
    manager.transition_to(AppState.BackendError)
    assert manager.state == AppState.BackendError


def test_backend_retrying_can_transition_to_ready(qapp):
    manager = AppStateManager()
    manager._state = AppState.BackendRetrying
    manager.transition_to(AppState.Ready)
    assert manager.state == AppState.Ready
