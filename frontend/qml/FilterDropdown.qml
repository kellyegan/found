import QtQuick

Item {
    id: root

    property bool open: false
    property var activeCategories: []   // [{id, name, mode}]
    property var activeTags: []          // [{id, name, mode}] — populated in Commit 8
    property bool showMissingOnly: false
    property bool importJobActive: false

    signal clearAllRequested()
    signal removeCategoryFilter(string categoryId)
    signal removeTagFilter(string tagId)
    signal toggleMissingOnlyRequested()

    visible: open

    Rectangle {
        anchors.fill: parent
        color: Theme.surface
        border.color: Theme.border
        border.width: 1
        radius: 4

        Column {
            id: content
            anchors { top: parent.top; left: parent.left; right: parent.right; topMargin: 10; leftMargin: 12; rightMargin: 12 }
            spacing: 6

            // ── Category chips ───────────────────────────────────────────────
            Repeater {
                model: root.activeCategories
                FilterChip {
                    required property var modelData
                    label: modelData.name
                    filterMode: modelData.mode
                    onRemoveRequested: root.removeCategoryFilter(modelData.id)
                }
            }

            // ── Tag chips ────────────────────────────────────────────────────
            Repeater {
                model: root.activeTags
                FilterChip {
                    required property var modelData
                    label: modelData.name
                    filterMode: modelData.mode
                    onRemoveRequested: root.removeTagFilter(modelData.id)
                }
            }

            // ── Missing-only toggle row ──────────────────────────────────────
            Rectangle {
                visible: true
                width: parent.width
                height: 28
                radius: 14
                color: root.showMissingOnly ? "#2a1515" : "transparent"
                border.color: root.showMissingOnly ? "#884444" : Theme.border
                border.width: 1

                Text {
                    anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                    text: "Missing images only"
                    font.pixelSize: Theme.fontSizeSm
                    font.family: Theme.fontFamily
                    color: root.showMissingOnly ? Theme.text : Theme.textMuted
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.toggleMissingOnlyRequested()
                }
            }

            // ── Import job chip ──────────────────────────────────────────────
            FilterChip {
                visible: root.importJobActive
                label: "Recent import"
                filterMode: "include"
                onRemoveRequested: root.clearAllRequested()
            }
        }

        // ── Separator ────────────────────────────────────────────────────────
        Rectangle {
            id: separator
            anchors { top: content.bottom; topMargin: 8; left: parent.left; right: parent.right; leftMargin: 12; rightMargin: 12 }
            height: 1
            color: Theme.border
            visible: root.activeCategories.length > 0 || root.activeTags.length > 0
                     || root.showMissingOnly || root.importJobActive
        }

        // ── Clear All button ─────────────────────────────────────────────────
        Text {
            anchors { top: separator.bottom; topMargin: 8; horizontalCenter: parent.horizontalCenter }
            text: "Clear all filters"
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            color: clearAllArea.containsMouse ? Theme.text : Theme.textMuted
            visible: root.activeCategories.length > 0 || root.activeTags.length > 0
                     || root.showMissingOnly || root.importJobActive

            MouseArea {
                id: clearAllArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.clearAllRequested()
            }
        }
    }
}
