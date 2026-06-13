"""Tests for the AppButton primitive.

Covers:
- AppButton.qml exists and loads cleanly
- Default state uses Theme.surface; hover state uses Theme.accent
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent

import found_app
from found_app.theme.theme import ThemeManager, register_theme_singleton

QML_DIR = Path(found_app.__file__).parent / "qml"


def load_component(engine, filename: str, **properties):
    path = QML_DIR / filename
    assert path.exists(), f"{filename} not found at {path}"
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(path)))
    errors = [err.toString() for err in component.errors()]
    assert not errors, f"{filename} load errors: {errors}"
    obj = component.create()
    assert obj is not None, f"{filename} create() returned None"
    obj.setParent(engine)
    for key, value in properties.items():
        obj.setProperty(key, value)
    return obj


@pytest.fixture
def theme(qapp):
    return register_theme_singleton(ThemeManager())


def test_app_button_qml_exists():
    assert (QML_DIR / "primitives/AppButton.qml").exists()


def test_app_button_loads(qapp, theme_qml_engine):
    load_component(theme_qml_engine, "primitives/AppButton.qml")


def test_default_state_uses_surface(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppButton.qml")

    assert obj.property("color") == QColor(theme.surface)


def test_hover_state_uses_accent(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppButton.qml", hovered=True)

    assert obj.property("color") == QColor(theme.accent)
