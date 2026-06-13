"""Tests for the AppTextField primitive.

Covers:
- AppTextField.qml exists and loads cleanly
- Default styling uses Theme.surface / Theme.border / Theme.text
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QObject, QUrl
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


def test_app_textfield_qml_exists():
    assert (QML_DIR / "primitives/AppTextField.qml").exists()


def test_app_textfield_loads(qapp, theme_qml_engine):
    load_component(theme_qml_engine, "primitives/AppTextField.qml")


def test_default_styling_matches_tokens(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")

    assert obj.property("color") == QColor(theme.surface)
    assert obj.property("borderColor") == QColor(theme.border)

    input_item = obj.findChild(QObject, "input")
    assert input_item.property("color") == QColor(theme.text)
