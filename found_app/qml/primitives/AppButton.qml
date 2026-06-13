import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property string text: ""
    property bool hovered: false

    implicitWidth: label.implicitWidth + Theme.spacingMd * 2
    implicitHeight: label.implicitHeight + Theme.spacingSm * 2
    radius: 4
    border.width: 1
    border.color: Theme.border

    color: root.hovered ? Theme.accent : Theme.surface

    AppText {
        id: label
        objectName: "label"
        anchors.centerIn: parent
        text: root.text
    }

    HoverHandler {
        target: root
        onHoveredChanged: root.hovered = hovered
    }
}
