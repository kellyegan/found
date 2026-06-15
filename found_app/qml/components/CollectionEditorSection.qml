import QtQuick
import Found.Theme 1.0

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
        Rectangle {
            id: dropdownBox
            objectName: "dropdownBox"
            property alias borderColor: dropdownBox.border.color
            visible: root._dropdownOpen
            width: secCol.width
            height: visible ? Math.min(dropList.contentHeight + 8, 160) : 0
            radius: 4; color: Theme.surface; border.color: Theme.border; border.width: 1; clip: true

            ListView {
                id: dropList
                anchors { fill: parent; topMargin: 4; bottomMargin: 4 }
                model: {
                    var all = CollectionsState.collections
                    var assigned = root.collections
                    var assignedIds = {}
                    for (var i = 0; i < assigned.length; i++) assignedIds[assigned[i].id] = true
                    return all.filter(function(c) { return !assignedIds[c.id] })
                }
                clip: true

                delegate: Item {
                    required property var modelData
                    width: dropList.width; height: 26

                    Rectangle {
                        objectName: "dropdownItemBg"
                        anchors.fill: parent
                        color: dropArea.containsMouse ? Theme.border : "transparent"
                        radius: 3
                    }

                    Text {
                        objectName: "dropdownItemText"
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: modelData.name ?? ""
                        color: Theme.text; font.pixelSize: Theme.fontSizeSm; font.family: Theme.fontFamily
                    }

                    MouseArea {
                        id: dropArea
                        anchors.fill: parent
                        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.addToCollectionRequested(modelData.id, modelData.name)
                            root._dropdownOpen = false
                        }
                    }
                }
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
                delegate: Rectangle {
                    id: collectionChip
                    objectName: "collectionChip"
                    property alias borderColor: collectionChip.border.color
                    required property var modelData
                    width: chipLabel.implicitWidth + 28; height: 22; radius: 11
                    color: Theme.surface; border.color: Theme.border; border.width: 1

                    Text {
                        id: chipLabel
                        objectName: "collectionChipLabel"
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: modelData.name ?? ""; font.pixelSize: Theme.fontSizeSm; font.family: Theme.fontFamily; color: Theme.text
                    }

                    Text {
                        objectName: "collectionChipRemoveText"
                        anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                        text: "×"; font.pixelSize: Theme.fontSizeSm
                        color: chipRemoveArea.containsMouse ? Theme.text : Theme.textMuted

                        MouseArea {
                            id: chipRemoveArea
                            anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: root.removeFromCollectionRequested(modelData.id)
                        }
                    }
                }
            }
        }

        Item { width: parent.width; height: 8 }
    }
}
