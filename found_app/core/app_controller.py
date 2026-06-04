from PySide6.QtCore import QObject

from found_app.core.process_manager import BackendProcessManager
from found_app.core.app_state import AppState, AppStateManager


class AppController(QObject):
    """Connects BackendProcessManager signals to AppStateManager transitions."""

    def __init__(
        self,
        app_state: AppStateManager,
        process_manager: BackendProcessManager,
        connection_monitor=None,
        library_view_model=None,
        parent=None,
    ):
        super().__init__(parent)
        self._app_state = app_state
        self._process_manager = process_manager
        self._connection_monitor = connection_monitor
        self._library_view_model = library_view_model

        process_manager.ready.connect(self._on_ready)
        process_manager.failed.connect(self._on_failed)
        process_manager.retrying.connect(self._on_retrying)

    def start(self) -> None:
        self._app_state.transition_to(AppState.BackendStarting)
        self._process_manager.start()

    def shutdown(self) -> None:
        self._app_state.transition_to(AppState.ShuttingDown)
        if self._connection_monitor is not None:
            self._connection_monitor.stop()
        self._process_manager.stop()

    def _on_ready(self) -> None:
        self._app_state.transition_to(AppState.Ready)
        if self._connection_monitor is not None:
            self._connection_monitor.start()
        if self._library_view_model is not None:
            self._library_view_model.load()

    def _on_failed(self, message: str) -> None:
        self._app_state.transition_to(AppState.BackendError)

    def _on_retrying(self, attempt: int) -> None:
        if self._app_state.state == AppState.BackendStarting:
            self._app_state.transition_to(AppState.BackendRetrying)
