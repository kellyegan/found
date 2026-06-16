import QtQuick
import Found.Theme 1.0
import "../primitives"

Item {
    id: root

    property string selectionMode: "none"
    property var collections: []           // assigned collections shown as chips
    property string multiSelectLabel: ""

    signal addToCollectionRequested(string collectionId, string collectionName)
    signal removeFromCollectionRequested(string collectionId)

    implicitHeight: secCol.implicitHeight

    property bool _dropdownOpen: false

    Column {
        id: secCol
        width: parent.width
        spacing: 0

        Rectangle { objectName: "divider"; width: parent.width; height: 1; color: Theme.border }

        Item {
            width: parent.width
            height: 32

            Text {
                objectName: "collectionsHeaderText"
                anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                text: "COLLECTIONS"
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
                font.capitalization: Font.AllUppercase
                font.letterSpacing: 0.8
                color: Theme.textMuted
            }
        }

        // "Add to collection" button row — opens dropdown of unassigned collections
        Item {
            width: secCol.width
            height: 32

            Rectangle {
                id: addToCollectionRow
                objectName: "addToCollectionRow"
                property alias borderColor: addToCollectionRow.border.color
                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter }
                height: 26; radius: 13
                color: addArea.containsMouse ? Theme.surface : "transparent"
                border.color: root._dropdownOpen ? Theme.textMuted : Theme.border
                border.width: 1

                Text {
                    objectName: "addIcon"
                    anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                    text: "+"; font.pixelSize: Theme.fontSizeSm; color: Theme.textMuted
                }

                Text {
                    objectName: "addLabelText"
                    anchors { left: parent.left; leftMargin: 24; right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                    text: "Add to collection…"
                    color: Theme.textMuted; font.pixelSize: Theme.fontSizeSm; font.family: Theme.fontFamily
                    elide: Text.ElideRight
                }

                MouseArea {
                    id: addArea
                    anchors.fill: parent
                    hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: root._dropdownOpen = !root._dropdownOpen
                }
            }
        }

        // Unassigned collections dropdown
        DropdownList {
            id: dropdownBox
            objectName: "dropdownBox"
            visible: root._dropdownOpen
            width: secCol.width
            model: {
                var all = CollectionsState.collections
                var assigned = root.collections
                var assignedIds = {}
                for (var i = 0; i < assigned.length; i++) assignedIds[assigned[i].id] = true
                return all.filter(function(c) { return !assignedIds[c.id] })
            }
            onItemSelected: function(id, name) {
                root.addToCollectionRequested(id, name)
                root._dropdownOpen = false
            }
        }

        // Multi-select note
        Text {
            objectName: "multiSelectText"
            visible: root.selectionMode === "multi"
            width: parent.width
            topPadding: 4; bottomPadding: 4
            text: root.multiSelectLabel
            color: Theme.textMuted; font.pixelSize: Theme.fontSizeSm; font.family: Theme.fontFamily; wrapMode: Text.WordWrap
        }

        // Assigned collection chips — single selection mode only
        Flow {
            visible: root.selectionMode === "single"
            width: parent.width; spacing: 4; topPadding: 4; bottomPadding: 4

            Repeater {
                id: chipRepeater
                model: root.selectionMode === "single" ? root.collections : []
                delegate: Chip {
                    id: collectionChip
                    objectName: "collectionChip"
                    required property var modelData
                    chipState: "assigned"
                    text: modelData.name ?? ""
                    removable: true
                    onRemoveRequested: root.removeFromCollectionRequested(modelData.id)
                }
            }
        }

        Item { width: parent.width; height: 8 }
    }
}
