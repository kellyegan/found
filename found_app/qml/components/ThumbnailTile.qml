import QtQuick

Item {
    id: root

    property string imageId: ""
    property string thumbnailUrl: ""
    property string fileStatus: "available"
    property bool selected: false
    property bool active: false
    property int inset: 0

    signal tileClicked(string imageId, int modifiers)
    signal tileDoubleClicked(string imageId)
    signal removeRequested(string imageId)
    signal locateRequested(string imageId)

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

        // Selection / active border — 2px for active, 1px for selected-only
        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.color: Theme.accent
            border.width: root.active ? 2 : (root.selected ? 1 : 0)
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
            // Clicks within the inset border (the visual gap between tiles) deselect.
            // Only clicks that land on the painted image area select the tile.
            var isInner = mouse.x >= root.inset && mouse.x <= root.width  - root.inset
                       && mouse.y >= root.inset && mouse.y <= root.height - root.inset
            if (isInner)
                root.tileClicked(root.imageId, mouse.modifiers)
            else
                SelectionManager.clear()
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

    // Locate button — always visible when file is missing, upper-left corner
    Rectangle {
        id: locateButton
        width: 22
        height: 22
        radius: 11
        anchors { top: parent.top; left: parent.left; margins: root.inset + 4 }
        color: locateArea.containsMouse ? "#ffffff" : "#aaffffff"
        visible: root.fileStatus === "missing"

        Text {
            anchors.centerIn: parent
            text: "⚠"
            color: "#555555"
            font.pixelSize: 11
        }

        MouseArea {
            id: locateArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.locateRequested(root.imageId)
        }
    }

    // Tooltip parented to the window so it renders above all sibling tiles.
    // Gate x/y on containsMouse so mapToGlobal runs after the tile is positioned.
    HoverTooltip {
        parent: root.Window.contentItem ?? root
        text: "File missing — click to locate"
        visible: locateArea.containsMouse

        x: {
            if (!locateArea.containsMouse) return 0
            var g = locateButton.mapToGlobal(0, locateButton.height / 2)
            var p = parent.mapFromGlobal(g.x, g.y)
            // Default: right of button; fall back to left if tooltip would overflow
            var rightX = p.x + locateButton.width + 8
            return (rightX + width <= parent.width) ? rightX : p.x - width - 8
        }
        y: {
            if (!locateArea.containsMouse) return 0
            var g = locateButton.mapToGlobal(0, locateButton.height / 2)
            var p = parent.mapFromGlobal(g.x, g.y)
            // Sit slightly above button centre for a diagonal offset
            return p.y - height / 2 - 8
        }
    }
}
