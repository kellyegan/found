import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property string text: ""
    property string variant: "default"  // "default" | "icon"
    property bool hovered: false
    property bool pressed: false

    signal clicked()

    implicitWidth: label.implicitWidth + Theme.spacingMd * 2
    implicitHeight: label.implicitHeight + Theme.spacingSm * 2

    radius: root.variant === "icon" ? height / 2 : 4
    border.width: root.variant === "icon" ? 0 : 1
    border.color: Theme.border

    color: {
        if (root.variant === "icon") return root.hovered ? Theme.border : "transparent"
        if (root.pressed) return Theme.border
        if (root.hovered) return Theme.accent
        return Theme.surface
    }

    AppText {
        id: label
        objectName: "label"
        anchors.centerIn: parent
        text: root.text
        variant: (root.variant === "icon" || !root.enabled) ? "muted" : "default"
    }

    HoverHandler {
        target: root
        enabled: root.enabled
        cursorShape: Qt.PointingHandCursor
        onHoveredChanged: root.hovered = hovered
    }

    TapHandler {
        target: root
        enabled: root.enabled
        onPressedChanged: root.pressed = pressed
        onTapped: root.clicked()
    }
}
