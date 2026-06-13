"""Tests for the AppText primitive.

Covers:
- AppText.qml exists and loads cleanly
- Default instance uses Theme.fontFamily / Theme.fontSizeMd / Theme.text
- muted/heading/label variants resolve to the expected tokens
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


def test_app_text_qml_exists():
    assert (QML_DIR / "primitives/AppText.qml").exists()


def test_app_text_loads(qapp, theme_qml_engine):
    load_component(theme_qml_engine, "primitives/AppText.qml")


def test_default_uses_theme_tokens(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppText.qml")
    font = obj.property("font")

    assert font.family() == theme.fontFamily
    assert font.pixelSize() == theme.fontSizeMd
    assert obj.property("color") == QColor(theme.text)


def test_muted_variant_uses_text_muted_color(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppText.qml", variant="muted")

    assert obj.property("color") == QColor(theme.textMuted)


def test_heading_variant_uses_font_size_lg(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppText.qml", variant="heading")
    font = obj.property("font")

    assert font.pixelSize() == theme.fontSizeLg


def test_label_variant_uses_font_size_sm(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppText.qml", variant="label")
    font = obj.property("font")

    assert font.pixelSize() == theme.fontSizeSm
