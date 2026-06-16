"""Tests for the AppButton primitive.

Covers:
- AppButton.qml exists and loads cleanly
- Default state uses Theme.surface; hover state uses Theme.accent
- Pressed state uses Theme.border; disabled state mutes the label
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


def test_pressed_state_uses_border(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppButton.qml", pressed=True)

    assert obj.property("color") == QColor(theme.border)


def test_disabled_state_mutes_label(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppButton.qml", enabled=False)

    label = obj.findChild(QObject, "label")
    assert label.property("color") == QColor(theme.textMuted)


# ---------------------------------------------------------------------------
# AppButton — variant: "icon"
# ---------------------------------------------------------------------------


def test_app_button_variant_defaults_to_default(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppButton.qml")
    assert obj.property("variant") == "default"


def test_app_button_icon_variant_default_color_is_transparent(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppButton.qml", variant="icon")
    assert obj.property("color") == QColor("transparent")


def test_app_button_icon_variant_hover_color_is_border(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppButton.qml", variant="icon", hovered=True)
    assert obj.property("color") == QColor(theme.border)


def test_app_button_icon_variant_label_color_is_muted(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppButton.qml", variant="icon")
    label = obj.findChild(QObject, "label")
    assert label.property("color") == QColor(theme.textMuted)
