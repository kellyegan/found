import os
import sys

# Must be set before any Qt import so the offscreen platform driver is used.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtGui import QGuiApplication

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    yield app
    # Do not call app.quit() — let the session end naturally.
