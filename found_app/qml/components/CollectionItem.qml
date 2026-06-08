import QtQuick

Rectangle {
    id: root

    property string collectionId: ""
    property string collectionName: ""
    property bool isDropTarget: false

    signal clicked(string collectionId, string collectionName)
    signal imageDropped(string collectionId, string imageId)
    signal removeRequested(string collectionId, string collectionName)

    implicitHeight: 36
    color: isDropTarget ? "#2a3a2a" : (hoverArea.containsMouse ? "#252525" : "transparent")
    radius: 4

    Behavior on color { ColorAnimation { duration: 100 } }

    Text {
        anchors {
            left: parent.left; leftMargin: 12
            right: removeBtn.left; rightMargin: Theme.spacingMd
            verticalCenter: parent.verticalCenter
        }
        text: root.collectionName
        color: root.isDropTarget ? "#88cc88" : "#cccccc"
        font.pixelSize: Theme.fontSizeMd
        font.weight: Font.DemiBold
        font.capitalization: Font.AllUppercase
        elide: Text.ElideRight
    }

    Rectangle {
        id: removeBtn
        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
        width: 20
        height: 20
        radius: 4
        visible: hoverArea.containsMouse || removeArea.containsMouse
        color: removeArea.containsMouse ? "#4a2a2a" : "transparent"

        Text {
            anchors.centerIn: parent
            text: "×"
            font.pixelSize: 15
            color: removeArea.containsMouse ? "#ff8888" : "#888888"
        }

        MouseArea {
            id: removeArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.removeRequested(root.collectionId, root.collectionName)
        }
    }

    // Drop target highlight border
    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        border.color: "#44aa44"
        border.width: root.isDropTarget ? 1 : 0
        visible: root.isDropTarget
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.clicked(root.collectionId, root.collectionName)
    }

    DropArea {
        anchors.fill: parent
        keys: ["found/image"]
        onEntered: function(drag) { root.isDropTarget = true }
        onExited: root.isDropTarget = false
        onDropped: function(drop) {
            root.isDropTarget = false
            var iid = drop.source ? (drop.source.imageId ?? "") : ""
            if (iid !== "") root.imageDropped(root.collectionId, iid)
        }
    }
}
