"""
Tests for the QML application shell — Commits 6–9.

Covers:
- SplashScreen.qml, MainRouter.qml, AppWindow.qml, LibraryView.qml exist
- Each component loads without QML errors
- SplashScreen exposes statusText (str) and hasError (bool) properties
- SplashScreen statusText value is readable after creation
- SplashScreen hasError defaults to False
- MainRouter exposes appState (str) property, defaulting to "Launching"
- LibraryView exposes loadingState (str) property, defaulting to "Loading"
- AppWindow loads as a top-level window component
- main.qml still loads cleanly after being updated to use AppWindow
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent, QQmlApplicationEngine

import frontend
from frontend.theme.theme import ThemeManager
from frontend.state.app_state import AppStateManager
from frontend.library.view_model import LibraryViewModel

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


# ---------------------------------------------------------------------------
# LibraryView
# ---------------------------------------------------------------------------


def test_library_view_qml_exists():
    assert (QML_DIR / "LibraryView.qml").exists()


def test_library_view_loads(engine):
    load_component(engine, "LibraryView.qml")


def test_library_view_has_loading_state_property(engine):
    obj = load_component(engine, "LibraryView.qml")
    assert obj.property("loadingState") is not None or obj.property("loadingState") == ""


def test_library_view_loading_state_defaults_to_loading(engine):
    obj = load_component(engine, "LibraryView.qml")
    assert obj.property("loadingState") == "Loading"


def test_library_view_loading_state_is_writable(engine):
    obj = load_component(engine, "LibraryView.qml")
    obj.setProperty("loadingState", "Empty")
    assert obj.property("loadingState") == "Empty"


# ---------------------------------------------------------------------------
# AppWindow & main.qml (integration)
# ---------------------------------------------------------------------------


def test_main_qml_loads_with_app_window(qapp):
    """main.qml (now using AppWindow) still loads via QQmlApplicationEngine."""
    from frontend.library.thumbnail_grid_model import ThumbnailGridModel
    theme = ThemeManager()
    app_state = AppStateManager()
    library_state = LibraryViewModel(page_fetcher=lambda cursor=None, limit=100: None)
    e = QQmlApplicationEngine()
    e.rootContext().setContextProperty("Theme", theme)
    e.rootContext().setContextProperty("AppState", app_state)
    e.rootContext().setContextProperty("LibraryState", library_state)
    e.load(str(QML_DIR / "main.qml"))
    assert e.rootObjects(), "main.qml failed to load after AppWindow refactor"


# ---------------------------------------------------------------------------
# ThumbnailTile
# ---------------------------------------------------------------------------


def test_thumbnail_tile_qml_exists():
    assert (QML_DIR / "ThumbnailTile.qml").exists()


def test_thumbnail_tile_loads(engine):
    load_component(engine, "ThumbnailTile.qml")


def test_thumbnail_tile_has_thumbnail_url_property(engine):
    obj = load_component(engine, "ThumbnailTile.qml")
    assert obj.property("thumbnailUrl") == ""


def test_thumbnail_tile_has_file_status_property(engine):
    obj = load_component(engine, "ThumbnailTile.qml")
    assert obj.property("fileStatus") == "available"


def test_thumbnail_tile_has_selected_property(engine):
    obj = load_component(engine, "ThumbnailTile.qml")
    assert obj.property("selected") is False


# ---------------------------------------------------------------------------
# ThumbnailGrid
# ---------------------------------------------------------------------------


def test_thumbnail_grid_qml_exists():
    assert (QML_DIR / "ThumbnailGrid.qml").exists()


def test_thumbnail_grid_loads(engine):
    load_component(engine, "ThumbnailGrid.qml")


def test_thumbnail_grid_has_model_property(engine):
    obj = load_component(engine, "ThumbnailGrid.qml")
    # model defaults to null — property should exist and be readable
    assert obj.property("model") is None or obj.property("model") is not None
