import QtQuick

Item {
    id: root

    property string imageId: ""
    property string thumbnailUrl: ""
    property string fileStatus: "available"
    property bool selected: false
    property int inset: 0

    signal tileClicked(string imageId, int modifiers)
    signal tileDoubleClicked(string imageId)

    // DragHandler tracks the gesture without moving the tile
    DragHandler {
        id: dragHandler
        target: null
        onActiveChanged: {
            if (active) {
                dragProxy.Drag.active = true
            } else {
                dragProxy.Drag.drop()
            }
        }
    }

    // Floating proxy parented to the window so it can move across the whole scene
    Item {
        id: dragProxy
        parent: root.Window.contentItem ?? root
        width: root.width - 2 * root.inset
        height: root.height - 2 * root.inset
        visible: Drag.active

        x: {
            if (!dragHandler.active) return 0
            var g = root.mapToGlobal(dragHandler.centroid.position.x, dragHandler.centroid.position.y)
            return dragProxy.parent.mapFromGlobal(g.x, g.y).x - width / 2
        }
        y: {
            if (!dragHandler.active) return 0
            var g = root.mapToGlobal(dragHandler.centroid.position.x, dragHandler.centroid.position.y)
            return dragProxy.parent.mapFromGlobal(g.x, g.y).y - height / 2
        }

        property string imageId: root.imageId

        Drag.keys: ["found/image"]
        Drag.hotSpot.x: width / 2
        Drag.hotSpot.y: height / 2

        Rectangle {
            anchors.fill: parent
            color: Theme.surface
            opacity: 0.9
            border.color: Theme.accent
            border.width: 2
            radius: 3

            Image {
                anchors { fill: parent; margins: 2 }
                source: root.thumbnailUrl
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                smooth: true
            }
        }
    }

    Rectangle {
        anchors { fill: parent; margins: root.inset }
        color: Theme.surface
        opacity: dragHandler.active ? 0.4 : 1.0

        Image {
            id: img
            anchors.fill: parent
            source: root.thumbnailUrl
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            smooth: true
        }

        // Loading placeholder — visible while thumbnail is in flight or not yet assigned
        Rectangle {
            anchors.fill: parent
            color: Theme.surface
            visible: root.thumbnailUrl === "" || img.status === Image.Loading
        }

        // Failed placeholder — generic dark square when load fails
        Rectangle {
            anchors.fill: parent
            color: "#1e1e1e"
            visible: img.status === Image.Error

            Text {
                anchors.centerIn: parent
                text: "?"
                font.pixelSize: 18
                color: Theme.textMuted
            }
        }

        // Missing-image indicator overlay
        Rectangle {
            anchors.fill: parent
            color: "#000000"
            opacity: 0.45
            visible: root.fileStatus === "missing"

            Text {
                anchors.centerIn: parent
                text: "!"
                font.pixelSize: 16
                font.weight: Font.Bold
                color: "#ff8800"
            }
        }

        // Selection highlight
        Rectangle {
            anchors.fill: parent
            color: Theme.accent
            opacity: 0.30
            visible: root.selected
        }

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.color: Theme.accent
            border.width: root.selected ? 2 : 0
        }
    }

    // MouseArea covers the full cell so the gap between tiles is also clickable
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onClicked: function(mouse) {
            root.tileClicked(root.imageId, mouse.modifiers)
        }
        onDoubleClicked: function(mouse) {
            root.tileDoubleClicked(root.imageId)
        }
    }
}
