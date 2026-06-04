import sys
from pathlib import Path

from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from found_app.core.app_container import AppContainer


def _load_bundled_fonts() -> None:
    fonts_dir = Path(__file__).parent / "resources" / "fonts"
    for ext in ("*.ttf", "*.otf"):
        for font_file in sorted(fonts_dir.glob(ext)):
            QFontDatabase.addApplicationFont(str(font_file))


def main():
    app = QGuiApplication(sys.argv)
    _load_bundled_fonts()

    container = AppContainer()
    engine = QQmlApplicationEngine()
    container.wire_engine(engine)

    qml_path = Path(__file__).parent / "qml" / "main.qml"
    engine.load(str(qml_path))

    if not engine.rootObjects():
        sys.exit(1)

    app.aboutToQuit.connect(container.shutdown)
    container.start()
    exit_code = app.exec()

    del engine
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
