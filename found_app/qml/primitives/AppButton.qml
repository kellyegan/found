import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property string text: ""
    property bool hovered: false
    property bool pressed: false

    signal clicked()

    implicitWidth: label.implicitWidth + Theme.spacingMd * 2
    implicitHeight: label.implicitHeight + Theme.spacingSm * 2
    radius: 4
    border.width: 1
    border.color: Theme.border

    color: {
        if (root.pressed) return Theme.border
        if (root.hovered) return Theme.accent
        return Theme.surface
    }

    AppText {
        id: label
        objectName: "label"
        anchors.centerIn: parent
        text: root.text
        variant: root.enabled ? "default" : "muted"
    }

    HoverHandler {
        target: root
        enabled: root.enabled
        onHoveredChanged: root.hovered = hovered
    }

    TapHandler {
        target: root
        enabled: root.enabled
        onPressedChanged: root.pressed = pressed
        onTapped: root.clicked()
    }
}
