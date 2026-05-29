import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from frontend.theme.theme import ThemeManager


def main():
    app = QGuiApplication(sys.argv)

    theme = ThemeManager()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("Theme", theme)
    qml_path = Path(__file__).parent / "qml" / "main.qml"
    engine.load(str(qml_path))

    if not engine.rootObjects():
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
