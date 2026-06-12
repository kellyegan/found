# Theme System Implementation Plan

A checklist-driven roadmap for rebuilding `found_app/theme` into a reactive,
multi-theme, OS-aware system with a shared component library.

## How to use this checklist

- Each **Section** below corresponds to one of the 8 agreed phases.
- Each **Feature** is a dedicated branch off `main`.
- Each checkbox within a feature is one commit, following the project's
  RED → GREEN → REFACTOR cycle (CLAUDE.md): write a failing test, implement
  the minimum to pass, then commit.
- Before merging a feature branch, run the full test suite
  (`python -m pytest found_app/tests/ -v` and `backend/` if touched).
- Sections 1-4 are strictly sequential. Within Section 5, the primitive
  features (5.1-5.5) must land before the rollout features (5.6-5.10); the
  rollout features can then proceed in any order. Sections 6-8 depend on
  Section 5 being complete.

---

## Section 1 — Reactive Theme Tokens

Goal: convert `ThemeManager` properties from `constant=True` to
notify-based, with no change in values or behavior. Lays the groundwork for
live palette swapping.

### Feature 1.1 — `theme/01-reactive-properties`

- [ ] Add a `paletteChanged` signal to `ThemeManager`.
  Test: a connected slot is invoked when `paletteChanged` is emitted.
  Implement: `paletteChanged = Signal()`.
- [ ] Move color tokens (`background`, `surface`, `text`, `textMuted`,
  `warningColor`, `accent`, `border`) onto an internal palette dict, with
  `notify=paletteChanged`.
  Test: each property still returns its current value; emitting
  `paletteChanged` after mutating internal state changes the returned value.
  Implement: replace per-property literals with `self._palette["..."]` reads.
- [ ] Move typography tokens (`fontFamily`, `fontSizeSm/Md/Lg/Xl`) onto the
  internal palette dict with `notify=paletteChanged`.
- [ ] Move spacing/layout tokens (`spacingXs/Sm/Md/Lg/Xl`, `overlayWidth`,
  `horizontalMargin`, `horizontalTextMargin`) onto the internal palette dict
  with `notify=paletteChanged`, and fix `horizontalTextPadding` (currently
  missing its `@Property` decorator entirely).
- [ ] Run full suite; confirm `test_theme.py` and all QML integration tests
  still pass unchanged.

---

## Section 2 — Palette Schema & Built-in Presets

Goal: formalize the token set as a data structure, define a light variant,
and group light/dark pairs into named themes.

### Feature 2.1 — `theme/02-palette-presets`

- [ ] Define a `FOUND_DARK` palette (dict or dataclass) in
  `found_app/theme/palettes.py` containing every token currently on
  `ThemeManager`, with today's values.
  Test: `FOUND_DARK` has all expected keys and matches `ThemeManager`'s
  current defaults.
- [ ] Source `ThemeManager`'s internal palette from `FOUND_DARK` by default.
  Test: `test_theme.py` values still pass, now sourced indirectly via
  `FOUND_DARK`.
- [ ] Define a `FOUND_LIGHT` palette — light-mode counterpart with the same
  keys (typography/spacing unchanged, colors inverted/adjusted).
  Test: `FOUND_LIGHT` has the same key set as `FOUND_DARK` and differs in
  color values.
- [ ] Add a `THEMES` registry grouping named theme families, each with
  `light`/`dark` palette references, e.g. `THEMES["Found"] = {"light":
  FOUND_LIGHT, "dark": FOUND_DARK}`.
  Test: `THEMES["Found"]["dark"] is FOUND_DARK`, etc.
- [ ] Add `ThemeManager.setPalette(palette)` to swap the active palette and
  emit `paletteChanged`.
  Test: after `setPalette(FOUND_LIGHT)`, `theme.background ==
  FOUND_LIGHT["background"]` and `paletteChanged` was emitted.
- [ ] Run full suite.

---

## Section 3 — AppSettings & Persistence

Goal: a generic local-settings wrapper, separate from the image database,
used to persist the active theme name and mode.

### Feature 3.1 — `theme/03-settings-persistence`

