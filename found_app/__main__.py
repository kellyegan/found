import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication, QImageReader
from PySide6.QtQml import QQmlApplicationEngine

from found_app.core.app_container import AppContainer


def main():
    app = QGuiApplication(sys.argv)

    # Local desktop app — users import and view their own files, which can be
    # multi-hundred-megapixel images. The default 256 MB cap is appropriate for
    # servers processing untrusted uploads; remove it here.
    QImageReader.setAllocationLimit(0)

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
