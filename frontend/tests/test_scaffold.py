"""
Scaffold tests for Commit 1.

Verifies the minimum contracts that must hold before any other frontend
code can be written:
  - the `frontend` package is importable
  - `python -m frontend` has a callable entry point
  - the root QML file exists at the path the entry point will use
  - the QML engine can load that file without errors in headless mode
"""

import os
from pathlib import Path


def test_frontend_package_importable():
    import frontend  # noqa: F401


def test_main_entry_point_is_callable():
    from frontend.__main__ import main

    assert callable(main)


def test_main_qml_exists():
    import frontend

    qml_path = Path(frontend.__file__).parent / "qml" / "main.qml"
    assert qml_path.exists(), f"main.qml not found at {qml_path}"


def test_qml_engine_loads_main(qapp):
    from PySide6.QtQml import QQmlApplicationEngine
    import frontend

    engine = QQmlApplicationEngine()
    qml_path = Path(frontend.__file__).parent / "qml" / "main.qml"
    engine.load(str(qml_path))

    assert engine.rootObjects(), (
        f"QQmlApplicationEngine failed to load {qml_path} — "
        "check for QML syntax errors or missing imports"
    )
