"""Tests for the HoverTooltip QML component.

Covers:
- HoverTooltip.qml exists and loads cleanly
- Exposes a text property
- Visibility is controlled by the caller
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent

import found_app
from found_app.theme.theme import ThemeManager

QML_DIR = Path(found_app.__file__).parent / "qml"


@pytest.fixture
def engine(qapp):
    theme = ThemeManager()
    e = QQmlEngine()
    e.rootContext().setContextProperty("Theme", theme)
    theme.setParent(e)
    yield e
    e.clearComponentCache()


def load_component(engine, filename: str):
    path = QML_DIR / filename
    assert path.exists(), f"{filename} not found at {path}"
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(path)))
    errors = [err.toString() for err in component.errors()]
    assert not errors, f"{filename} load errors: {errors}"
    assert component.status() == QQmlComponent.Status.Ready, (
        f"{filename} status: {component.status()}"
    )
    obj = component.create(engine.rootContext())
    assert obj is not None, f"{filename} create() returned None"
    obj.setParent(engine)
    return obj


# ---------------------------------------------------------------------------
# Loads
# ---------------------------------------------------------------------------


def test_hover_tooltip_qml_exists():
    assert (QML_DIR / "components/HoverTooltip.qml").exists()


def test_hover_tooltip_loads(engine):
    load_component(engine, "components/HoverTooltip.qml")


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def test_text_defaults_to_empty(engine):
    obj = load_component(engine, "components/HoverTooltip.qml")
    assert obj.property("text") == ""


def test_text_is_writable(engine):
    obj = load_component(engine, "components/HoverTooltip.qml")
    obj.setProperty("text", "File missing — click to locate")
    assert obj.property("text") == "File missing — click to locate"


def test_visible_defaults_to_true(engine):
    obj = load_component(engine, "components/HoverTooltip.qml")
    assert obj.property("visible") is True


def test_visible_is_writable(engine):
    obj = load_component(engine, "components/HoverTooltip.qml")
    obj.setProperty("visible", False)
    assert obj.property("visible") is False
