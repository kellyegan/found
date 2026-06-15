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
from PySide6.QtCore import QSettings, QUrl

from found_app.core.app_settings import AppSettings
from found_app.theme.palettes import FOUND_DARK, FOUND_LIGHT
from found_app.theme.theme import ThemeManager


def _app_settings(tmp_path, name="settings.ini"):
    return AppSettings(QSettings(str(tmp_path / name), QSettings.Format.IniFormat))


HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$")

COLOR_PROPS = ["background", "surface", "text", "textMuted", "accent", "border", "warning", "error", "success"]
FONT_SIZE_PROPS = ["fontSizeSm", "fontSizeMd", "fontSizeLg", "fontSizeXl"]
TYPOGRAPHY_PROPS = ["fontFamily"] + FONT_SIZE_PROPS
SPACING_PROPS = ["spacingXs", "spacingSm", "spacingMd", "spacingLg", "spacingXl"]
LAYOUT_PROPS = ["overlayWidth"]
SPACING_LAYOUT_PROPS = SPACING_PROPS + LAYOUT_PROPS + [
    "horizontalMargin",
    "horizontalTextMargin",
    "horizontalTextPadding",
]


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


@pytest.mark.parametrize("prop", SPACING_LAYOUT_PROPS)
def test_spacing_layout_property_reflects_palette_change(qapp, prop):
    theme = ThemeManager()
    new_value = 999

    theme._palette[prop] = new_value

    assert getattr(theme, prop) == new_value


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


def test_theme_name_defaults_to_found(qapp):
    theme = ThemeManager()
    assert theme.themeName == "Found"


def test_set_theme_name_persists_and_restores(qapp, tmp_path):
    theme = ThemeManager(settings=_app_settings(tmp_path))
    theme.setThemeName("Found")

    restored = ThemeManager(settings=_app_settings(tmp_path))
    assert restored.themeName == "Found"


def test_mode_defaults_to_system(qapp):
    theme = ThemeManager()
    assert theme.mode == "system"


def test_set_mode_persists_and_restores(qapp, tmp_path):
    theme = ThemeManager(settings=_app_settings(tmp_path))
    theme.setMode("dark")

    restored = ThemeManager(settings=_app_settings(tmp_path))
    assert restored.mode == "dark"


def test_system_mode_resolves_to_light_palette_via_darkdetect(qapp, monkeypatch):
    import found_app.theme.theme as theme_module

    monkeypatch.setattr(theme_module.darkdetect, "theme", lambda: "Light")

    theme = ThemeManager()

    assert theme.background == FOUND_LIGHT["background"]


def test_system_mode_resolves_to_dark_palette_via_darkdetect(qapp, monkeypatch):
    import found_app.theme.theme as theme_module

    monkeypatch.setattr(theme_module.darkdetect, "theme", lambda: "Dark")

    theme = ThemeManager()

    assert theme.background == FOUND_DARK["background"]


def test_system_mode_poll_detects_os_theme_change(qapp, monkeypatch):
    import found_app.theme.theme as theme_module

    monkeypatch.setattr(theme_module.darkdetect, "theme", lambda: "Light")
    theme = ThemeManager()
    assert theme.background == FOUND_LIGHT["background"]

    received = []
    theme.paletteChanged.connect(lambda: received.append(True))

    monkeypatch.setattr(theme_module.darkdetect, "theme", lambda: "Dark")
    theme._poll_system_theme()

    assert received == [True]
    assert theme.background == FOUND_DARK["background"]


def test_system_mode_poll_does_nothing_when_os_theme_unchanged(qapp, monkeypatch):
    import found_app.theme.theme as theme_module

    monkeypatch.setattr(theme_module.darkdetect, "theme", lambda: "Light")
    theme = ThemeManager()

    received = []
    theme.paletteChanged.connect(lambda: received.append(True))

    theme._poll_system_theme()

    assert received == []


def test_poll_timer_runs_in_system_mode(qapp):
    theme = ThemeManager()  # mode defaults to "system"
    assert theme._poll_timer.isActive() is True


def test_poll_timer_does_not_run_outside_system_mode(qapp, tmp_path):
    theme = ThemeManager(settings=_app_settings(tmp_path))
    theme.setMode("dark")

    fresh = ThemeManager(settings=_app_settings(tmp_path))
    assert fresh.mode == "dark"
    assert fresh._poll_timer.isActive() is False


def test_poll_timer_start_stop_follows_set_mode(qapp):
    theme = ThemeManager()  # mode defaults to "system"
    assert theme._poll_timer.isActive() is True

    theme.setMode("dark")
    assert theme._poll_timer.isActive() is False

    theme.setMode("light")
    assert theme._poll_timer.isActive() is False

    theme.setMode("system")
    assert theme._poll_timer.isActive() is True


def test_poll_timer_triggers_poll_on_timeout(qapp, monkeypatch):
    import found_app.theme.theme as theme_module

    monkeypatch.setattr(theme_module.darkdetect, "theme", lambda: "Light")
    theme = ThemeManager()

    received = []
    theme.paletteChanged.connect(lambda: received.append(True))

    monkeypatch.setattr(theme_module.darkdetect, "theme", lambda: "Dark")
    theme._poll_timer.timeout.emit()

    assert received == [True]
    assert theme.background == FOUND_DARK["background"]


def test_set_palette_swaps_active_palette_and_notifies(qapp):
    theme = ThemeManager()
    received = []
    theme.paletteChanged.connect(lambda: received.append(True))

    theme.setPalette(FOUND_LIGHT)

    assert theme.background == FOUND_LIGHT["background"]
    assert received == [True]


def test_theme_registered_as_qml_singleton(qapp, theme_qml_engine, tmp_path):
    from PySide6.QtQml import QQmlComponent
    from found_app.theme.theme import register_theme_singleton

    theme = ThemeManager()
    active_theme = register_theme_singleton(theme)

    qml_file = tmp_path / "test_singleton.qml"
    qml_file.write_text(
        """
        import QtQuick
        import Found.Theme 1.0
        Item {
            property string bg: Theme.background
        }
        """
    )

    # qmlRegisterSingletonInstance binds the singleton to whichever engine
    # first reads one of its properties; reuse the engine that conftest's
    # qapp fixture already bound it to (see theme_qml_engine) — a fresh
    # QQmlEngine here would get a null singleton with a "must only be
    # accessed from one engine" warning.
    component = QQmlComponent(theme_qml_engine, QUrl.fromLocalFile(str(qml_file)))
    errors = [e.toString() for e in component.errors()]
    assert not errors, f"QML errors: {errors}"

    obj = component.create()
    assert obj is not None
    assert obj.property("bg") == active_theme.background


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
