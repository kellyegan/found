import QtQuick
import Found.Theme 1.0

SidePanel {
    id: root

    edge: "left"
    title: "Collections"
    panelIcon: "☰"
    dragOpenKeys: ["found/image"]

    property var collections: []

    signal collectionClicked(string collectionId, string collectionName)
    signal createCollectionRequested(string name)
    signal imageDropped(string collectionId, string imageId)
    signal removeCollectionRequested(string collectionId, string collectionName)

    // New collection input area — pill input matching ChipSearchSection's
    // "new tag"/"new category" pattern.
    Item {
        id: newCollectionArea
        anchors { top: parent.top; left: parent.left; right: parent.right }
        height: 48

        function _submit() {
            var name = newCollectionInput.text.trim()
            if (name.length > 0) {
                root.createCollectionRequested(name)
                newCollectionInput.text = ""
            }
        }

        Rectangle {
            id: newCollectionInputBox
            objectName: "newCollectionInputBox"
            property alias borderColor: newCollectionInputBox.border.color
            anchors {
                left: parent.left; leftMargin: Theme.horizontalMargin
                right: parent.right; rightMargin: Theme.horizontalMargin
                verticalCenter: parent.verticalCenter
            }
            height: 26
            radius: 13
            color: Theme.surface
            border.color: newCollectionInput.activeFocus ? Theme.accent : Theme.border
            border.width: 1

            Text {
                id: addIcon
                objectName: "addIcon"
                anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                text: "+"
                font.pixelSize: Theme.fontSizeSm
                color: Theme.textMuted
            }

            Rectangle {
                id: submitBtn
                objectName: "submitBtn"
                visible: newCollectionInput.text.trim().length > 0
                anchors { right: parent.right; rightMargin: 3; verticalCenter: parent.verticalCenter }
                width: 20; height: 20; radius: 10
                color: submitArea.containsMouse ? Theme.border : "transparent"

                Text {
                    id: submitIcon
                    objectName: "submitIcon"
                    anchors.centerIn: parent
                    text: "↵"
                    font.pixelSize: Theme.fontSizeSm
                    color: Theme.success
                }

                MouseArea {
                    id: submitArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: newCollectionArea._submit()
                }
            }

            TextInput {
                id: newCollectionInput
                objectName: "newCollectionInput"
                anchors {
                    left: addIcon.right; leftMargin: 4
                    right: submitBtn.left; rightMargin: 2
                    verticalCenter: parent.verticalCenter
                }
                color: Theme.text
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
                clip: true

                Text {
                    anchors.fill: parent
                    visible: newCollectionInput.text.length === 0
                    text: "New collection…"
                    color: Theme.textMuted
                    font.pixelSize: Theme.fontSizeSm
                    font.family: Theme.fontFamily
                }

                Keys.priority: Keys.BeforeItem
                Keys.onReturnPressed: function(event) { event.accepted = true; newCollectionArea._submit() }
                Keys.onEnterPressed:  function(event) { event.accepted = true; newCollectionArea._submit() }
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
            onRemoveRequested: (cid, cname) => root.removeCollectionRequested(cid, cname)
        }

        Text {
            id: emptyLabel
            objectName: "emptyLabel"
            anchors.centerIn: parent
            visible: collectionList.count === 0
            text: "No collections yet"
            color: Theme.textMuted
            font.pixelSize: Theme.fontSizeSm
        }
    }
}