- [x] Add `AppSettings`, a thin wrapper around `QSettings`, in
  `found_app/core/app_settings.py`.
  Test: `set(key, value)` then `get(key)` round-trips, including across a
  new `AppSettings` instance pointed at the same backing store (use
  `QSettings.IniFormat` with a temp file in tests).
- [x] `ThemeManager` accepts an `AppSettings` instance and persists the
  selected theme name via `setThemeName(name)` / `themeName`.
  Test: setting the theme name and constructing a new `ThemeManager` with
  the same `AppSettings` restores it.
- [x] `ThemeManager` persists the active mode (`light` / `dark` / `system`)
  via `setMode(mode)` / `mode`, same round-trip test pattern.
- [x] Add `darkdetect` to `found_app/requirements.txt`; on startup, when
  `mode == "system"`, resolve to the light or dark palette via
  `darkdetect.theme()`.
  Test: with `darkdetect.theme()` mocked to return `"Light"`/`"Dark"`,
  `ThemeManager` resolves to `FOUND_LIGHT`/`FOUND_DARK` respectively.
- [x] Wire `AppSettings` construction into `AppContainer` and pass it to
  `ThemeManager`.
  Test: `AppContainer`-level integration test confirms the wired
  `ThemeManager` is settings-backed.
- [x] Run full suite.

---

## Section 4 — QML Singleton Registration & Migration

Goal: expose `ThemeManager` as an importable QML singleton and migrate all
QML files off the `Theme` context property.

### Feature 4.1 — `theme/04-qml-singleton`

- [x] Register the `ThemeManager` instance as a QML singleton (e.g.
  `qmlRegisterSingletonInstance("Found.Theme", 1, 0, "Theme", theme)`),
  alongside the existing context property.
  Test: a QML test imports `Found.Theme` and reads `Theme.background`,
  matching `ThemeManager.background`.
- [x] Migrate `shell/` QML (`AppWindow.qml`, `MainRouter.qml`,
  `TitleBar.qml`) to `import Found.Theme`, removing reliance on the context
  property.
  Test: existing shell QML tests stay green after the import change.
- [x] Migrate filtering/chip components (`CategoriesBar.qml`,
  `CategoryChip.qml`, `ChipSearchSection.qml`, `FilterChip.qml`,
  `FilterDropdown.qml`, `TagSearchField.qml`, `MetaRow.qml`) to
  `import Found.Theme`.
- [x] Migrate panels/dialogs (`SidePanel.qml`, `CollectionsSidePanel.qml`,
  `MetadataSidePanel.qml`, `ConfirmDialog.qml`, `HoverTooltip.qml`,
  `EdgeTab.qml`, `ImportPanel.qml`, `CollectionEditorSection.qml`,
  `CollectionItem.qml`) to `import Found.Theme`.
- [x] Migrate grid/thumbnail components (`ImageGridPane.qml`,
  `ThumbnailGrid.qml`, `ThumbnailTile.qml`) and `views/` (`ImageView.qml`,
  `SplashScreen.qml`, `LibraryView.qml`, `CollectionView.qml`) to
  `import Found.Theme`.
- [x] Remove the legacy `ctx.setContextProperty("Theme", ...)` registration
  from `app_container.py` now that nothing references it.
  Test: full QML test suite stays green with the context property removed.
- [x] Fix the dangling `Theme.surface2` reference in `CategoryChip.qml`
  (no such property exists on `ThemeManager`) — replace with the correct
  existing token.
- [x] Run full suite.

---

## Section 5 — Shared Primitives & Token Consolidation

Goal: build a small set of theme-aware base components, then sweep every
file with hardcoded colors/sizes (21 files: 177 hex literals, 66 `pixelSize`
literals) to use tokens and primitives.

### Feature 5.0 — `theme/05-token-lint-test`

