import QtQuick

SidePanel {
    id: root

    edge: "left"
    title: "Collections"
    panelIcon: "☰"

    property var collections: []

    signal collectionClicked(string collectionId, string collectionName)
    signal createCollectionRequested(string name)
    signal imageDropped(string collectionId, string imageId)

    // New collection input area
    Item {
        id: newCollectionArea
        anchors { top: parent.top; left: parent.left; right: parent.right }
        height: 48

        Rectangle {
            anchors {
                left: parent.left; leftMargin: Theme.horizontalMargin
                right: addBtn.left; rightMargin: 6
                verticalCenter: parent.verticalCenter
            }
            height: 36
            color: "#252525"
            radius: 4

            TextInput {
                id: newCollectionInput
                anchors {
                    left: parent.left; leftMargin: 12
                    right: parent.right; rightMargin: 12
                    verticalCenter: parent.verticalCenter
                }
                color: "#cccccc"
                font.pixelSize: Theme.fontSizeMd
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
                    color: Theme.textMuted
                    font.pixelSize: Theme.fontSizeMd
                    visible: parent.text.length === 0
                }
            }
        }

        Rectangle {
            id: addBtn
            anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
            width: 36
            height: 36
            color: addBtnHover.containsMouse ? "#3a4a3a" : "#2a3a2a"
            radius: 4

            Text {
                anchors.centerIn: parent
                text: "+"
                font.pixelSize: Theme.fontSizeMd
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
            leftMargin: Theme.horizontalMargin
            rightMargin: Theme.horizontalMargin
            bottomMargin: Theme.horizontalMargin
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

        Text {
            anchors.centerIn: parent
            visible: collectionList.count === 0
            text: "No collections yet"
            color: "#555555"
            font.pixelSize: 12
        }
    }
}
