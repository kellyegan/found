import QtQuick
import Found.Theme 1.0
import "../primitives"

SidePanelBody {
    id: root

    panelId: "collections"
    title: ""
    panelIcon: "☰"
    dragOpenKeys: ["found/image"]

    property var collections: []

    signal collectionClicked(string collectionId, string collectionName)
    signal createCollectionRequested(string name)
    signal imageDropped(string collectionId, string imageId)
    signal removeCollectionRequested(string collectionId, string collectionName)

    // New collection input area
    Item {
        id: newCollectionArea
        anchors { top: parent.top; left: parent.left; right: parent.right }
        height: 48

        function _submit() {
            var name = newCollectionField.text.trim()
            if (name.length > 0) {
                root.createCollectionRequested(name)
                newCollectionField.text = ""
            }
        }

        AppTextField {
            id: newCollectionField
            objectName: "newCollectionField"
            anchors {
                left: parent.left; leftMargin: Theme.horizontalMargin
                right: parent.right; rightMargin: Theme.horizontalMargin
                verticalCenter: parent.verticalCenter
            }
            height: 36
            fontSize: Theme.fontSizeMd
            fontCapitalization: Font.AllUppercase
            pill: false
            leadingIcon: "+"
            trailingVisible: text.trim().length > 0
            placeholderText: "Add collection…"
            onSubmitted: newCollectionArea._submit()
            onEscaped: { text = ""; blur() }
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