- [ ] Add a test that scans `found_app/qml/**/*.qml` for hardcoded hex color
  literals and `pixelSize:` integer literals, failing if any are found
  outside an explicit allowlist. Seed the allowlist with the 21 known files
  (`CategoriesBar.qml`, `CategoryChip.qml`, `ChipSearchSection.qml`,
  `CollectionEditorSection.qml`, `CollectionItem.qml`,
  `CollectionsSidePanel.qml`, `ConfirmDialog.qml`, `EdgeTab.qml`,
  `FilterChip.qml`, `FilterDropdown.qml`, `HoverTooltip.qml`,
  `ImportPanel.qml`, `MetadataSidePanel.qml`, `MetaRow.qml`,
  `SidePanel.qml`, `TagSearchField.qml`, `ThumbnailTile.qml`,
  `MainRouter.qml`, `TitleBar.qml`, `ImageView.qml`, `SplashScreen.qml`) so
  the test passes initially. Each rollout commit below removes one file from
  the allowlist.
- [ ] Run full suite.

### Feature 5.1 — `theme/05-app-text-primitive`

- [ ] Add `AppText.qml`: a `Text` wrapper defaulting to
  `Theme.fontFamily`/`Theme.fontSizeMd`/`Theme.text`.
  Test: default instance exposes those values.
- [ ] Add `muted`, `heading`, and `label` variants mapping to
  `Theme.textMuted`/`fontSizeSm`/`fontSizeLg` as appropriate.
  Test: each variant resolves to the expected token.
- [ ] Run full suite.

### Feature 5.2 — `theme/05-app-button-primitive`

- [ ] Add `AppButton.qml` (container + `AppText`) with default and hover
  states styled from `Theme.surface`/`Theme.accent`/`Theme.border`.
  Test: hover state changes background to the expected token value.
- [ ] Add pressed and disabled states.
  Test: each state maps to its expected token.
- [ ] Run full suite.

### Feature 5.3 — `theme/05-app-textfield-primitive`

- [ ] Add `AppTextField.qml` styled from `Theme.surface`/`Theme.border`/
  `Theme.text`.
  Test: default styling matches expected tokens.
- [ ] Add focus state (border → `Theme.accent`) and error/warning state
  (border/text → `Theme.warningColor`).
  Test: each state maps to its expected token.
- [ ] Run full suite.

### Feature 5.4 — `theme/05-chip-primitive`

- [ ] Add a base `Chip.qml` supporting `off`/`include`/`exclude`/`mixed`/
  `drag-hover` states via theme tokens.
  Test: each state resolves to its expected color token.
- [ ] Refactor `CategoryChip.qml` to build on `Chip`.
  Test: existing `CategoryChip` behavioral tests stay green.
- [ ] Refactor `FilterChip.qml` to build on `Chip`.
  Test: existing `FilterChip` behavioral tests stay green.
- [ ] Run full suite.

### Feature 5.5 — `theme/05-surface-primitive`

- [ ] Add `Surface.qml`: a `Rectangle` wrapper using `Theme.surface`,
  `Theme.border`, and a spacing token for padding/radius — the base for
  panels and cards.
  Test: default instance exposes expected color/spacing tokens.
- [ ] Run full suite.

### Feature 5.6 — `theme/05-rollout-shell`

- [ ] Convert `MainRouter.qml`: replace hardcoded literals with
  `Theme.*`/primitives; remove from lint allowlist.
