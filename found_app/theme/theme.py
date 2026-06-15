import darkdetect
from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
from PySide6.QtQml import QQmlEngine, qmlRegisterSingletonInstance

from found_app.theme.palettes import THEMES


class ThemeManager(QObject):
    """Exposes design tokens as Qt properties for use as a QML context property."""

    paletteChanged = Signal()

    # How often to re-check darkdetect.theme() while mode == "system".
    SYSTEM_POLL_INTERVAL_MS = 2000

    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self._settings = settings
        self._theme_name = (
            self._settings.get("theme/name", "Found") if self._settings else "Found"
        )
        self._mode = (
            self._settings.get("theme/mode", "system") if self._settings else "system"
        )
        self._system_variant = None
        self._apply_palette()

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(self.SYSTEM_POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll_system_theme)
        if self._mode == "system":
            self._poll_timer.start()

    def _resolve_variant(self) -> str:
        if self._mode in ("light", "dark"):
            return self._mode
        self._system_variant = "light" if darkdetect.theme() == "Light" else "dark"
        return self._system_variant

    def _apply_palette(self) -> None:
        theme_family = THEMES.get(self._theme_name, THEMES["Found"])
        variant = self._resolve_variant()
        self.setPalette(theme_family[variant])

    def _poll_system_theme(self) -> None:
        """Re-check the OS theme and re-apply the palette if it changed.

        Only meaningful in "system" mode — the cached `_system_variant` is
        only updated by `_resolve_variant` when `_mode == "system"`.
        """
        if self._mode != "system":
            return
        current = "light" if darkdetect.theme() == "Light" else "dark"
        if current != self._system_variant:
            self._apply_palette()

    @Property(str, notify=paletteChanged)
    def themeName(self) -> str:
        return self._theme_name

    @Slot(str)
    def setThemeName(self, name: str) -> None:
        self._theme_name = name
        if self._settings:
            self._settings.set("theme/name", name)
        self._apply_palette()

    @Property(str, notify=paletteChanged)
    def mode(self) -> str:
        return self._mode

    @Slot(str)
    def setMode(self, mode: str) -> None:
        self._mode = mode
        if self._settings:
            self._settings.set("theme/mode", mode)
        self._apply_palette()

    def setPalette(self, palette: dict) -> None:
        self._palette = dict(palette)
        self.paletteChanged.emit()

    # ------------------------------------------------------------------
    # Colors
    # ------------------------------------------------------------------

    @Property(str, notify=paletteChanged)
    def background(self) -> str:
        return self._palette["background"]

    @Property(str, notify=paletteChanged)
    def surface(self) -> str:
        return self._palette["surface"]

    @Property(str, notify=paletteChanged)
    def text(self) -> str:
        return self._palette["text"]

    @Property(str, notify=paletteChanged)
    def textMuted(self) -> str:
        return self._palette["textMuted"]

    @Property(str, notify=paletteChanged)
    def warning(self) -> str:
        return self._palette["warning"]

    @Property(str, notify=paletteChanged)
    def error(self) -> str:
        return self._palette["error"]

    @Property(str, notify=paletteChanged)
    def success(self) -> str:
        return self._palette["success"]

    @Property(str, notify=paletteChanged)
    def accent(self) -> str:
        return self._palette["accent"]

    @Property(str, notify=paletteChanged)
    def border(self) -> str:
        return self._palette["border"]

    # ------------------------------------------------------------------
    # Typography
    # ------------------------------------------------------------------

    @Property(str, notify=paletteChanged)
    def fontFamily(self) -> str:
        return self._palette["fontFamily"]

    @Property(int, notify=paletteChanged)
    def fontSizeSm(self) -> int:
        return self._palette["fontSizeSm"]

    @Property(int, notify=paletteChanged)
    def fontSizeMd(self) -> int:
        return self._palette["fontSizeMd"]

    @Property(int, notify=paletteChanged)
    def fontSizeLg(self) -> int:
        return self._palette["fontSizeLg"]

    @Property(int, notify=paletteChanged)
    def fontSizeXl(self) -> int:
        return self._palette["fontSizeXl"]

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    @Property(int, notify=paletteChanged)
    def overlayWidth(self) -> int:
        return self._palette["overlayWidth"]

    # ------------------------------------------------------------------
    # Spacing
    # ------------------------------------------------------------------

    @Property(int, notify=paletteChanged)
    def horizontalTextMargin(self) -> int:
        return self._palette["horizontalTextMargin"]

    @Property(int, notify=paletteChanged)
    def horizontalTextPadding(self) -> int:
        return self._palette["horizontalTextPadding"]

    @Property(int, notify=paletteChanged)
    def horizontalMargin(self) -> int:
        return self._palette["horizontalMargin"]

    @Property(int, notify=paletteChanged)
    def spacingXs(self) -> int:
        return self._palette["spacingXs"]

    @Property(int, notify=paletteChanged)
    def spacingSm(self) -> int:
        return self._palette["spacingSm"]

    @Property(int, notify=paletteChanged)
    def spacingMd(self) -> int:
        return self._palette["spacingMd"]

    @Property(int, notify=paletteChanged)
    def spacingLg(self) -> int:
        return self._palette["spacingLg"]

    @Property(int, notify=paletteChanged)
    def spacingXl(self) -> int:
        return self._palette["spacingXl"]


_registered_theme: ThemeManager | None = None


def register_theme_singleton(theme: ThemeManager) -> ThemeManager:
    """Expose a `ThemeManager` to QML as the `Found.Theme` 1.0 `Theme` singleton.

    Registration is process-wide and one-time: QML's singleton type registry
    does not support swapping the instance behind an already-registered
    type, so repeated calls are no-ops and return the instance that was
    registered first.

    Ownership is set to CppOwnership before registering so the instance can
    be accessed from multiple QQmlEngines (e.g. one per test) — without this,
    Qt ties the singleton to whichever engine first reads a property and
    raises "Singleton registered by registerSingletonInstance must only be
    accessed from one engine" for any other engine.
    """
    global _registered_theme
    if _registered_theme is None:
        QQmlEngine.setObjectOwnership(theme, QQmlEngine.ObjectOwnership.CppOwnership)
        qmlRegisterSingletonInstance(ThemeManager, "Found.Theme", 1, 0, "Theme", theme)
        _registered_theme = theme
    return _registered_theme
