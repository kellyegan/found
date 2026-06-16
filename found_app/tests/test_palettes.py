"""
Tests for built-in theme palettes.

Covers:
- FOUND_DARK matches ThemeManager's current default palette
- ThemeManager sources its default palette from FOUND_DARK (as an
  independent copy, not a shared reference)
"""

from found_app.theme.palettes import FOUND_DARK, FOUND_LIGHT, THEMES
from found_app.theme.theme import ThemeManager


def test_theme_manager_default_palette_is_found_dark(qapp, monkeypatch):
    import found_app.theme.theme as theme_module

    monkeypatch.setattr(theme_module.darkdetect, "theme", lambda: "Dark")
    theme = ThemeManager()

    assert theme._palette == FOUND_DARK
    assert theme._palette is not FOUND_DARK


def test_found_light_has_same_keys_as_found_dark_and_differs_in_color():
    assert set(FOUND_LIGHT.keys()) == set(FOUND_DARK.keys())
    assert FOUND_LIGHT["background"] != FOUND_DARK["background"]
    assert FOUND_LIGHT["text"] != FOUND_DARK["text"]


def test_themes_registry_groups_found_palettes():
    assert THEMES["Found"]["dark"] is FOUND_DARK
    assert THEMES["Found"]["light"] is FOUND_LIGHT


def test_found_light_typography_and_spacing_match_found_dark():
    shared_keys = [
        "fontFamily",
        "fontSizeSm",
        "fontSizeMd",
        "fontSizeLg",
        "fontSizeXl",
        "overlayWidth",
        "horizontalTextMargin",
        "horizontalTextPadding",
        "horizontalMargin",
        "spacingXxs",
        "spacingXs",
        "spacingSm",
        "spacingMd",
        "spacingLg",
        "spacingXl",
    ]
    for key in shared_keys:
        assert FOUND_LIGHT[key] == FOUND_DARK[key], key


def test_themes_registry_includes_sepia_with_required_keys():
    assert "Sepia" in THEMES
    sepia = THEMES["Sepia"]
    assert set(sepia.keys()) == {"light", "dark"}

    required_keys = set(FOUND_DARK.keys())
    assert set(sepia["light"].keys()) == required_keys
    assert set(sepia["dark"].keys()) == required_keys
    assert sepia["light"]["background"] != sepia["dark"]["background"]
