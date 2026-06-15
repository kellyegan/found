import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property alias text: input.text
    property string placeholderText: ""
    property bool focused: false
    property bool error: false
    property alias borderColor: root.border.color

    implicitWidth: 160
    implicitHeight: input.implicitHeight + Theme.spacingSm * 2
    radius: 4
    color: Theme.surface
    border.width: 1
    border.color: {
        if (root.error) return Theme.warning
        if (root.focused) return Theme.accent
        return Theme.border
    }

    TextInput {
        id: input
        objectName: "input"
        anchors {
            left: parent.left
            right: parent.right
            verticalCenter: parent.verticalCenter
            leftMargin: Theme.spacingSm
            rightMargin: Theme.spacingSm
        }
        color: root.error ? Theme.warning : Theme.text
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeMd
        clip: true
        onActiveFocusChanged: root.focused = activeFocus

        AppText {
            anchors.fill: parent
            visible: input.text.length === 0
            text: root.placeholderText
            variant: "muted"
        }
    }
}
