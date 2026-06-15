import QtQuick
import Found.Theme 1.0

Item {
    id: root

    property string text: ""

    width: label.implicitWidth + 16
    height: label.implicitHeight + 8

    Rectangle {
        id: tooltipBg
        objectName: "tooltipBg"
        property alias borderColor: tooltipBg.border.color
        anchors.fill: parent
        color: Theme.surface
        border.color: Theme.border
        border.width: 1
        radius: 4

        Text {
            id: label
            objectName: "tooltipLabel"
            anchors.centerIn: parent
            text: root.text
            color: Theme.text
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
        }
    }
}
