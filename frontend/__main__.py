import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from frontend.app.controller import AppController
from frontend.backend.connection_monitor import BackendConnectionManager
from frontend.backend.process_manager import BackendProcessManager
from frontend.state.app_state import AppStateManager
from frontend.theme.theme import ThemeManager


def main():
    app = QGuiApplication(sys.argv)

    theme = ThemeManager()
    app_state = AppStateManager()
    process_manager = BackendProcessManager()
    connection_monitor = BackendConnectionManager(
        health_checker=process_manager._health_checker,
        health_url=process_manager.health_url,
    )
    controller = AppController(app_state, process_manager, connection_monitor=connection_monitor)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("Theme", theme)
    engine.rootContext().setContextProperty("AppState", app_state)
    engine.rootContext().setContextProperty("BackendConnection", connection_monitor)

    qml_path = Path(__file__).parent / "qml" / "main.qml"
    engine.load(str(qml_path))

    if not engine.rootObjects():
        sys.exit(1)

    controller.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
