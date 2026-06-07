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
    signal removeRequested(string imageId)

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
        color: "transparent"
        opacity: dragHandler.active ? 0.4 : 1.0

        // Selection highlight
        Rectangle {
            anchors.fill: parent
            color: Theme.accent
            opacity: 0.20
            visible: root.selected
        }

        Image {
            id: img
            anchors.fill: parent
            source: root.thumbnailUrl
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            smooth: true

            // DragHandler scoped to the painted image pixels — gestures on the
            // transparent letterbox area fall through to the grid for scrolling
            Item {
                anchors.centerIn: parent
                width: img.paintedWidth
                height: img.paintedHeight

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
            }
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

        // Selection highlight border
        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.color: Theme.accent
            border.width: root.selected ? 1 : 0
        }

    }

    // MouseArea covers the full cell so the gap between tiles is also clickable
    MouseArea {
        id: tileMouseArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        onClicked: function(mouse) {
            forceActiveFocus()
            root.tileClicked(root.imageId, mouse.modifiers)
        }
        onDoubleClicked: function(mouse) {
            root.tileDoubleClicked(root.imageId)
        }
    }

    // Hover-revealed remove button — top-right corner
    Rectangle {
        id: removeButton
        width: 20
        height: 20
        radius: 10
        anchors { top: parent.top; right: parent.right; margins: root.inset + 4 }
        color: removeArea.containsMouse ? "#cc4444" : "#00000099"
        visible: tileMouseArea.containsMouse

        Text {
            anchors.centerIn: parent
            text: "✕"
            color: "#ffffff"
            font.pixelSize: 11
        }

        MouseArea {
            id: removeArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.removeRequested(root.imageId)
        }
    }
}
