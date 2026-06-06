import QtQuick

Item {
    id: root

    property string edge: "right"      // "left" | "right"
    property bool open: false
    property string title: ""
    property string panelIcon: ""      // passed through to EdgeTab
    property int tabIndex: 0           // vertical slot index for stacking tabs on the same edge

    signal toggleRequested()

    default property alias contents: contentArea.data

    implicitWidth: Theme.overlayWidth

    onOpenChanged: {
        if (!open && Window.activeFocusItem instanceof TextInput)
            root.forceActiveFocus()
    }

    // Edge tab — pinned to the window edge (left panel → left edge; right panel → right edge)
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

    // Slide-in panel
    Rectangle {
        id: panel
        width: root.implicitWidth
        height: parent.height
        x: root.open ? 0 : (root.edge === "left" ? -width : width)
        color: Theme.background
        clip: true

        Behavior on x { NumberAnimation { duration: 200; easing.type: Easing.InOutQuad } }

        // Blocks clicks from reaching content behind the panel and clears TextInput focus
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onPressed: {
                if (Window.activeFocusItem instanceof TextInput)
                    root.forceActiveFocus()
            }
        }

        // Optional header
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
            anchors { top: header.bottom; left: parent.left; right: parent.right }
            height: root.title !== "" ? 1 : 0
            color: "#2a2a2a"
        }

        // Content slot — children of the extending component land here
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
