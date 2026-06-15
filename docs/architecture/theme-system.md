# FOUND — Theme System

## Purpose

Found's theme system gives every screen a single, reactive source of
design tokens (colors, typography, spacing) so that:

- the whole UI can switch between named theme families (e.g. "Found",
  "Sepia") and between light/dark variants — live, without restarting.
- the active theme/mode follows the OS appearance when set to "system",
  and updates while the app is running.
- the user's choice persists across launches.
- QML files never hardcode colors, font sizes, or spacing — they read
  from `Theme.*` or build on shared primitives.

This document describes how the pieces fit together and how to add a
new theme.

---

## 1. Components

### `ThemeManager` (`found_app/theme/theme.py`)

A `QObject` exposing the active palette as Qt `Property`s (e.g.
`Theme.background`, `Theme.accent`, `Theme.fontSizeMd`,
`Theme.spacingMd`). All properties share a single `paletteChanged`
signal — changing the active palette emits one signal and every
binding across the app re-evaluates.

Key state:

- `themeName` — the active theme family (e.g. `"Found"`, `"Sepia"`).
  Changed via `setThemeName(name)`.
- `mode` — `"light"`, `"dark"`, or `"system"`. Changed via
  `setMode(mode)`.
- `availableThemes()` — returns `list(THEMES.keys())`, used to drive
  the theme picker in Settings.

When `mode == "system"`, `ThemeManager` resolves the variant via
`darkdetect.theme()` and polls it on a `QTimer`
(`SYSTEM_POLL_INTERVAL_MS`) so the UI follows OS appearance changes
while running. The poll timer only runs in `system` mode — it starts
and stops in `setMode()`.

Both `themeName` and `mode` are persisted via an injected `AppSettings`
(see below) and restored on the next launch.

### Palettes (`found_app/theme/palettes.py`)

Each palette is a flat `dict` containing the full token set: colors
(`background`, `surface`, `text`, `textMuted`, `accent`, `border`,
`warning`, `error`, `success`), typography (`fontFamily`,
`fontSizeSm/Md/Lg/Xl`), and spacing/layout
(`spacingXs/Sm/Md/Lg/Xl`, `overlayWidth`, `horizontalMargin`,
`horizontalTextMargin`, `horizontalTextPadding`).

Palettes are grouped into named **theme families** in the `THEMES`
registry:

```python
THEMES = {
    "Found": {"light": FOUND_LIGHT, "dark": FOUND_DARK},
    "Sepia": {"light": SEPIA_LIGHT, "dark": SEPIA_DARK},
}
```

`ThemeManager._apply_palette()` looks up `THEMES[self._theme_name]`
and picks the `light`/`dark` variant based on `mode` (resolving
`"system"` via `darkdetect`), then calls `setPalette(...)`, which
swaps `self._palette` and emits `paletteChanged`.

### `AppSettings` (`found_app/core/app_settings.py`)

A thin wrapper around `QSettings`, kept separate from the image
database — it only stores per-machine UI preferences. `ThemeManager`
is constructed with an `AppSettings` instance (wired in
`AppContainer`) and uses it to persist `theme/name` and `theme/mode`.

### QML singleton (`Found.Theme 1.0`)

`register_theme_singleton()` registers the live `ThemeManager`
instance as the `Found.Theme` QML module, so any `.qml` file can do:

```qml
import Found.Theme 1.0

Text {
    color: Theme.text
    font.pixelSize: Theme.fontSizeMd
}
```

Registration is process-wide and one-time — the first instance
registered "wins" for the lifetime of the process (relevant for
tests, see §4).

---

## 2. Shared primitives (`found_app/qml/primitives/`)

Rather than every view reading `Theme.*` directly, common UI patterns
are built once as theme-aware primitives:

- **`AppText.qml`** — `Text` wrapper. `variant` is `"default"`,
  `"heading"`, `"label"`, or `"muted"`, mapping to the appropriate
  `Theme.fontSize*` / `Theme.text` / `Theme.textMuted`.
