"""Tests for the Chip primitive.

Covers:
- Chip.qml exists and loads cleanly
- Each chipState (off/include/exclude/mixed/drag-hover) resolves color and
  border color to the expected theme token
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


def test_chip_qml_exists():
    assert (QML_DIR / "primitives/Chip.qml").exists()


def test_chip_loads(qapp, theme_qml_engine):
    load_component(theme_qml_engine, "primitives/Chip.qml")


CHIP_STATE_TOKENS = [
    ("off", "border"),
    ("include", "accent"),
    ("exclude", "warningColor"),
    ("mixed", "surface"),
    ("drag-hover", "accent"),
]


@pytest.mark.parametrize("chip_state, token", CHIP_STATE_TOKENS)
def test_chip_state_resolves_color_token(qapp, theme_qml_engine, theme, chip_state, token):
    obj = load_component(theme_qml_engine, "primitives/Chip.qml", chipState=chip_state)

    expected = QColor(getattr(theme, token))
    assert obj.property("color") == expected
    assert obj.property("borderColor") == expected
