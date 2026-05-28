from enum import Enum, auto

from PySide6.QtCore import QObject, Signal


class AppState(Enum):
    Launching = auto()
    BackendStarting = auto()
    BackendRetrying = auto()
    Ready = auto()
    BackendError = auto()
    ShuttingDown = auto()


_VALID_TRANSITIONS: dict[AppState, set[AppState]] = {
    AppState.Launching: {AppState.BackendStarting, AppState.ShuttingDown},
    AppState.BackendStarting: {AppState.Ready, AppState.BackendRetrying, AppState.ShuttingDown},
    AppState.BackendRetrying: {AppState.BackendStarting, AppState.BackendError, AppState.ShuttingDown},
    AppState.Ready: {AppState.ShuttingDown},
    AppState.BackendError: {AppState.ShuttingDown},
    AppState.ShuttingDown: set(),
}


class AppStateManager(QObject):
    stateChanged = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = AppState.Launching

    @property
    def state(self) -> AppState:
        return self._state

    def transition_to(self, new_state: AppState) -> None:
        allowed = _VALID_TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition: {self._state.name} → {new_state.name}"
            )
        self._state = new_state
        self.stateChanged.emit(new_state)
