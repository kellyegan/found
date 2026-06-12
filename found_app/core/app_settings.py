from typing import Any

from PySide6.QtCore import QSettings


class AppSettings:
    """Thin wrapper around QSettings for local application preferences.

    Kept separate from the image library database -- this only stores
    per-machine UI preferences (e.g. theme selection).
    """

    def __init__(self, settings: QSettings):
        self._settings = settings

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.value(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings.setValue(key, value)
        self._settings.sync()
