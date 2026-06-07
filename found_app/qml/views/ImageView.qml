import QtQuick
import QtQuick.Window
import "../components"

Item {
    id: root

    property string imageId: ""
    property string imageUrl: ""
    property string filename: ""
    property string fileStatus: "available"
    property bool hasNext: false
    property bool hasPrev: false

    // Inset from left/right edges so buttons clear the panel edge tabs.
    // 40 = 16px edge-tab + 24px gap. Measured from the viewport edge, so
    // rightInset stays 40 whether the metadata panel is open or not —
    // the viewport itself shrinks via rightPanelWidth.
    property real leftInset: 40
    property real rightInset: 40

    // Width of the metadata panel when open; shrinks the viewport so the
    // image re-centres in the remaining area. Animated to match panel slide.
    property real rightPanelWidth: 0
    Behavior on rightPanelWidth { NumberAnimation { duration: 200; easing.type: Easing.InOutQuad } }

    signal prevRequested()
    signal nextRequested()
    signal imageLoadFailed(string imageId)
    signal removeImageRequested(string imageId)

    // Pending removal — drives the confirmation dialog below. Always targets
    // only the image currently being viewed, never other selected images.
    property string _removeId: ""
    property string _removeMessage: ""

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

    // Remove the currently-viewed image from the library — never affects any
    // other selected images, and stays out of the way of text inputs (e.g.
    // the metadata sidebar's tag/category editors).
    Shortcut {
        sequences: [StandardKey.Delete, "Backspace"]
        enabled: root.visible && !(Window.activeFocusItem instanceof TextInput)
        onActivated: {
            if (root.imageId === "") return
            root._removeId = root.imageId
            root._removeMessage = "Are you sure you want to remove " + root.filename + " from the library?"
        }
    }

    // Keyboard zoom — steps without cursor anchoring
    Shortcut { sequence: "="; enabled: root.visible; onActivated: { root.zoomLevel = Math.min(root._maxZoom, root.zoomLevel * 1.25); root._clampPan() } }
    Shortcut { sequence: "+"; enabled: root.visible; onActivated: { root.zoomLevel = Math.min(root._maxZoom, root.zoomLevel * 1.25); root._clampPan() } }
    Shortcut { sequence: "-"; enabled: root.visible; onActivated: { root.zoomLevel = Math.max(root._minZoom, root.zoomLevel / 1.25); root._clampPan() } }
    Shortcut { sequence: "0"; enabled: root.visible; onActivated: root.resetView() }

    // Background fills the full root area so the bottom margin strip matches the viewport.
    Rectangle { anchors.fill: parent; color: "#111111" }

    Rectangle {
        id: viewport
        anchors.fill: parent
        anchors.bottomMargin: NavigationManager.immersiveMode ? 0 : 48
        anchors.rightMargin: root.rightPanelWidth
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
            onStatusChanged: {
                if (status === Image.Error && root.imageUrl !== "")
                    root.imageLoadFailed(root.imageId)
            }
        }

        // Loading indicator
        Text {
            anchors.centerIn: parent
            visible: img.status === Image.Loading && root.imageUrl !== ""
            text: "Loading…"
            color: Theme.textMuted
            font.pixelSize: Theme.fontSizeMd
            z: 1
        }

        // Error overlay — shown when the file is missing or the image cannot be decoded.
        // fileStatus === "missing"  → file no longer exists at its recorded path
        // img.status === Image.Error with an available file → decode failure (e.g. very
        //   large image that exhausted memory, unsupported codec, corrupt data)
        Column {
            anchors.centerIn: parent
            visible: root.fileStatus === "missing" || (img.status === Image.Error && root.imageUrl !== "")
            spacing: 8
            z: 1

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "!"
                color: Theme.warningColor
                font.pixelSize: 48
                font.weight: Font.Bold
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.fileStatus === "missing" ? "File not found" : "Could not display image"
                color: Theme.textMuted
                font.pixelSize: Theme.fontSizeMd
           }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.filename
                color: Theme.textMuted
                font.pixelSize: Theme.fontSizeSm
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

    ConfirmDialog {
        id: removeDialog
        anchors.fill: parent
        z: 50
        open: root._removeId !== ""
        message: root._removeMessage
        onConfirmed: {
            var idToRemove = root._removeId
            root._removeId = ""
            root._removeMessage = ""
            if (root.hasNext) NavigationManager.goNext()
            else if (root.hasPrev) NavigationManager.goPrev()
            else NavigationManager.goBack()
            root.removeImageRequested(idToRemove)
        }
        onCancelled: {
            root._removeId = ""
            root._removeMessage = ""
        }
    }
}
