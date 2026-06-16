# QML Simplification Plan

Audit-driven refactoring to reduce duplication and better utilise existing primitives.
Each item is designed to be completed independently.

---

## Item 1 — Extend `Chip` with removable variant ✅ Done

**What:** The assigned-item chip (label + × button) was coded identically in
`ChipSearchSection` and `CollectionEditorSection`. Rather than a new primitive,
the existing `Chip` was extended with optional `text`, `removable`, and a new
`"assigned"` chipState (`Theme.surface` fill / `Theme.border` border).

**API added:**
```qml
Chip {
    chipState: "assigned"
    text: "Nature"
    removable: true
    onRemoveRequested: { ... }
}
```

**Files changed:** `primitives/Chip.qml`, `ChipSearchSection.qml`,
`CollectionEditorSection.qml`

---

## Item 2 — Extract `DropdownList` component

**What:** The suggestion/item list (Surface rectangle → ListView → hover delegate
with text + click) is repeated in `ChipSearchSection`, `CollectionEditorSection`,
and `TagSearchField`. Extract to `found_app/qml/components/DropdownList.qml`.

**Proposed API:**
```qml
DropdownList {
    model: someList       // [{ id, name }]
    maxHeight: 160
    onItemSelected: function(id, name) { ... }
}
```

**Files changed:** `ChipSearchSection.qml`, `CollectionEditorSection.qml`,
`TagSearchField.qml`

**Dependencies:** None — fully standalone.

---

## Item 3 — Unify `ChipSearchSection` and `CollectionEditorSection`

**What:** Both components share the same skeleton — divider, uppercase section
header, pill-shaped "add" row, dropdown, multi-select note, chip Flow. The only
behavioural difference is how the "add" row works:

- `ChipSearchSection` types to search, delegates to a `searchState`, uses `AppTextField`
- `CollectionEditorSection` clicks to reveal a static filtered list

After Items 1 and 2 are extracted, both components shrink enough to be replaced
by a single `ChipSection` with two modes:

```qml
// Search mode (replaces ChipSearchSection)
ChipSection {
    mode: "search"
    sectionLabel: "Tags"
    searchState: TagEditorSearchState
    items: root.tags
    allowCreateNew: true
    onAddRequested: ...
    onRemoveRequested: ...
}

// Select mode (replaces CollectionEditorSection)
ChipSection {
    mode: "select"
    sectionLabel: "Collections"
    items: root.collections
    onAddRequested: ...
    onRemoveRequested: ...
}
```

**Files changed:** `ChipSearchSection.qml` (merged into new `ChipSection`),
`CollectionEditorSection.qml` (deleted), `MetadataSidePanel.qml` (callsites updated)

**Dependencies:** Items 1 and 2 should be done first to keep the merge manageable.

---

## Item 4 — Add icon-only variant to `AppButton`

**What:** ~15 places hand-roll a small interactive icon button:

```qml
Rectangle {
    color: hoverArea.containsMouse ? Theme.border : "transparent"
    MouseArea {
        id: hoverArea
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: { ... }
    }
}
```

Add a compact `"icon"` variant to `AppButton` that handles this pattern:

```qml
AppButton {
    variant: "icon"
    label: "+"
    size: "sm"
    onClicked: { ... }
}
```

**Files changed:** `primitives/AppButton.qml`, then callsites in `CategoriesBar.qml`,
`ChipSearchSection.qml`, `FilterDropdown.qml`, `CollectionEditorSection.qml`,
`ConfirmDialog.qml`

**Dependencies:** None — can be done independently. Doing Item 3 first reduces
the number of callsites to update.

---

## Item 5 — Centralise spacing and colour tokens

**What:** Replace hard-coded pixel values (`8`, `12`, `14`, `16`) and inline
`Qt.tint()` colour expressions with named Theme tokens.

**Additions to Theme:**
```python
# Spacing
spacingXxs = 2
spacingXs  = 4

# Colour helpers
errorBg   = Qt.tint(surface, Qt.rgba(1, 0, 0, 0.15))
successBg = Qt.tint(surface, Qt.rgba(0, 1, 0, 0.15))
```

**Files changed:** `theme.py` + QML files using magic numbers:
`CategoriesBar.qml`, `ChipSearchSection.qml`, `FilterDropdown.qml`,
`CollectionItem.qml`, `ConfirmDialog.qml`, `MetadataSidePanel.qml`

**Dependencies:** None — fully standalone and safe at any time.

---

## Suggested order

```
1 → 2 → 3   (sequential — each extraction shrinks the next task)
4           (any time)
5           (any time)
```
