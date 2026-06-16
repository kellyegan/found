import QtQuick
import Found.Theme 1.0

Item {
    id: root

    property bool open: false
    property var activeCategories: []   // [{id, name, mode}]
    property var activeTags: []          // [{id, name, mode}]
    property bool showMissingOnly: false
    property bool importJobActive: false

    signal clearAllRequested()
    signal removeCategoryFilter(string categoryId)
    signal removeTagFilter(string tagId)
    signal toggleMissingOnlyRequested()

    visible: open

    readonly property bool _anyFilterActive: activeTags.length > 0
                                             || activeCategories.length > 0
                                             || showMissingOnly
                                             || importJobActive

    implicitHeight: mainColumn.implicitHeight + 20

    // Reusable group header layout: ──── Label ────
    component GroupHeader: Item {
        property string text: ""
        width: parent ? parent.width : 0
        height: 20

        Rectangle {
            anchors.left: parent.left
            anchors.right: lbl.left
            anchors.rightMargin: 6
            anchors.verticalCenter: lbl.verticalCenter
            height: 1
            color: Theme.border
        }
        Text {
            id: lbl
            anchors.centerIn: parent
            text: parent.text
            color: Theme.textMuted
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
        }
        Rectangle {
            anchors.left: lbl.right
            anchors.leftMargin: 6
            anchors.right: parent.right
            anchors.verticalCenter: lbl.verticalCenter
            height: 1
            color: Theme.border
        }
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.surface
        border.color: Theme.border
        border.width: 1
        radius: 4

        Column {
            id: mainColumn
            anchors { top: parent.top; topMargin: 10; left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12 }
            spacing: 0

            // ── Recent Import ────────────────────────────────────────────────
            Column {
                visible: root.importJobActive
                width: parent.width
                spacing: 6

                GroupHeader { text: "Recent Import" }

                FilterChip {
                    width: parent.width
                    label: "Recent import"
                    filterMode: "include"
                    onRemoveRequested: root.clearAllRequested()
                }

                Item { width: 1; height: Theme.spacingXs }
            }
            Rectangle { visible: root.importJobActive; width: parent.width; height: 1; color: Theme.border }
            Item    { visible: root.importJobActive; width: 1; height: 6 }

            // ── Keywords ─────────────────────────────────────────────────────
            Column {
                visible: root.activeTags.length > 0
                width: parent.width
                spacing: 6

                GroupHeader { text: "Keywords" }

                Repeater {
                    model: root.activeTags
                    delegate: FilterChip {
                        required property var modelData
                        width: parent ? parent.width : 0
                        label: modelData.name
                        filterMode: modelData.mode
                        onRemoveRequested: root.removeTagFilter(modelData.id)
                    }
                }

                Item { width: 1; height: Theme.spacingXs }
            }
            Rectangle { visible: root.activeTags.length > 0; width: parent.width; height: 1; color: Theme.border }
            Item    { visible: root.activeTags.length > 0; width: 1; height: 6 }

            // ── Categories ───────────────────────────────────────────────────
            Column {
                visible: root.activeCategories.length > 0
                width: parent.width
                spacing: 6

                GroupHeader { text: "Categories" }

                Repeater {
                    model: root.activeCategories
                    delegate: FilterChip {
                        required property var modelData
                        width: parent ? parent.width : 0
                        label: modelData.name
                        filterMode: modelData.mode
                        onRemoveRequested: root.removeCategoryFilter(modelData.id)
                    }
                }

                Item { width: 1; height: Theme.spacingXs }
            }
            Rectangle { visible: root.activeCategories.length > 0; width: parent.width; height: 1; color: Theme.border }
            Item    { visible: root.activeCategories.length > 0; width: 1; height: 6 }

            // ── Missing Images ───────────────────────────────────────────────
            Column {
                width: parent.width
                spacing: 6

                GroupHeader { text: "Missing Images" }

                Rectangle {
                    id: missingToggle
                    objectName: "missingToggle"
                    property alias borderColor: missingToggle.border.color
                    width: parent.width
                    height: 28
                    radius: 14
                    color: root.showMissingOnly ? Theme.errorBg : "transparent"
                    border.color: root.showMissingOnly ? Theme.error : Theme.border
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
            }

            // ── Clear All ────────────────────────────────────────────────────
            Item      { visible: root._anyFilterActive; width: 1; height: Theme.spacingSm }
            Rectangle { visible: root._anyFilterActive; width: parent.width; height: 1; color: Theme.border }
            Item      { visible: root._anyFilterActive; width: 1; height: Theme.spacingSm }

            Text {
                visible: root._anyFilterActive
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                text: "Clear all filters"
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
                color: clearAllArea.containsMouse ? Theme.text : Theme.textMuted

                MouseArea {
                    id: clearAllArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.clearAllRequested()
                }
            }

            Item { width: 1; height: Theme.spacingXs }
        }
    }
}
