import QtQuick

Item {
    id: root

    property bool open: false
    property var collections: []

    signal collectionClicked(string collectionId, string collectionName)
    signal createCollectionRequested(string name)
    signal imageDropped(string collectionId, string imageId)
    signal toggleRequested()

    implicitWidth: 260

    // Edge tab — follows the panel's right edge, always visible
    Rectangle {
        id: edgeTab
        width: 16
        height: 72
        x: panel.x + panel.width
        y: (parent.height - height) / 2
        color: "#1a1a1a"
        radius: 2
        z: 1

        Text {
            anchors.centerIn: parent
            text: root.open ? "◀" : "▶"
            font.pixelSize: 10
            color: "#888888"
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.toggleRequested()
        }
    }

    // Slide-in panel
    Rectangle {
        id: panel
        width: root.implicitWidth
        height: parent.height
        x: root.open ? 0 : -width
        color: "#1a1a1a"

        Behavior on x { NumberAnimation { duration: 200; easing.type: Easing.InOutQuad } }

        // Header
        Item {
            id: header
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: 48

            Text {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                text: "Collections"
                font.pixelSize: 14
                font.weight: Font.Medium
                color: "#ffffff"
            }
        }

        // Divider
        Rectangle {
            id: divider
            anchors { top: header.bottom; left: parent.left; right: parent.right }
            height: 1
            color: "#2a2a2a"
        }

        // New collection input area
        Item {
            id: newCollectionArea
            anchors { top: divider.bottom; left: parent.left; right: parent.right }
            height: 44

            Rectangle {
                id: inputBg
                anchors { left: parent.left; leftMargin: 12; right: addBtn.left; rightMargin: 6; verticalCenter: parent.verticalCenter }
                height: 28
                color: "#252525"
                radius: 4

                TextInput {
                    id: newCollectionInput
                    anchors { left: parent.left; leftMargin: 8; right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                    color: "#cccccc"
                    font.pixelSize: 12
                    clip: true
                    Keys.onReturnPressed: {
                        if (text.trim().length > 0) {
                            root.createCollectionRequested(text.trim())
                            text = ""
                        }
                    }

                    Text {
                        anchors.fill: parent
                        text: "New collection…"
                        color: "#555555"
                        font.pixelSize: 12
                        visible: parent.text.length === 0
                    }
                }
            }

            Rectangle {
                id: addBtn
                anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                width: 28
                height: 28
                color: addBtnHover.containsMouse ? "#3a4a3a" : "#2a3a2a"
                radius: 4

                Text {
                    anchors.centerIn: parent
                    text: "+"
                    font.pixelSize: 16
                    color: "#88cc88"
                }

                MouseArea {
                    id: addBtnHover
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        var name = newCollectionInput.text.trim()
                        if (name.length > 0) {
                            root.createCollectionRequested(name)
                            newCollectionInput.text = ""
                        }
                    }
                }
            }
        }

        // Collection list
        ListView {
            id: collectionList
            anchors {
                top: newCollectionArea.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
                leftMargin: 8
                rightMargin: 8
                bottomMargin: 8
            }
            clip: true
            model: root.collections

            delegate: CollectionItem {
                width: collectionList.width
                collectionId: modelData.id ?? ""
                collectionName: modelData.name ?? ""
                onClicked: (cid, cname) => root.collectionClicked(cid, cname)
                onImageDropped: (cid, iid) => root.imageDropped(cid, iid)
            }

            // Empty state
            Text {
                anchors.centerIn: parent
                visible: collectionList.count === 0
                text: "No collections yet"
                color: "#555555"
                font.pixelSize: 12
            }
        }
    }
}
