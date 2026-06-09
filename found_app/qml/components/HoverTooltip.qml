import QtQuick

Item {
    id: root

    property string text: ""

    width: label.implicitWidth + 16
    height: label.implicitHeight + 8

    Rectangle {
        anchors.fill: parent
        color: "#2a2a2a"
        border.color: "#444444"
        border.width: 1
        radius: 4

        Text {
            id: label
            anchors.centerIn: parent
            text: root.text
            color: "#cccccc"
            font.pixelSize: 11
            font.family: Theme.fontFamily
        }
    }
}
