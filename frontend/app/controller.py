from PySide6.QtCore import QObject

from frontend.backend.process_manager import BackendProcessManager
from frontend.state.app_state import AppState, AppStateManager


class AppController(QObject):
    """Connects BackendProcessManager signals to AppStateManager transitions."""

    def __init__(
        self,
        app_state: AppStateManager,
        process_manager: BackendProcessManager,
        parent=None,
    ):
        super().__init__(parent)
        self._app_state = app_state
        self._process_manager = process_manager

        process_manager.ready.connect(self._on_ready)
        process_manager.failed.connect(self._on_failed)
        process_manager.retrying.connect(self._on_retrying)

    def start(self) -> None:
        self._app_state.transition_to(AppState.BackendStarting)
        self._process_manager.start()

    def shutdown(self) -> None:
        self._app_state.transition_to(AppState.ShuttingDown)
        self._process_manager.stop()

    def _on_ready(self) -> None:
        self._app_state.transition_to(AppState.Ready)

    def _on_failed(self, message: str) -> None:
        self._app_state.transition_to(AppState.BackendError)

    def _on_retrying(self, attempt: int) -> None:
        if self._app_state.state == AppState.BackendStarting:
            self._app_state.transition_to(AppState.BackendRetrying)
