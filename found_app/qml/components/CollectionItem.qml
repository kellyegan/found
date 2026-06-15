import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property string collectionId: ""
    property string collectionName: ""
    property bool isDropTarget: false

    signal clicked(string collectionId, string collectionName)
    signal imageDropped(string collectionId, string imageId)
    signal removeRequested(string collectionId, string collectionName)

    implicitHeight: 36
    color: isDropTarget ? Qt.tint(Theme.surface, Qt.rgba(0, 1, 0, 0.15)) : (hoverArea.containsMouse ? Theme.surface : "transparent")
    radius: 4

    Behavior on color { ColorAnimation { duration: 100 } }

    // hoverArea declared first so removeBtn/removeArea sits above it in z-order
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

    Text {
        objectName: "collectionNameText"
        anchors {
            left: parent.left; leftMargin: 12
            right: removeBtn.left; rightMargin: Theme.spacingMd
            verticalCenter: parent.verticalCenter
        }
        text: root.collectionName
        color: root.isDropTarget ? Theme.success : Theme.text
        font.pixelSize: Theme.fontSizeMd
        font.weight: Font.DemiBold
        font.capitalization: Font.AllUppercase
        elide: Text.ElideRight
    }

    Rectangle {
        id: removeBtn
        objectName: "removeBtn"
        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
        width: 20
        height: 20
        radius: 4
        visible: hoverArea.containsMouse || removeArea.containsMouse
        color: removeArea.containsMouse ? Qt.tint(Theme.surface, Qt.rgba(1, 0, 0, 0.2)) : "transparent"

        Text {
            objectName: "removeIconText"
            anchors.centerIn: parent
            text: "×"
            font.pixelSize: Theme.fontSizeMd
            color: removeArea.containsMouse ? Theme.warning : Theme.textMuted
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
        id: dropBorder
        objectName: "dropBorder"
        property alias borderColor: dropBorder.border.color
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        border.color: Theme.success
        border.width: root.isDropTarget ? 1 : 0
        visible: root.isDropTarget
    }
}
