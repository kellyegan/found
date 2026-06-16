import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property string chipState: "off"
    property alias borderColor: root.border.color
    property string text: ""
    property bool removable: false

    signal removeRequested()

    implicitWidth: root.text.length > 0 ? (_chipLabel.implicitWidth + (root.removable ? 28 : 20)) : 0
    implicitHeight: root.text.length > 0 ? 22 : 0

    radius: height / 2
    border.width: 1

    color: {
        switch (root.chipState) {
        case "include":    return Theme.accent
        case "exclude":    return Theme.warning
        case "mixed":      return Theme.surface
        case "drag-hover": return Theme.accent
        case "assigned":   return Theme.surface
        default:           return Theme.border
        }
    }
    border.color: root.chipState === "assigned" ? Theme.border : root.color

    Text {
        id: _chipLabel
        visible: root.text.length > 0
        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
        text: root.text
        font.pixelSize: Theme.fontSizeSm
        font.family: Theme.fontFamily
        color: Theme.text
    }

    Text {
        visible: root.removable
        anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
        text: "×"
        font.pixelSize: Theme.fontSizeSm
        color: _removeArea.containsMouse ? Theme.text : Theme.textMuted

        MouseArea {
            id: _removeArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.removeRequested()
        }
    }
}
