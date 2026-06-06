import QtQuick

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

        Rectangle { width: parent.width; height: 1; color: "#2a2a2a" }

        Item {
            width: parent.width
            height: 32

            Text {
                anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                text: "COLLECTIONS"
                font.pixelSize: 10
                font.family: Theme.fontFamily
                font.capitalization: Font.AllUppercase
                font.letterSpacing: 0.8
                color: "#666666"
            }
        }

        // "Add to collection" button row — opens dropdown of unassigned collections
        Item {
            width: secCol.width
            height: 32

            Rectangle {
                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter }
                height: 26; radius: 13
                color: addArea.containsMouse ? "#242424" : "transparent"
                border.color: root._dropdownOpen ? "#555555" : "#333333"
                border.width: 1

                Text {
                    anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                    text: "+"; font.pixelSize: 14; color: "#555555"
                }

                Text {
                    anchors { left: parent.left; leftMargin: 24; right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                    text: "Add to collection…"
                    color: "#555555"; font.pixelSize: 11; font.family: Theme.fontFamily
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
            visible: root._dropdownOpen
            width: secCol.width
            height: visible ? Math.min(dropList.contentHeight + 8, 160) : 0
            radius: 4; color: "#242424"; border.color: "#3a3a3a"; border.width: 1; clip: true

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

                    Rectangle { anchors.fill: parent; color: dropArea.containsMouse ? "#2a2a2a" : "transparent"; radius: 3 }

                    Text {
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: modelData.name ?? ""
                        color: Theme.text; font.pixelSize: 11; font.family: Theme.fontFamily
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
            visible: root.selectionMode === "multi"
            width: parent.width
            topPadding: 4; bottomPadding: 4
            text: root.multiSelectLabel
            color: "#666666"; font.pixelSize: 11; font.family: Theme.fontFamily; wrapMode: Text.WordWrap
        }

        // Assigned collection chips — single selection mode only
        Flow {
            visible: root.selectionMode === "single"
            width: parent.width; spacing: 4; topPadding: 4; bottomPadding: 4

            Repeater {
                model: root.selectionMode === "single" ? root.collections : []
                delegate: Rectangle {
                    required property var modelData
                    width: chipLabel.implicitWidth + 28; height: 22; radius: 11
                    color: "#232323"; border.color: "#3a3a3a"; border.width: 1

                    Text {
                        id: chipLabel
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: modelData.name ?? ""; font.pixelSize: 11; font.family: Theme.fontFamily; color: "#aaaaaa"
                    }

                    Text {
                        anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                        text: "×"; font.pixelSize: 12
                        color: chipRemoveArea.containsMouse ? "#ffffff" : "#666666"

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
