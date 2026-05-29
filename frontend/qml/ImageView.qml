import QtQuick

Item {
    id: root

    property string imageId: ""
    property string imageUrl: ""
    property string filename: ""
    property string fileStatus: "available"
    property bool hasNext: false
    property bool hasPrev: false

    property real zoomLevel: 1.0
    property real panOffsetX: 0.0
    property real panOffsetY: 0.0

    readonly property real _minZoom: 0.25
    readonly property real _maxZoom: 8.0

    function resetView() {
        zoomLevel  = 1.0
        panOffsetX = 0.0
        panOffsetY = 0.0
    }

    function _clampPan() {
        var maxX = Math.max(0, (root.width  * zoomLevel - root.width)  / 2)
        var maxY = Math.max(0, (root.height * zoomLevel - root.height) / 2)
        panOffsetX = Math.max(-maxX, Math.min(maxX, panOffsetX))
        panOffsetY = Math.max(-maxY, Math.min(maxY, panOffsetY))
    }

    // Reset zoom when image changes
    onImageIdChanged: resetView()

    // Arrow key navigation
    Shortcut {
        sequence: "Right"
        onActivated: if (root.hasNext) NavigationManager.goNext()
    }

    Shortcut {
        sequence: "Left"
        onActivated: if (root.hasPrev) NavigationManager.goPrev()
    }

    // Immersive / fullscreen
    Shortcut {
        sequence: "F"
        onActivated: NavigationManager.toggleImmersive()
    }

    Shortcut {
        sequence: "Escape"
        onActivated: {
            if (NavigationManager.immersiveMode)
                NavigationManager.setImmersive(false)
            else
                NavigationManager.goBack()
        }
    }

    // Keyboard zoom
    Shortcut {
        sequence: "="
        onActivated: root.zoomLevel = Math.min(root._maxZoom, root.zoomLevel * 1.25)
    }

    Shortcut {
        sequence: "+"
        onActivated: root.zoomLevel = Math.min(root._maxZoom, root.zoomLevel * 1.25)
    }

    Shortcut {
        sequence: "-"
        onActivated: {
            root.zoomLevel = Math.max(root._minZoom, root.zoomLevel / 1.25)
            root._clampPan()
        }
    }

    Shortcut {
        sequence: "0"
        onActivated: root.resetView()
    }

    Rectangle {
        anchors.fill: parent
        color: "#111111"
        clip: true

        // Zoomable + pannable image container
        Item {
            id: imageContainer
            anchors.centerIn: parent
            width: parent.width
            height: parent.height

            transform: [
                Translate { x: root.panOffsetX; y: root.panOffsetY },
                Scale { origin.x: imageContainer.width / 2; origin.y: imageContainer.height / 2; xScale: root.zoomLevel; yScale: root.zoomLevel }
            ]

            // Full-resolution image
            Image {
                id: img
                anchors.fill: parent
                source: root.imageUrl
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                smooth: true
                visible: img.status === Image.Ready
            }
        }

        // Loading indicator
        Item {
            anchors.centerIn: parent
            visible: img.status === Image.Loading && root.imageUrl !== ""
            z: 1

            Text {
                anchors.centerIn: parent
                text: "Loading…"
                color: "#888888"
                font.pixelSize: 14
            }
        }

        // Error state
        Item {
            anchors.centerIn: parent
            visible: img.status === Image.Error
            z: 1

            Text {
                anchors.centerIn: parent
                text: "Failed to load image"
                color: "#ff4444"
                font.pixelSize: 14
            }
        }

        // Missing-file overlay
        Item {
            anchors.centerIn: parent
            visible: root.fileStatus === "missing"
            z: 1

            Column {
                anchors.centerIn: parent
                spacing: 8

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "!"
                    color: "#ff8800"
                    font.pixelSize: 48
                    font.weight: Font.Bold
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "File not found"
                    color: "#888888"
                    font.pixelSize: 14
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: root.filename
                    color: "#666666"
                    font.pixelSize: 12
                }
            }
        }

        // Mouse wheel zoom — centered on cursor position
        WheelHandler {
            id: wheelHandler
            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            onWheel: function(event) {
                var factor = event.angleDelta.y > 0 ? 1.15 : (1.0 / 1.15)
                var newZoom = Math.max(root._minZoom, Math.min(root._maxZoom, root.zoomLevel * factor))
                if (newZoom === root.zoomLevel) return

                // Adjust pan so zoom centres on the cursor
                var cursorX = event.x - imageContainer.width  / 2
                var cursorY = event.y - imageContainer.height / 2
                root.panOffsetX += cursorX * (1 - newZoom / root.zoomLevel)
                root.panOffsetY += cursorY * (1 - newZoom / root.zoomLevel)
                root.zoomLevel = newZoom
                root._clampPan()
            }
        }

        // Drag to pan
        DragHandler {
            id: dragHandler
            enabled: root.zoomLevel > 1.0
            onTranslationChanged: {
                root.panOffsetX += translation.x - (root._lastDragX ?? 0)
                root.panOffsetY += translation.y - (root._lastDragY ?? 0)
                root._lastDragX = translation.x
                root._lastDragY = translation.y
                root._clampPan()
            }
            onActiveChanged: {
                if (!active) {
                    root._lastDragX = 0
                    root._lastDragY = 0
                }
            }
        }

        // Double-click to reset zoom
        TapHandler {
            onTapped: { if (tapCount >= 2) root.resetView() }
        }
    }

    // Internal drag tracking — not part of public API
    property real _lastDragX: 0
    property real _lastDragY: 0
}
