import QtQuick
import Found.Theme 1.0
import "../components"
import "../primitives"

Item {
    id: root

    property bool canGoBack: false
    property string viewTitle: ""
    property bool filterActive: false
    property bool searchReadOnly: false
    property var activeFilters: []

    property string importState: "Idle"
    property real importProgress: 0.0
    property int missingCount: 0
    property bool backendConnected: true

    property bool _filterOpen: false

    signal goBackRequested()
    signal settingsRequested()

    FilterDropdown {
        objectName: "filterDropdown"
        anchors { top: parent.bottom; right: parent.right; rightMargin: Theme.spacingMd }
        width: 280
        open: root._filterOpen
        showMissingOnly: FilterState.showMissingOnly
        importJobActive: FilterState.importJobId !== ""
        activeCategories: {
            var result = []
            var filters = FilterState.categoryFilters
            var cats = CategoriesState.categories
            for (var i = 0; i < cats.length; i++) {
                var mode = filters[cats[i].id]
                if (mode && mode !== "off")
                    result.push({ id: cats[i].id, name: cats[i].name, mode: mode })
            }
            return result
        }
        activeTags: {
            var result = []
            var tagFilters = FilterState.tagFilters
            var tagNames = TagSearchState.tagNames
            for (var tid in tagFilters) {
                var mode = tagFilters[tid]
                if (mode && mode !== "off")
                    result.push({ id: tid, name: tagNames[tid] ?? tid, mode: mode })
            }
            return result
        }
        onClearAllRequested: {
            FilterState.clearAllFilters()
            root._filterOpen = false
        }
        onRemoveCategoryFilter: function(catId) { FilterState.setCategoryFilter(catId, "off") }
        onRemoveTagFilter: function(tagId) { FilterState.setTagFilter(tagId, "off") }
        onToggleMissingOnlyRequested: FilterState.setShowMissingOnly(!FilterState.showMissingOnly)
    }

    // ── Title zone (left) ────────────────────────────────────────────────────
    Item {
        id: titleZone
        anchors { top: parent.top; left: parent.left; bottom: parent.bottom }
        width: parent.width * 0.5

        Item {
            id: backBtn
            width: visible ? 44 : 0
            height: parent.height
            visible: root.canGoBack

            Text {
                anchors.centerIn: parent
                text: "◀"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSm
                color: Theme.text
            }

            MouseArea {
                anchors.fill: parent
                onClicked: root.goBackRequested()
            }
        }

        Text {
            anchors {
                left: backBtn.right
                leftMargin: Theme.horizontalTextMargin
                verticalCenter: parent.verticalCenter
            }
            text: root.viewTitle
            font.pixelSize: Theme.fontSizeMd
            font.family: Theme.fontFamily
            font.weight: Font.DemiBold
            font.capitalization: Font.AllUppercase
            color: Theme.textMuted
        }
    }

    // ── Status zone (center) ─────────────────────────────────────────────────
    Item {
        id: statusZone
        anchors {
            top: parent.top
            bottom: parent.bottom
            left: titleZone.right
        }
        width: parent.width * 0.2

        Row {
            anchors.centerIn: parent
            spacing: 10

            // Import indicator — shown while scanning or importing
            Row {
                visible: root.importState === "Scanning" || root.importState === "Importing"
                spacing: 6

                // Animated pulse dot
                Rectangle {
                    id: importDot
                    width: 8; height: 8
                    radius: 4
                    color: Theme.accent
                    anchors.verticalCenter: parent.verticalCenter

                    SequentialAnimation on opacity {
                        running: importDot.visible
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.3; duration: 600; easing.type: Easing.InOutSine }
                        NumberAnimation { to: 1.0; duration: 600; easing.type: Easing.InOutSine }
                    }
                }

                Column {
                    spacing: 2
                    anchors.verticalCenter: parent.verticalCenter

                    Text {
                        text: root.importState === "Scanning" ? "Scanning…" : "Importing…"
                        font.pixelSize: Theme.fontSizeSm
                        font.family: Theme.fontFamily
                        color: Theme.textMuted
                    }

                    // Progress bar — only during active import
                    Rectangle {
                        visible: root.importState === "Importing"
                        width: 72; height: 3
                        color: Theme.surface
                        radius: 1.5

                        Rectangle {
                            width: parent.width * root.importProgress
                            height: parent.height
                            color: Theme.accent
                            radius: 1.5

                            Behavior on width { NumberAnimation { duration: 200 } }
                        }
                    }
                }
            }

            // Missing images indicator
            Row {
                visible: root.missingCount > 0
                spacing: 5

                Text {
                    objectName: "missingIcon"
                    text: "!"
                    font.pixelSize: Theme.fontSizeSm
                    font.weight: Font.Bold
                    color: Theme.error
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    objectName: "missingText"
                    text: root.missingCount + " missing"
                    font.pixelSize: Theme.fontSizeSm
                    font.family: Theme.fontFamily
                    color: Theme.error
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // Backend connection indicator — hidden when connected
            Row {
                visible: !root.backendConnected
                spacing: 5

                Rectangle {
                    objectName: "disconnectedDot"
                    width: 8; height: 8
                    radius: 4
                    color: Theme.warning
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    objectName: "disconnectedText"
                    text: "Disconnected"
                    font.pixelSize: Theme.fontSizeSm
                    font.family: Theme.fontFamily
                    color: Theme.warning
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }

    // ── Search zone (right) ──────────────────────────────────────────────────
    Item {
        id: searchZone
        anchors {
            top: parent.top
            bottom: parent.bottom
            left: statusZone.right
            right: parent.right
        }

        // Interactive mode: tag search field + filter icon (library/collection)
        TagSearchField {
            id: tagSearchField
            visible: !root.searchReadOnly
            anchors {
                left: parent.left; leftMargin: 8
                right: filterIconBtn.left; rightMargin: 4
                verticalCenter: parent.verticalCenter
            }
            height: 28
        }

        Item {
            id: filterIconBtn
            visible: !root.searchReadOnly
            width: 36
            height: parent.height
            anchors { right: settingsIconBtn.left; verticalCenter: parent.verticalCenter }

            Text {
                objectName: "filterIcon"
                anchors.centerIn: parent
                text: "⊟"
                font.pixelSize: Theme.fontSizeMd
                color: root.filterActive ? Theme.accent : Theme.textMuted
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root._filterOpen = !root._filterOpen
            }
        }

        // Read-only mode: non-interactive filter chips (image view)
        Flow {
            visible: root.searchReadOnly
            anchors {
                left: parent.left; leftMargin: 8
                right: settingsIconBtn.left; rightMargin: 4
                verticalCenter: parent.verticalCenter
            }
            spacing: 4

            Repeater {
                id: filterRepeater
                model: root.activeFilters

                delegate: Item {
                    required property var modelData
                    implicitWidth: roChipRow.implicitWidth + 20
                    height: 22

                    Chip {
                        objectName: "roChip"
                        anchors.fill: parent
                        chipState: modelData.mode === "exclude" ? "exclude" : "include"
                    }

                    Row {
                        id: roChipRow
                        anchors {
                            left: parent.left; leftMargin: 8
                            right: parent.right; rightMargin: 8
                            verticalCenter: parent.verticalCenter
                        }
                        spacing: 4

                        Text {
                            text: modelData.mode === "exclude" ? "−" : "+"
                            font.pixelSize: Theme.fontSizeSm
                            color: Theme.text
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: modelData.name ?? ""
                            font.pixelSize: Theme.fontSizeSm
                            font.family: Theme.fontFamily
                            color: Theme.text
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }
            }
        }

        // Settings entry point — always visible
        Item {
            id: settingsIconBtn
            width: 36
            height: parent.height
            anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }

            Text {
                objectName: "settingsIcon"
                anchors.centerIn: parent
                text: "⚙"
                font.pixelSize: Theme.fontSizeMd
                color: Theme.textMuted
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.settingsRequested()
            }
        }
    }
}
