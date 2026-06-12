"""
Tests for ThemeManager.

Covers:
- all expected color properties are defined and are valid hex strings
- all expected typography properties are defined and positive
- all expected spacing properties are defined and positive
- font sizes increase from sm → md → lg → xl
- spacing values increase from xs → sm → md → lg → xl
- theme properties are readable from QML via context property
"""

import re
import pytest
from PySide6.QtCore import QUrl

from found_app.theme.theme import ThemeManager


HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$")

COLOR_PROPS = ["background", "surface", "text", "textMuted", "accent", "border"]
FONT_SIZE_PROPS = ["fontSizeSm", "fontSizeMd", "fontSizeLg", "fontSizeXl"]
TYPOGRAPHY_PROPS = ["fontFamily"] + FONT_SIZE_PROPS
SPACING_PROPS = ["spacingXs", "spacingSm", "spacingMd", "spacingLg", "spacingXl"]
LAYOUT_PROPS = ["overlayWidth"]


# ---------------------------------------------------------------------------
# Color properties
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prop", COLOR_PROPS)
def test_color_property_is_valid_hex(qapp, prop):
    theme = ThemeManager()
    value = getattr(theme, prop)
    assert isinstance(value, str), f"{prop} should be a string"
    assert HEX_COLOR.match(value), f"{prop} value {value!r} is not a valid hex color"


@pytest.mark.parametrize("prop", COLOR_PROPS)
def test_color_property_reflects_palette_change(qapp, prop):
    theme = ThemeManager()
    new_value = "#123456"

    theme._palette[prop] = new_value

    assert getattr(theme, prop) == new_value


# ---------------------------------------------------------------------------
# Typography properties
# ---------------------------------------------------------------------------


def test_font_family_is_non_empty_string(qapp):
    theme = ThemeManager()
    assert isinstance(theme.fontFamily, str)
    assert len(theme.fontFamily) > 0


@pytest.mark.parametrize("prop", FONT_SIZE_PROPS)
def test_font_size_property_is_positive_int(qapp, prop):
    theme = ThemeManager()
    value = getattr(theme, prop)
    assert isinstance(value, int), f"{prop} should be an int"
    assert value > 0, f"{prop} should be positive"


def test_font_sizes_are_strictly_increasing(qapp):
    theme = ThemeManager()
    assert theme.fontSizeSm < theme.fontSizeMd < theme.fontSizeLg < theme.fontSizeXl


@pytest.mark.parametrize("prop", TYPOGRAPHY_PROPS)
def test_typography_property_reflects_palette_change(qapp, prop):
    theme = ThemeManager()
    new_value = "Comic Sans" if prop == "fontFamily" else 999

    theme._palette[prop] = new_value

    assert getattr(theme, prop) == new_value


# ---------------------------------------------------------------------------
# Spacing properties
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prop", SPACING_PROPS)
def test_spacing_property_is_positive_int(qapp, prop):
    theme = ThemeManager()
    value = getattr(theme, prop)
    assert isinstance(value, int), f"{prop} should be an int"
    assert value > 0, f"{prop} should be positive"


def test_spacing_values_are_strictly_increasing(qapp):
    theme = ThemeManager()
    assert (
        theme.spacingXs
        < theme.spacingSm
        < theme.spacingMd
        < theme.spacingLg
        < theme.spacingXl
    )


# ---------------------------------------------------------------------------
# Layout properties
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prop", LAYOUT_PROPS)
def test_layout_property_is_positive_int(qapp, prop):
    theme = ThemeManager()
    value = getattr(theme, prop)
    assert isinstance(value, int), f"{prop} should be an int"
    assert value > 0, f"{prop} should be positive"


def test_overlay_width_matches_sidebar_and_metadata_panel(qapp):
    theme = ThemeManager()
    assert theme.overlayWidth == 260


# ---------------------------------------------------------------------------
# QML integration
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Reactive palette
# ---------------------------------------------------------------------------


def test_palette_changed_signal_emits(qapp):
    theme = ThemeManager()
    received = []
    theme.paletteChanged.connect(lambda: received.append(True))

    theme.paletteChanged.emit()

    assert received == [True]


def test_theme_properties_accessible_in_qml(qapp, tmp_path):
    from PySide6.QtQml import QQmlApplicationEngine

    qml_file = tmp_path / "test_theme.qml"
    qml_file.write_text(
        """
        import QtQuick
        Item {
            property string bg: Theme.background
            property int fontSize: Theme.fontSizeMd
            property int spacing: Theme.spacingMd
        }
        """
    )

    theme = ThemeManager()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("Theme", theme)
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    roots = engine.rootObjects()
    assert roots, "QML failed to load with Theme context property"
    assert roots[0].property("bg") == theme.background
    assert roots[0].property("fontSize") == theme.fontSizeMd
    assert roots[0].property("spacing") == theme.spacingMd
