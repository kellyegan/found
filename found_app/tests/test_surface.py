"""Tests for the Surface primitive.

Covers:
- Surface.qml exists and loads cleanly
- Default instance exposes Theme.surface / Theme.border / spacing tokens
  for color, border, radius, and padding
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


def test_surface_qml_exists():
    assert (QML_DIR / "primitives/Surface.qml").exists()


def test_surface_loads(qapp, theme_qml_engine):
    load_component(theme_qml_engine, "primitives/Surface.qml")


def test_default_exposes_theme_tokens(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/Surface.qml")

    assert obj.property("color") == QColor(theme.surface)
    assert obj.property("borderColor") == QColor(theme.border)
    assert obj.property("radius") == theme.spacingXs
    assert obj.property("padding") == theme.spacingMd