- [ ] Convert `TitleBar.qml`: replace hardcoded literals (including
  `#ff8800`/`#ff4444`/`#cc6666` — decide whether these map to
  `Theme.warningColor` or warrant a new semantic `errorColor` token added
  back in Section 2's palette). While deciding, also rename `warningColor`
  to `warning` to match the naming pattern of the other color tokens
  (`background`, `surface`, `text`, `accent`, `border`) — update
  `theme.py`, `palettes.py`, and the 3 existing QML usages; remove from
  lint allowlist.
- [ ] Run full suite.

### Feature 5.7 — `theme/05-rollout-filtering`

- [ ] Convert `CategoriesBar.qml`; remove from lint allowlist.
- [ ] Convert `CategoryChip.qml`; remove from lint allowlist.
- [ ] Convert `ChipSearchSection.qml`; remove from lint allowlist.
- [ ] Convert `FilterChip.qml`; remove from lint allowlist.
- [ ] Convert `FilterDropdown.qml`; remove from lint allowlist.
- [ ] Convert `TagSearchField.qml`; remove from lint allowlist.
- [ ] Convert `MetaRow.qml`; remove from lint allowlist.
- [ ] Run full suite.

### Feature 5.8 — `theme/05-rollout-panels`

- [ ] Convert `SidePanel.qml`; remove from lint allowlist.
- [ ] Convert `CollectionsSidePanel.qml`; remove from lint allowlist.
- [ ] Convert `MetadataSidePanel.qml`; remove from lint allowlist.
- [ ] Convert `ConfirmDialog.qml`; remove from lint allowlist.
- [ ] Convert `HoverTooltip.qml`; remove from lint allowlist.
- [ ] Convert `EdgeTab.qml`; remove from lint allowlist.
- [ ] Convert `ImportPanel.qml`; remove from lint allowlist.
- [ ] Convert `CollectionEditorSection.qml`; remove from lint allowlist.
- [ ] Convert `CollectionItem.qml`; remove from lint allowlist.
- [ ] Run full suite.

### Feature 5.9 — `theme/05-rollout-grids`

- [ ] Convert `ThumbnailTile.qml`; remove from lint allowlist.
- [ ] Run full suite.

### Feature 5.10 — `theme/05-rollout-views`

- [ ] Convert `ImageView.qml`; remove from lint allowlist.
- [ ] Convert `SplashScreen.qml`; remove from lint allowlist.
- [ ] Confirm the lint allowlist is now empty.
- [ ] Run full suite.

---

## Section 6 — Live OS Theme Switching

Goal: when mode is `system`, follow OS dark/light changes while the app is
running.

### Feature 6.1 — `theme/06-os-live-switching`

- [ ] Add a `QTimer`-based poll of `darkdetect.theme()` while
  `mode == "system"`.
  Test: with `darkdetect.theme()` mocked to change between polls,
  `ThemeManager` emits `paletteChanged` and resolves the new palette.
- [ ] Start/stop the poll timer in response to `setMode()` changes (only
  active in `system` mode).
  Test: timer is running iff mode is `system`.
- [ ] Manually verify (via the `run` skill): toggle OS appearance while the
  app is running in "system" mode and confirm the UI updates live.
- [ ] Run full suite.

---

## Section 7 — Settings View

Goal: a user-facing surface for theme/mode selection — also the first real
exercise of live switching end-to-end.

### Feature 7.1 — `theme/07-settings-view`

- [ ] Add `SettingsView.qml` with an "Appearance" section scaffold, built
  from `AppText`/`Surface` primitives.
  Test: instantiating `SettingsView` exposes an Appearance section.
- [ ] Add a theme picker bound to `THEMES`/`Theme.availableThemes()`,
  calling `Theme.setThemeName(...)` on selection.
  Test: selecting an entry calls `setThemeName` with the right name.
- [ ] Add a mode picker (`light`/`dark`/`system`) calling `Theme.setMode(...)`.
  Test: selecting an entry calls `setMode` with the right value.
- [ ] Add a navigation entry point to `SettingsView` (route in `MainRouter`
  + trigger in `TitleBar`).
  Test: `MainRouter` can route to the Settings view.
- [ ] Manually verify (via the `run` skill): open Settings, switch theme and
  mode, confirm the whole UI updates live.
- [ ] Run full suite.

---

## Section 8 — Additional Named Theme Presets

Goal: add further built-in theme families now that the infrastructure is
data-driven. Each new theme is its own small feature.

### Feature 8.1 — `theme/08-<theme-name>-preset` (repeat per theme)

- [ ] Define `<NAME>_LIGHT`/`<NAME>_DARK` palettes with the full token set
  and add to `THEMES`.
  Test: new entry in `THEMES` has both variants with all required keys.
- [ ] Manually verify the new theme appears in and applies correctly from
  the Settings picker.
- [ ] Run full suite.

---

## Deferred — Icon System

Not scheduled yet. When picked up: reserve `found_app/resources/icons/` and
a placeholder `Icon.qml` with an unused `color` prop, marking the seam for a
later tinting strategy (runtime `MultiEffect`/`ColorOverlay` vs. pre-rendered
per-theme sets) without committing now.
