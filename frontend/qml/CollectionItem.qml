import QtQuick

Rectangle {
    id: root

    property string collectionId: ""
    property string collectionName: ""
    property bool isDropTarget: false

    signal clicked(string collectionId, string collectionName)
    signal imageDropped(string collectionId, string imageId)

    implicitHeight: 36
    color: isDropTarget ? "#2a3a2a" : (hoverArea.containsMouse ? "#252525" : "transparent")
    radius: 4

    Behavior on color { ColorAnimation { duration: 100 } }

    Row {
        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 12 }
        spacing: 8

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.collectionName
            color: root.isDropTarget ? "#88cc88" : "#cccccc"
            font.pixelSize: 13
            elide: Text.ElideRight
            width: parent.width
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
