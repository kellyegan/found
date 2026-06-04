"""
Scaffold tests for Commit 1.

Verifies the minimum contracts that must hold before any other found_app
code can be written:
  - the `found_app` package is importable
  - `python -m found_app` has a callable entry point
  - the root QML file exists at the path the entry point will use
  - the QML engine can load that file without errors in headless mode
"""

import os
from pathlib import Path


def test_found_app_package_importable():
    import found_app  # noqa: F401


def test_main_entry_point_is_callable():
    from found_app.__main__ import main

    assert callable(main)


def test_main_qml_exists():
    import found_app

    qml_path = Path(found_app.__file__).parent / "qml" / "main.qml"
    assert qml_path.exists(), f"main.qml not found at {qml_path}"


def test_qml_engine_loads_main(qapp):
    from PySide6.QtQml import QQmlApplicationEngine
    from found_app.theme.theme import ThemeManager
    import found_app

    theme = ThemeManager()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("Theme", theme)
    qml_path = Path(found_app.__file__).parent / "qml" / "main.qml"
    engine.load(str(qml_path))

    assert engine.rootObjects(), (
        f"QQmlApplicationEngine failed to load {qml_path} — "
        "check for QML syntax errors or missing imports"
    )
