"""Tests for the AppTextField primitive.

Covers:
- AppTextField.qml exists and loads cleanly
- Default styling uses Theme.surface / Theme.border / Theme.text
- Focus state uses Theme.accent for the border
- Error/warning state uses Theme.warning for border and text
- leadingIcon, trailingIcon, trailingVisible, pill properties
- fontSize, fontCapitalization, backgroundColor properties
- submitted and escaped signals
- leadingIconItem and trailingBtn visibility
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


def test_focused_state_uses_accent_border(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml", focused=True)

    assert obj.property("borderColor") == QColor(theme.accent)


def test_error_state_uses_warning_color_for_border_and_text(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml", error=True)

    input_item = obj.findChild(QObject, "input")
    assert obj.property("borderColor") == QColor(theme.warning)
    assert input_item.property("color") == QColor(theme.warning)


# ---------------------------------------------------------------------------
# leadingIcon
# ---------------------------------------------------------------------------


def test_leading_icon_defaults_to_empty(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    assert obj.property("leadingIcon") == ""


def test_leading_icon_is_writable(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    obj.setProperty("leadingIcon", "+")
    assert obj.property("leadingIcon") == "+"


def test_leading_icon_item_hidden_when_icon_is_empty(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    item = obj.findChild(QObject, "leadingIconItem")
    assert item is not None
    assert item.property("visible") is False


def test_leading_icon_item_visible_when_icon_is_set(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml", leadingIcon="+")
    item = obj.findChild(QObject, "leadingIconItem")
    assert item is not None
    assert item.property("visible") is True


# ---------------------------------------------------------------------------
# trailingIcon / trailingVisible
# ---------------------------------------------------------------------------


def test_trailing_icon_defaults_to_return_glyph(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    assert obj.property("trailingIcon") == "↵"


def test_trailing_icon_is_writable(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    obj.setProperty("trailingIcon", "×")
    assert obj.property("trailingIcon") == "×"


def test_trailing_visible_defaults_to_false(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    assert obj.property("trailingVisible") is False


def test_trailing_visible_is_writable(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    obj.setProperty("trailingVisible", True)
    assert obj.property("trailingVisible") is True


def test_trailing_btn_hidden_by_default(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    item = obj.findChild(QObject, "trailingBtn")
    assert item is not None
    assert item.property("visible") is False


def test_trailing_btn_visible_when_trailing_visible_true(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml", trailingVisible=True)
    item = obj.findChild(QObject, "trailingBtn")
    assert item is not None
    assert item.property("visible") is True


def test_submit_icon_uses_theme_success(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    icon = obj.findChild(QObject, "submitIcon")
    assert icon is not None
    assert icon.property("color") == QColor(theme.success)


# ---------------------------------------------------------------------------
# pill
# ---------------------------------------------------------------------------


def test_pill_defaults_to_false(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    assert obj.property("pill") is False


def test_pill_is_writable(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    obj.setProperty("pill", True)
    assert obj.property("pill") is True


def test_non_pill_radius_is_4(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    assert obj.property("radius") == 4


def test_pill_radius_equals_half_height(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml", pill=True)
    h = obj.property("height")
    assert obj.property("radius") == h / 2


# ---------------------------------------------------------------------------
# fontSize / fontCapitalization
# ---------------------------------------------------------------------------


def test_font_size_is_writable(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    obj.setProperty("fontSize", theme.fontSizeMd)
    assert obj.property("fontSize") == theme.fontSizeMd


def test_font_capitalization_defaults_to_mixed_case(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    assert obj.property("fontCapitalization") == 0  # Font.MixedCase


def test_font_capitalization_is_writable(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    obj.setProperty("fontCapitalization", 3)  # Font.AllUppercase
    assert obj.property("fontCapitalization") == 3


# ---------------------------------------------------------------------------
# backgroundColor
# ---------------------------------------------------------------------------


def test_background_color_defaults_to_theme_surface(qapp, theme_qml_engine, theme):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    assert obj.property("backgroundColor") == QColor(theme.surface)


def test_background_color_is_writable(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    obj.setProperty("backgroundColor", QColor("transparent"))
    assert obj.property("backgroundColor") == QColor("transparent")


def test_unfocused_color_follows_background_color(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml",
                         backgroundColor=QColor("transparent"))
    assert obj.property("color") == QColor("transparent")


# ---------------------------------------------------------------------------
# signals
# ---------------------------------------------------------------------------


def test_has_submitted_signal(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    received = []
    obj.submitted.connect(lambda: received.append(1))
    assert isinstance(received, list)


def test_has_escaped_signal(qapp, theme_qml_engine):
    obj = load_component(theme_qml_engine, "primitives/AppTextField.qml")
    received = []
    obj.escaped.connect(lambda: received.append(1))
    assert isinstance(received, list)
