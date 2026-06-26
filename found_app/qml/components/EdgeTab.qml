import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property string edge: "right"   // "left" | "right"
    property bool open: false
    property string icon: ""
    property string tooltip: ""

    // Commit 4: panel identity and drag state
    property string panelId: ""
    property bool dragActive: false
    property var dragOpenKeys: []   // MIME keys that spring-open this panel on drag hover

    signal clicked()
    signal toggleRequested()
    signal layoutRequested(string targetEdge, int targetSideIndex)

    width: 16
    height: 72
    color: Theme.surface
    radius: 2
    topLeftRadius: root.edge === "left" ? 0 : 12
    bottomLeftRadius: root.edge === "left" ? 0 : 12
    topRightRadius: root.edge === "right" ? 0 : 12
    bottomRightRadius: root.edge === "right" ? 0 : 12

    Column {
        anchors.centerIn: parent
        spacing: 4

        Text {
            objectName: "edgeTabIcon"
            visible: root.icon !== ""
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.icon
            font.pixelSize: Theme.fontSizeSm
            color: Theme.textMuted
        }

        Text {
            objectName: "edgeTabArrow"
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.edge === "right"
                  ? (root.open ? "▶" : "◀")
                  : (root.open ? "◀" : "▶")
            font.pixelSize: Theme.fontSizeSm
            color: Theme.textMuted
        }
    }

    // Spring-open: hovering a compatible drag over the tab opens the panel
    DropArea {
        anchors.fill: parent
        keys: root.dragOpenKeys
        enabled: root.dragOpenKeys.length > 0 && !root.open
        z: 3
        onEntered: root.toggleRequested()
    }

    // Hover gives pointer cursor; TapHandler detects click without blocking DragHandler
    HoverHandler { cursorShape: Qt.PointingHandCursor }

    TapHandler {
        onTapped: {
            root.clicked()
            root.toggleRequested()
        }
    }

    // ── Drag gesture ─────────────────────────────────────────────────────────

    DragHandler {
        id: dragHandler
        target: null
        grabPermissions: PointerHandler.CanTakeOverFromHandlersOfSameType

        property bool _canceled: false

        onCanceled: _canceled = true

        onActiveChanged: {
            root.dragActive = active
            if (!active) {
                if (!_canceled && root.Window.contentItem) {
                    var p = root.mapToItem(root.Window.contentItem, centroid.position)
                    var tEdge = p.x < root.Window.width / 2 ? "left" : "right"
                    var tIdx = root._calcSlotIndex(tEdge, p.y)
                    root.layoutRequested(tEdge, tIdx)
                }
                _canceled = false
            }
        }
    }

    // Ghost tab shown over the window content during drag
    Rectangle {
        id: ghost
        parent: root.Window.contentItem ? root.Window.contentItem : root
        visible: dragHandler.active && !!root.Window.contentItem
        width: root.width
        height: root.height
        color: root.color
        opacity: 0.7
        radius: 2
        border.width: 1
        border.color: Theme.text

        readonly property string ghostEdge: {
            if (!dragHandler.active || !root.Window.contentItem) return root.edge
            var p = root.mapToItem(root.Window.contentItem, dragHandler.centroid.position)
            return p.x < root.Window.width / 2 ? "left" : "right"
        }

        topLeftRadius: ghostEdge === "left" ? 0 : 12
        bottomLeftRadius: ghostEdge === "left" ? 0 : 12
        topRightRadius: ghostEdge === "right" ? 0 : 12
        bottomRightRadius: ghostEdge === "right" ? 0 : 12

        x: !root.Window.contentItem ? 0
           : (ghostEdge === "left" ? 0 : root.Window.width - width)

        y: {
            if (!dragHandler.active || !root.Window.contentItem) return 0
            var p = root.mapToItem(root.Window.contentItem, dragHandler.centroid.position)
            return root._snapY(ghostEdge, p.y)
        }

        Column {
            anchors.centerIn: parent
            spacing: 4
            Text {
                visible: root.icon !== ""
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.icon
                font.pixelSize: Theme.fontSizeSm
                color: Theme.textMuted
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: ghost.ghostEdge === "right" ? "◀" : "▶"
                font.pixelSize: Theme.fontSizeSm
                color: Theme.textMuted
            }
        }
    }

    // Insertion indicator: 2 px accent line just above the ghost
    Rectangle {
        parent: root.Window.contentItem ? root.Window.contentItem : root
        visible: dragHandler.active && !!root.Window.contentItem
        width: root.width + 4
        height: 2
        color: Theme.accent
        x: ghost.x - 2
        y: ghost.y - 3
    }

    // ── Slot-position helpers ─────────────────────────────────────────────────

    // How many peers-above-cursor on targetEdge → that's the insertion index
    function _calcSlotIndex(targetEdge, cursorY) {
        if (!PanelLayout || !PanelLayout.order || !root.Window.contentItem) return 0
        var peers = PanelLayout.order.filter(function(p) {
            return PanelLayout.edges[p] === targetEdge && p !== root.panelId
        })
        var winH = root.Window.height
        var tabH = root.height
        var spacing = 8
        var totalH = peers.length * tabH + Math.max(0, peers.length - 1) * spacing
        var startY = (winH - totalH) / 2
        for (var i = 0; i < peers.length; i++) {
            if (cursorY < startY + i * (tabH + spacing) + tabH / 2) return i
        }
        return peers.length
    }

    // Y position for the ghost at the given slot on targetEdge
    function _snapY(targetEdge, cursorY) {
        var slot = _calcSlotIndex(targetEdge, cursorY)
        if (!PanelLayout || !PanelLayout.order || !root.Window.contentItem) return cursorY
        var peers = PanelLayout.order.filter(function(p) {
            return PanelLayout.edges[p] === targetEdge && p !== root.panelId
        })
        var winH = root.Window.height
        var tabH = root.height
        var spacing = 8
        var allSlots = peers.length + 1
        var totalH = allSlots * tabH + Math.max(0, allSlots - 1) * spacing
        var startY = (winH - totalH) / 2
        return startY + slot * (tabH + spacing)
    }
}