- **`AppButton.qml`** — themed button with default/hover/pressed/
  disabled states driven by `Theme.surface`/`Theme.accent`/
  `Theme.border`.
- **`AppTextField.qml`** — themed text input with focus and
  error/warning states.
- **`Chip.qml`** — base for filter/category chips, with
  `off`/`include`/`exclude`/`mixed`/`drag-hover` states.
- **`Surface.qml`** — `Rectangle` wrapper using `Theme.surface` /
  `Theme.border` for panels and cards, with a `padding` token and a
  `default property alias content` for child layout.

New views should be built from these primitives wherever the pattern
fits, falling back to direct `Theme.*` token reads only for
one-off layout.

### Token lint test

`found_app/tests/test_qml_token_lint.py` scans every `found_app/qml/**/*.qml`
file for hardcoded hex colors and `pixelSize:` integer literals. Any
file not in `ALLOWED_FILES` (currently empty) fails the build if it
contains one. **New QML files must not add hardcoded colors or pixel
sizes** — use `Theme.*` tokens or a primitive instead.

---

## 3. Settings view

`found_app/qml/views/SettingsView.qml` is the user-facing surface for
theme selection, routed via `NavigationManager.push("settings", {})`
and a gear icon in `TitleBar`. It renders:

- a **theme picker** — one button per `Theme.availableThemes()` entry,
  calling `Theme.setThemeName(name)`.
- a **mode picker** — `light`/`dark`/`system` buttons calling
  `Theme.setMode(mode)`.

Because every token read in the app goes through the `Theme` singleton
and `paletteChanged`, selecting either updates the entire UI live —
no view-specific wiring is needed.

---

## 4. Testing notes

- `theme_qml_engine` fixture registers a `ThemeManager()` via
  `register_theme_singleton`. Because registration is one-time
  process-wide, tests that need a *fresh* theme state should fetch the
  already-registered instance (`register_theme_singleton(ThemeManager())`
  returns the **existing** singleton, not a new one) and mutate it
  directly (`setThemeName`, `setMode`) rather than assuming a new
  instance.
- Repeater-instantiated delegates (e.g. the theme/mode picker buttons)
  aren't reachable via `findChild`. Give the `Repeater` an `id` and
  drive it via `QQmlExpression(ctx, None, "themeRepeater.itemAt(i).clicked()")`.

---

## 5. Adding a new theme preset

Adding a theme is intentionally a small, self-contained change (plan
Section 8, Feature 8.1 template — `theme/08-<theme-name>-preset`):

1. In `found_app/theme/palettes.py`, define `<NAME>_LIGHT` and
   `<NAME>_DARK` dicts with **every key** that exists in
   `FOUND_DARK`/`FOUND_LIGHT` (colors, typography, spacing/layout —
   see §1). Reuse the existing typography/spacing values unless the
   new theme has a deliberate reason to differ.
2. Add an entry to `THEMES`:
   ```python
   THEMES = {
       "Found": {"light": FOUND_LIGHT, "dark": FOUND_DARK},
       "Sepia": {"light": SEPIA_LIGHT, "dark": SEPIA_DARK},
       "<Name>": {"light": <NAME>_LIGHT, "dark": <NAME>_DARK},
   }
   ```
3. Write a test (see `test_themes_registry_includes_sepia_with_required_keys`
   in `found_app/tests/test_palettes.py`) asserting the new entry has
   `light`/`dark` variants with the full required key set and that the
   two variants actually differ.
4. Nothing else needs to change — `availableThemes()`, the Settings
   picker, and every themed view pick up the new entry automatically.
5. Manually verify via the Settings view: the new theme appears in the
   picker and applying it updates the whole UI live in both light and
   dark mode.
6. Run the full suite.

Record the new preset under "Completed presets" in
`docs/plans/theme-system.md` Section 8 (the Feature 8.1 checklist
itself is a reusable template, not a one-time checklist).
