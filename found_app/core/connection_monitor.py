import time
from enum import Enum, auto
from typing import Callable

from PySide6.QtCore import QObject, QThread, Property, Signal


class BackendConnectionState(Enum):
    Connected = auto()
    Reconnecting = auto()
    Disconnected = auto()


class BackendConnectionManager(QObject):
    stateChanged = Signal(object)
    stateNameChanged = Signal(str)
    isConnectedChanged = Signal(bool)

    def __init__(
        self,
        health_checker: Callable[[str], bool],
        health_url: str,
        poll_interval: float = 30.0,
        max_retries: int = 3,
        retry_interval: float = 10.0,
        parent=None,
    ):
        super().__init__(parent)
        self._health_checker = health_checker
        self._health_url = health_url
        self._poll_interval = poll_interval
        self._max_retries = max_retries
        self._retry_interval = retry_interval
        self._state = BackendConnectionState.Connected
        self._thread: _MonitorThread | None = None

    @property
    def state(self) -> BackendConnectionState:
        return self._state

    @Property(str, notify=stateNameChanged)
    def stateName(self) -> str:
        return self._state.name

    @Property(bool, notify=isConnectedChanged)
    def isConnected(self) -> bool:
        return self._state == BackendConnectionState.Connected

    def start(self) -> None:
        self._thread = _MonitorThread(
            health_checker=self._health_checker,
            health_url=self._health_url,
            poll_interval=self._poll_interval,
            max_retries=self._max_retries,
            retry_interval=self._retry_interval,
        )
        self._thread.connectionLost.connect(self._on_connection_lost)
        self._thread.reconnected.connect(self._on_reconnected)
        self._thread.disconnected.connect(self._on_disconnected)
        self._thread.start()

    def stop(self) -> None:
        if self._thread and self._thread.isRunning():
            self._thread.requestInterruption()
            self._thread.wait(3000)

    def _set_state(self, new_state: BackendConnectionState) -> None:
        if new_state == self._state:
            return
        prev_connected = self.isConnected
        self._state = new_state
        self.stateChanged.emit(new_state)
        self.stateNameChanged.emit(new_state.name)
        if self.isConnected != prev_connected:
            self.isConnectedChanged.emit(self.isConnected)

    def _on_connection_lost(self) -> None:
        self._set_state(BackendConnectionState.Reconnecting)

    def _on_reconnected(self) -> None:
        self._set_state(BackendConnectionState.Connected)

    def _on_disconnected(self) -> None:
        self._set_state(BackendConnectionState.Disconnected)


class _MonitorThread(QThread):
    connectionLost = Signal()
    reconnected = Signal()
    disconnected = Signal()

    def __init__(
        self,
        health_checker: Callable[[str], bool],
        health_url: str,
        poll_interval: float,
        max_retries: int,
        retry_interval: float,
        parent=None,
    ):
        super().__init__(parent)
        self._health_checker = health_checker
        self._health_url = health_url
        self._poll_interval = poll_interval
        self._max_retries = max_retries
        self._retry_interval = retry_interval

    def run(self) -> None:
        while not self.isInterruptionRequested():
            self._interruptible_sleep(self._poll_interval)
            if self.isInterruptionRequested():
                return
            if self._health_checker(self._health_url):
                continue
            self.connectionLost.emit()
            reconnected = False
            for _ in range(self._max_retries):
                if self.isInterruptionRequested():
                    return
                self._interruptible_sleep(self._retry_interval)
                if self.isInterruptionRequested():
                    return
                if self._health_checker(self._health_url):
                    self.reconnected.emit()
                    reconnected = True
                    break
            if not reconnected:
                self.disconnected.emit()
                return

    def _interruptible_sleep(self, duration: float) -> None:
        if duration <= 0:
            return
        elapsed = 0.0
        step = min(0.05, duration)
        while elapsed < duration:
            if self.isInterruptionRequested():
                return
            time.sleep(step)
            elapsed += step
