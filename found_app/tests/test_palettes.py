"""
Tests for built-in theme palettes.

Covers:
- FOUND_DARK matches ThemeManager's current default palette
- ThemeManager sources its default palette from FOUND_DARK (as an
  independent copy, not a shared reference)
"""

from found_app.theme.palettes import FOUND_DARK
from found_app.theme.theme import ThemeManager


def test_theme_manager_default_palette_is_found_dark(qapp):
    theme = ThemeManager()

    assert theme._palette == FOUND_DARK
    assert theme._palette is not FOUND_DARK
