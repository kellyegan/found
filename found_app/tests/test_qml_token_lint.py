"""
Lint test for hardcoded theme literals in QML.

Covers:
- found_app/qml/**/*.qml contain no hardcoded hex color literals or
  pixelSize integer literals outside an explicit allowlist.
"""

import re
from pathlib import Path

import found_app

QML_DIR = Path(found_app.__file__).parent / "qml"

HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
PIXEL_SIZE_RE = re.compile(r"pixelSize:\s*\d+")

# Files that still contain hardcoded hex colors and/or pixelSize literals.
# Each Section 5 rollout commit converts one file to theme tokens/primitives
# and removes it from this list.
ALLOWED_FILES = {
    "components/CategoriesBar.qml",
    "components/CategoryChip.qml",
    "components/ChipSearchSection.qml",
    "components/CollectionEditorSection.qml",
    "components/CollectionItem.qml",
    "components/CollectionsSidePanel.qml",
    "components/ConfirmDialog.qml",
    "components/EdgeTab.qml",
    "components/FilterChip.qml",
    "components/FilterDropdown.qml",
    "components/HoverTooltip.qml",
    "components/ImportPanel.qml",
    "components/MetadataSidePanel.qml",
    "components/MetaRow.qml",
    "components/SidePanel.qml",
    "components/TagSearchField.qml",
    "components/ThumbnailTile.qml",
    "views/ImageView.qml",
    "views/SplashScreen.qml",
}


def _violations():
    violations = {}
    for qml_file in sorted(QML_DIR.rglob("*.qml")):
        rel = qml_file.relative_to(QML_DIR).as_posix()
        if rel in ALLOWED_FILES:
            continue
        text = qml_file.read_text()
        hits = HEX_COLOR_RE.findall(text) + PIXEL_SIZE_RE.findall(text)
        if hits:
            violations[rel] = hits
    return violations


def test_no_hardcoded_tokens_outside_allowlist():
    violations = _violations()
    assert not violations, (
        "Hardcoded hex colors / pixelSize literals found outside the "
        f"allowlist: {violations}"
    )
