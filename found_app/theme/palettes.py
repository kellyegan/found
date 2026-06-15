"""Built-in design token palettes."""

FOUND_DARK = {
    "background": "#000000",
    "surface": "#1a1a1a",
    "text": "#e8e8e8",
    "textMuted": "#777777",
    "accent": "#eeeeff",
    "border": "#2a2a2a",
    "warning": "#ff4444",
    "error": "#ff8800",
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

FOUND_LIGHT = {
    "background": "#f5f5f5",
    "surface": "#ffffff",
    "text": "#1a1a1a",
    "textMuted": "#777777",
    "accent": "#5555cc",
    "border": "#dddddd",
    "warning": "#ff4444",
    "error": "#ff8800",
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

# Named theme families, each grouping a light and dark palette variant.
THEMES = {
    "Found": {"light": FOUND_LIGHT, "dark": FOUND_DARK},
}
