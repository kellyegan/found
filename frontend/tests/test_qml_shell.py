"""
Tests for the QML application shell — Commit 6.

Covers:
- SplashScreen.qml, MainRouter.qml, and AppWindow.qml exist
- Each component loads without QML errors
- SplashScreen exposes statusText (str) and hasError (bool) properties
- SplashScreen statusText value is readable after creation
- SplashScreen hasError defaults to False
- MainRouter exposes appState (str) property, defaulting to "Launching"
- AppWindow loads as a top-level window component
- main.qml still loads cleanly after being updated to use AppWindow
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent, QQmlApplicationEngine

import frontend
from frontend.theme.theme import ThemeManager

QML_DIR = Path(frontend.__file__).parent / "qml"


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def engine(qapp):
    """QQmlEngine with Theme registered. Holds a Python ref to ThemeManager so
    it is not garbage-collected while the fixture is active."""
    theme = ThemeManager()
    e = QQmlEngine()
    e.rootContext().setContextProperty("Theme", theme)
    # Attach theme to engine so Qt's ownership tree keeps it alive alongside e.
    theme.setParent(e)
    yield e
    e.clearComponentCache()


def load_component(engine, filename: str):
    """Load a QML file from QML_DIR, assert no errors, return instance.

    The created object is parented to the engine so it stays alive for the
    duration of the test even if the local QQmlComponent is collected.
    """
    path = QML_DIR / filename
    assert path.exists(), f"{filename} not found at {path}"

    component = QQmlComponent(engine, QUrl.fromLocalFile(str(path)))
    errors = [e.toString() for e in component.errors()]
    assert not errors, f"{filename} load errors: {errors}"
    assert component.status() == QQmlComponent.Status.Ready, (
        f"{filename} component status: {component.status()}"
    )

    obj = component.create(engine.rootContext())
    assert obj is not None, f"{filename} component.create() returned None"
    obj.setParent(engine)
    return obj


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------


def test_splash_screen_qml_exists():
    assert (QML_DIR / "SplashScreen.qml").exists()


def test_main_router_qml_exists():
    assert (QML_DIR / "MainRouter.qml").exists()


def test_app_window_qml_exists():
    assert (QML_DIR / "AppWindow.qml").exists()


# ---------------------------------------------------------------------------
# SplashScreen
# ---------------------------------------------------------------------------


def test_splash_screen_loads(engine):
    load_component(engine, "SplashScreen.qml")


def test_splash_screen_has_status_text_property(engine):
    obj = load_component(engine, "SplashScreen.qml")
    assert obj.property("statusText") is not None or obj.property("statusText") == ""


def test_splash_screen_status_text_defaults_to_empty(engine):
    obj = load_component(engine, "SplashScreen.qml")
    assert obj.property("statusText") == ""


def test_splash_screen_status_text_is_writable(engine):
    obj = load_component(engine, "SplashScreen.qml")
    obj.setProperty("statusText", "Connecting…")
    assert obj.property("statusText") == "Connecting…"


def test_splash_screen_has_error_defaults_to_false(engine):
    obj = load_component(engine, "SplashScreen.qml")
    assert obj.property("hasError") is False


def test_splash_screen_has_error_is_writable(engine):
    obj = load_component(engine, "SplashScreen.qml")
    obj.setProperty("hasError", True)
    assert obj.property("hasError") is True


# ---------------------------------------------------------------------------
# MainRouter
# ---------------------------------------------------------------------------


def test_main_router_loads(engine):
    load_component(engine, "MainRouter.qml")


def test_main_router_app_state_defaults_to_launching(engine):
    obj = load_component(engine, "MainRouter.qml")
    assert obj.property("appState") == "Launching"


def test_main_router_app_state_is_writable(engine):
    obj = load_component(engine, "MainRouter.qml")
    obj.setProperty("appState", "Ready")
    assert obj.property("appState") == "Ready"


# ---------------------------------------------------------------------------
# AppWindow & main.qml (integration)
# ---------------------------------------------------------------------------


def test_main_qml_loads_with_app_window(qapp):
    """main.qml (now using AppWindow) still loads via QQmlApplicationEngine."""
    theme = ThemeManager()
    e = QQmlApplicationEngine()
    e.rootContext().setContextProperty("Theme", theme)
    e.load(str(QML_DIR / "main.qml"))
    assert e.rootObjects(), "main.qml failed to load after AppWindow refactor"
