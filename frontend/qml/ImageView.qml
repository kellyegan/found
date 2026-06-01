import QtQuick

Item {
    id: root

    property string imageId: ""
    property string imageUrl: ""
    property string filename: ""
    property string fileStatus: "available"
    property bool hasNext: false
    property bool hasPrev: false

    // Inset from left/right edges so buttons clear the panel edge tabs.
    // 40 = 16px edge-tab + 24px gap (panels closed).
    // 300 = 260px panel + 16px edge-tab + 24px gap (panels open).
    property real leftInset: 40
    property real rightInset: 40

    signal prevRequested()
    signal nextRequested()

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

    // Clamp pan so image edges don't pull past the viewport centre.
    // panOffset is in screen pixels — same unit as the image x/y position.
    function _clampPan() {
        var maxX = Math.max(0, viewport.width  * (zoomLevel - 1) / 2)
        var maxY = Math.max(0, viewport.height * (zoomLevel - 1) / 2)
        panOffsetX = Math.max(-maxX, Math.min(maxX, panOffsetX))
        panOffsetY = Math.max(-maxY, Math.min(maxY, panOffsetY))
    }

    onImageIdChanged: resetView()

    // All shortcuts scoped to this view via enabled: root.visible

    // Arrow key navigation
    Shortcut { sequence: "Right";   enabled: root.visible; onActivated: if (root.hasNext) NavigationManager.goNext() }
    Shortcut { sequence: "Left";    enabled: root.visible; onActivated: if (root.hasPrev) NavigationManager.goPrev() }

    // Space — toggle back to the grid (same key that opened image view)
    Shortcut { sequence: "Space";   enabled: root.visible; onActivated: NavigationManager.goBack() }

    // Immersive / fullscreen
    Shortcut {
        sequence: "F"
        enabled: root.visible
        onActivated: NavigationManager.toggleImmersive()
    }
    Shortcut {
        sequence: "Escape"
        enabled: root.visible
        onActivated: {
            if (NavigationManager.immersiveMode) NavigationManager.setImmersive(false)
            else NavigationManager.goBack()
        }
    }

    // Keyboard zoom — steps without cursor anchoring
    Shortcut { sequence: "="; enabled: root.visible; onActivated: { root.zoomLevel = Math.min(root._maxZoom, root.zoomLevel * 1.25); root._clampPan() } }
    Shortcut { sequence: "+"; enabled: root.visible; onActivated: { root.zoomLevel = Math.min(root._maxZoom, root.zoomLevel * 1.25); root._clampPan() } }
    Shortcut { sequence: "-"; enabled: root.visible; onActivated: { root.zoomLevel = Math.max(root._minZoom, root.zoomLevel / 1.25); root._clampPan() } }
    Shortcut { sequence: "0"; enabled: root.visible; onActivated: root.resetView() }

    Rectangle {
        id: viewport
        anchors.fill: parent
        color: "#111111"
        clip: true

        // Image is sized and positioned directly — no transforms.
        // width  = viewport × zoom  → scaling is just making the element bigger.
        // x      = centred + panOffsetX  → pan is a plain pixel offset.
        // This makes pan always 1:1 with mouse movement regardless of zoom level.
        Image {
            id: img
            width:  viewport.width  * root.zoomLevel
            height: viewport.height * root.zoomLevel
            x: (viewport.width  - width)  / 2 + root.panOffsetX
            y: (viewport.height - height) / 2 + root.panOffsetY
            source: root.imageUrl
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            smooth: true
            visible: status === Image.Ready
        }

        // Loading indicator
        Text {
            anchors.centerIn: parent
            visible: img.status === Image.Loading && root.imageUrl !== ""
            text: "Loading…"
            color: "#888888"
            font.pixelSize: 14
            z: 1
        }

        // Load error
        Text {
            anchors.centerIn: parent
            visible: img.status === Image.Error
            text: "Failed to load image"
            color: "#ff4444"
            font.pixelSize: 14
            z: 1
        }

        // Missing file overlay
        Column {
            anchors.centerIn: parent
            visible: root.fileStatus === "missing"
            spacing: 8
            z: 1

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

        // Mouse-wheel zoom — keeps the pixel under the cursor stationary.
        // Formula: cursor maps to the same fractional position in the image
        // before and after zoom, so we derive the new panOffset from the
        // old image top-left position and the cursor location.
        WheelHandler {
            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            onWheel: function(event) {
                var factor  = event.angleDelta.y > 0 ? 1.15 : (1.0 / 1.15)
                var oldZoom = root.zoomLevel
                var newZoom = Math.max(root._minZoom, Math.min(root._maxZoom, oldZoom * factor))
                if (newZoom === oldZoom) return

                // Top-left of the image in viewport coordinates before zoom
                var oldImgX = (viewport.width  - viewport.width  * oldZoom) / 2 + root.panOffsetX
                var oldImgY = (viewport.height - viewport.height * oldZoom) / 2 + root.panOffsetY

                // New top-left that keeps event.x/y on the same image pixel
                var newImgX = event.x - (event.x - oldImgX) * newZoom / oldZoom
                var newImgY = event.y - (event.y - oldImgY) * newZoom / oldZoom

                root.zoomLevel  = newZoom
                root.panOffsetX = newImgX - (viewport.width  - viewport.width  * newZoom) / 2
                root.panOffsetY = newImgY - (viewport.height - viewport.height * newZoom) / 2
                root._clampPan()
            }
        }

        // Drag to pan — stores the pan position at drag start and adds the
        // cumulative translation directly. No delta accumulation needed.
        DragHandler {
            enabled: root.zoomLevel > 1.0

            property real _startX: 0
            property real _startY: 0

            onActiveChanged: {
                if (active) {
                    _startX = root.panOffsetX
                    _startY = root.panOffsetY
                }
            }
            onTranslationChanged: {
                root.panOffsetX = _startX + translation.x
                root.panOffsetY = _startY + translation.y
                root._clampPan()
            }
        }

        // Double-click resets zoom and pan
        TapHandler {
            onTapped: { if (tapCount >= 2) root.resetView() }
        }

        // ── Prev / Next hover buttons ─────────────────────────────────────
        // The Item spans full height so the MouseArea captures hover anywhere
        // along the edge. The visible square badge is centered within it.

        Item {
            id: prevBtn
            anchors { left: parent.left; leftMargin: root.leftInset; top: parent.top; bottom: parent.bottom }
            width: 108
            z: 2
            visible: root.hasPrev

            Rectangle {
                anchors.centerIn: parent
                width: 100
                height: 100
                radius: 4
                color: "#cc000000"
                opacity: prevBtnArea.containsMouse ? 0.75 : 0.0
                Behavior on opacity { NumberAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "◀"
                    color: "#d9d9d9"
                    font.pixelSize: 50
                }
            }

            MouseArea {
                id: prevBtnArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.prevRequested()
            }
        }

        Item {
            id: nextBtn
            anchors { right: parent.right; rightMargin: root.rightInset; top: parent.top; bottom: parent.bottom }
            width: 108
            z: 2
            visible: root.hasNext

            Rectangle {
                anchors.centerIn: parent
                width: 100
                height: 100
                radius: 4
                color: "#cc000000"
                opacity: nextBtnArea.containsMouse ? 0.75 : 0.0
                Behavior on opacity { NumberAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "▶"
                    color: "#d9d9d9"
                    font.pixelSize: 50
                }
            }

            MouseArea {
                id: nextBtnArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.nextRequested()
            }
        }
    }
}
