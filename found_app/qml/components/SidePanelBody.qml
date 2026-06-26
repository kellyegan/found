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

    // Open/close animates; edge changes snap instantly (no cross-edge transition).
    states: [
        State { name: "openLeft";   when: root.open && root.edge === "left"
                PropertyChanges { target: panel; x: 0 } },
        State { name: "closedLeft"; when: !root.open && root.edge === "left"
                PropertyChanges { target: panel; x: -panel.width } },
        State { name: "openRight";  when: root.open && root.edge === "right"
                PropertyChanges { target: panel; x: 0 } },
        State { name: "closedRight"; when: !root.open && root.edge === "right"
                PropertyChanges { target: panel; x: panel.width } }
    ]
    transitions: [
        Transition { from: "openLeft";    to: "closedLeft"
                     NumberAnimation { target: panel; property: "x"; duration: 200; easing.type: Easing.InOutQuad } },
        Transition { from: "closedLeft";  to: "openLeft"
                     NumberAnimation { target: panel; property: "x"; duration: 200; easing.type: Easing.InOutQuad } },
        Transition { from: "openRight";   to: "closedRight"
                     NumberAnimation { target: panel; property: "x"; duration: 200; easing.type: Easing.InOutQuad } },
        Transition { from: "closedRight"; to: "openRight"
                     NumberAnimation { target: panel; property: "x"; duration: 200; easing.type: Easing.InOutQuad } }
    ]

    Rectangle {
        id: panel
        width: root.implicitWidth
        height: parent.height
        color: Theme.background
        clip: true

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
