import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property string edge: "right"   // "left" | "right"
    property bool open: false
    property string icon: ""        // identifying glyph set by the owning panel
    property string tooltip: ""     // reserved — wire up ToolTip when needed

    signal clicked()

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

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
