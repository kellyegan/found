import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import httpx

from frontend.app.controller import AppController
from frontend.backend.connection_monitor import BackendConnectionManager
from frontend.backend.process_manager import BackendProcessManager
from frontend.library.view_model import LibraryViewModel
from frontend.state.app_state import AppStateManager
from frontend.theme.theme import ThemeManager


def _make_image_fetcher(base_url: str):
    def fetch() -> int | None:
        try:
            response = httpx.get(f"{base_url}/api/v1/images?limit=1", timeout=5.0)
            data = response.json()
            if data.get("success"):
                return len(data.get("data", []))
            return None
        except Exception:
            return None
    return fetch


def main():
    app = QGuiApplication(sys.argv)

    theme = ThemeManager()
    app_state = AppStateManager()
    process_manager = BackendProcessManager()
    connection_monitor = BackendConnectionManager(
        health_checker=process_manager._health_checker,
        health_url=process_manager.health_url,
    )
    base_url = f"http://{process_manager._host}:{process_manager._port}"
    library_state = LibraryViewModel(image_fetcher=_make_image_fetcher(base_url))
    controller = AppController(
        app_state,
        process_manager,
        connection_monitor=connection_monitor,
        library_view_model=library_state,
    )

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("Theme", theme)
    engine.rootContext().setContextProperty("AppState", app_state)
    engine.rootContext().setContextProperty("BackendConnection", connection_monitor)
    engine.rootContext().setContextProperty("LibraryState", library_state)

    qml_path = Path(__file__).parent / "qml" / "main.qml"
    engine.load(str(qml_path))

    if not engine.rootObjects():
        sys.exit(1)

    controller.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
