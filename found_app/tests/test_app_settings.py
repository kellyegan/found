"""
Tests for AppSettings.

Covers:
- set/get round-trips a value
- get returns a provided default when the key is unset
- values persist across separate AppSettings instances backed by the
  same store
"""

from PySide6.QtCore import QSettings

from found_app.core.app_settings import AppSettings


def _settings(tmp_path):
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


def test_set_then_get_round_trips(tmp_path):
    settings = AppSettings(_settings(tmp_path))

    settings.set("theme/name", "Found")

    assert settings.get("theme/name") == "Found"


def test_get_returns_default_when_unset(tmp_path):
    settings = AppSettings(_settings(tmp_path))

    assert settings.get("theme/mode", "system") == "system"


def test_persists_across_instances(tmp_path):
    path = tmp_path / "settings.ini"

    AppSettings(QSettings(str(path), QSettings.Format.IniFormat)).set("theme/name", "Found")
    restored = AppSettings(QSettings(str(path), QSettings.Format.IniFormat))

    assert restored.get("theme/name") == "Found"
