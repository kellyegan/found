import QtQuick
import Found.Theme 1.0

Item {
    id: root

    property string panelId: ""

    // Computed from PanelLayout when panelId is set; falls back to "right" when
    // PanelLayout is unavailable (e.g. offscreen test engines without PanelLayout).
    property string edge: (PanelLayout && PanelLayout.edges && panelId)
                          ? (PanelLayout.edges[panelId] ?? "right")
                          : "right"

    // Open state driven by MainRouter until Commit 5; kept writable for
    // backward compat while `isOpen` (the PanelLayout-reactive version) is wired in.
    property bool open: false

    // Reactive open flag derived from PanelLayout. Drives the slide animation
    // once MainRouter is updated in Commit 5.
    readonly property bool isOpen: (PanelLayout && PanelLayout.openPanels && panelId)
                                   ? PanelLayout.openPanels[edge] === panelId
                                   : false

    property string title: ""
    property string panelIcon: ""
    property int tabIndex: {
        if (!PanelLayout || !PanelLayout.order || !panelId) return 0
        var peers = PanelLayout.order.filter(function(p) {
            return PanelLayout.edges[p] === edge
        })
        var idx = peers.indexOf(panelId)
        return idx >= 0 ? idx : 0
    }
    property var dragOpenKeys: []

    signal toggleRequested()

    default property alias contents: contentArea.data

    implicitWidth: Theme.overlayWidth

    onOpenChanged: {
        if (!open && Window.activeFocusItem instanceof TextInput)
            root.forceActiveFocus()
    }

    EdgeTab {
        id: edgeTab
        anchors.left:  root.edge === "left"  ? parent.left  : undefined
        anchors.right: root.edge === "right" ? parent.right : undefined
        y: (parent.height - height) / 2 + root.tabIndex * (height + 8)
        z: 1
        edge: root.edge
        open: root.open
        icon: root.panelIcon
        onClicked: root.toggleRequested()
    }

    DropArea {
        x: root.edge === "left" ? 0 : (parent.width - edgeTab.width)
        y: edgeTab.y
        width: edgeTab.width
        height: edgeTab.height
        keys: root.dragOpenKeys
        enabled: !root.open && root.dragOpenKeys.length > 0
        z: 2
        onEntered: root.toggleRequested()
    }

    Rectangle {
        id: panel
        width: root.implicitWidth
        height: parent.height
        x: root.open ? 0 : (root.edge === "left" ? -width : width)
        color: Theme.background
        clip: true

        Behavior on x { NumberAnimation { duration: 200; easing.type: Easing.InOutQuad } }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onWheel: (wheel) => wheel.accepted = true
            onPressed: {
                if (Window.activeFocusItem instanceof TextInput)
                    root.forceActiveFocus()
            }
        }

        // This DragHandler (target: null) wins the exclusive grab over tile
        // DragHandlers when the cursor is over the open panel, preventing tiles
        // behind the panel from being accidentally dragged.
        DragHandler {
            target: null
            grabPermissions: PointerHandler.CanTakeOverFromHandlersOfSameType |
                             PointerHandler.CanTakeOverFromHandlersOfDifferentType
        }

        Item {
            id: header
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: root.title !== "" ? 48 : 0
            visible: root.title !== ""

            Text {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                text: root.title
                font.pixelSize: Theme.fontSizeMd
                font.weight: Font.Medium
                color: Theme.text
            }
        }

        Rectangle {
            id: divider
            objectName: "divider"
            anchors { top: header.bottom; left: parent.left; right: parent.right }
            height: root.title !== "" ? 1 : 0
            color: Theme.border
        }

        Item {
            id: contentArea
            anchors {
                top: divider.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
        }
    }
}
