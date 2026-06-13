import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property alias text: input.text
    property string placeholderText: ""
    property alias borderColor: root.border.color

    implicitWidth: 160
    implicitHeight: input.implicitHeight + Theme.spacingSm * 2
    radius: 4
    color: Theme.surface
    border.width: 1
    border.color: Theme.border

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
        color: Theme.text
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeMd
        clip: true

        AppText {
            anchors.fill: parent
            visible: input.text.length === 0
            text: root.placeholderText
            variant: "muted"
        }
    }
}
