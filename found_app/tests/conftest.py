import os
import sys

# Must be set before any Qt import so the offscreen platform driver is used.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    from found_app.theme.theme import ThemeManager, register_theme_singleton

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    # Registering the Found.Theme QML singleton is one-time and process-wide
    # (see register_theme_singleton), so do it once here rather than letting
    # whichever test happens to instantiate AppContainer first register it —
    # that would make `import Found.Theme` resolve only for tests that run
    # after that one.
    register_theme_singleton(ThemeManager())

    # qmlRegisterSingletonInstance ties the singleton to whichever QQmlEngine
    # first reads one of its properties; every other engine then gets a null
    # singleton ("must only be accessed from one engine"). Bind it to a
    # dedicated engine here, before any test creates its own, and hand that
    # engine out via the theme_qml_engine fixture for tests that need to read
    # Theme.* values through QML.
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.setData(
        b'import QtQuick\nimport Found.Theme 1.0\nQtObject { property string bg: Theme.background }',
        QUrl(),
    )
    component.create()
    app._theme_qml_engine = engine

    yield app
    # Do not call app.quit() — let the session end naturally.


@pytest.fixture(scope="session")
def theme_qml_engine(qapp):
    return qapp._theme_qml_engine
