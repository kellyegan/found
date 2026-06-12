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
    color: Theme.background
    radius: 2

    Column {
        anchors.centerIn: parent
        spacing: 4

        Text {
            visible: root.icon !== ""
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.icon
            font.pixelSize: 11
            color: "#888888"
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.edge === "right"
                  ? (root.open ? "▶" : "◀")
                  : (root.open ? "◀" : "▶")
            font.pixelSize: 10
            color: "#888888"
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
