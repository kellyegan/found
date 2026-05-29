from enum import Enum, auto

from PySide6.QtCore import QObject, Property, Signal


class AppState(Enum):
    Launching = auto()
    BackendStarting = auto()
    BackendRetrying = auto()
    Ready = auto()
    BackendError = auto()
    ShuttingDown = auto()


_VALID_TRANSITIONS: dict[AppState, set[AppState]] = {
    AppState.Launching: {AppState.BackendStarting, AppState.ShuttingDown},
    AppState.BackendStarting: {
        AppState.Ready,
        AppState.BackendRetrying,
        AppState.BackendError,   # direct failure when max_retries=0
        AppState.ShuttingDown,
    },
    AppState.BackendRetrying: {
        AppState.BackendStarting,
        AppState.BackendError,
        AppState.Ready,           # retry succeeds
        AppState.ShuttingDown,
    },
    AppState.Ready: {AppState.ShuttingDown},
    AppState.BackendError: {AppState.ShuttingDown},
    AppState.ShuttingDown: set(),
}

_STATUS_MESSAGES: dict[AppState, str] = {
    AppState.Launching: "",
    AppState.BackendStarting: "Starting…",
    AppState.BackendRetrying: "Retrying…",
    AppState.Ready: "",
    AppState.BackendError: "Failed to start. Please check the logs.",
    AppState.ShuttingDown: "",
}


class AppStateManager(QObject):
    stateChanged = Signal(object)
    stateNameChanged = Signal(str)
    statusMessageChanged = Signal(str)
    hasErrorChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = AppState.Launching

    @property
    def state(self) -> AppState:
        return self._state

    @Property(str, notify=stateNameChanged)
    def stateName(self) -> str:
        return self._state.name

    @Property(str, notify=statusMessageChanged)
    def statusMessage(self) -> str:
        return _STATUS_MESSAGES.get(self._state, "")

    @Property(bool, notify=hasErrorChanged)
    def hasError(self) -> bool:
        return self._state == AppState.BackendError

    def transition_to(self, new_state: AppState) -> None:
        allowed = _VALID_TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition: {self._state.name} → {new_state.name}"
            )
        prev_has_error = self.hasError
        self._state = new_state
        self.stateChanged.emit(new_state)
        self.stateNameChanged.emit(new_state.name)
        self.statusMessageChanged.emit(self.statusMessage)
        if self.hasError != prev_has_error:
            self.hasErrorChanged.emit(self.hasError)
