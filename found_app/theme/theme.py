from PySide6.QtCore import QObject, Property


class ThemeManager(QObject):
    """Exposes design tokens as Qt properties for use as a QML context property."""

    def __init__(self, parent=None):
        super().__init__(parent)

    # ------------------------------------------------------------------
    # Colors
    # ------------------------------------------------------------------

    @Property(str, constant=True)
    def background(self) -> str:
        return "#0d0d0d"

    @Property(str, constant=True)
    def surface(self) -> str:
        return "#1a1a1a"

    @Property(str, constant=True)
    def text(self) -> str:
        return "#e8e8e8"

    @Property(str, constant=True)
    def textMuted(self) -> str:
        return "#777777"

    @Property(str, constant=True)
    def accent(self) -> str:
        return "#4a9eff"

    @Property(str, constant=True)
    def border(self) -> str:
        return "#2a2a2a"

    # ------------------------------------------------------------------
    # Typography
    # ------------------------------------------------------------------

    @Property(str, constant=True)
    def fontFamily(self) -> str:
        return "Inter, -apple-system, sans-serif"

    @Property(int, constant=True)
    def fontSizeSm(self) -> int:
        return 12

    @Property(int, constant=True)
    def fontSizeMd(self) -> int:
        return 16

    @Property(int, constant=True)
    def fontSizeLg(self) -> int:
        return 24

    @Property(int, constant=True)
    def fontSizeXl(self) -> int:
        return 48

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    @Property(int, constant=True)
    def overlayWidth(self) -> int:
        return 260

    # ------------------------------------------------------------------
    # Spacing
    # ------------------------------------------------------------------

    @Property(int, constant=True)
    def spacingXs(self) -> int:
        return 4

    @Property(int, constant=True)
    def spacingSm(self) -> int:
        return 8

    @Property(int, constant=True)
    def spacingMd(self) -> int:
        return 16

    @Property(int, constant=True)
    def spacingLg(self) -> int:
        return 24

    @Property(int, constant=True)
    def spacingXl(self) -> int:
        return 40
