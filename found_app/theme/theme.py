from PySide6.QtCore import QObject, Property, Signal


class ThemeManager(QObject):
    """Exposes design tokens as Qt properties for use as a QML context property."""

    paletteChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = {
            "background": "#000000",
            "surface": "#1a1a1a",
            "text": "#e8e8e8",
            "textMuted": "#777777",
            "accent": "#eeeeff",
            "border": "#2a2a2a",
            "fontFamily": "Inter",
            "fontSizeSm": 12,
            "fontSizeMd": 16,
            "fontSizeLg": 24,
            "fontSizeXl": 48,
            "overlayWidth": 260,
            "horizontalTextMargin": 30,
            "horizontalTextPadding": 12,
            "horizontalMargin": 18,
            "spacingXs": 4,
            "spacingSm": 8,
            "spacingMd": 16,
            "spacingLg": 24,
            "spacingXl": 40,
        }

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
