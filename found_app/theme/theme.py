from PySide6.QtCore import QObject, Property, Signal

from found_app.theme.palettes import FOUND_DARK


class ThemeManager(QObject):
    """Exposes design tokens as Qt properties for use as a QML context property."""

    paletteChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = dict(FOUND_DARK)

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

    @Property(str, constant=True)
    def warningColor(self) -> str:
        return "#ff4444"

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
