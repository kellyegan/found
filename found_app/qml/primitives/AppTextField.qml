import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property alias text: input.text
    property string placeholderText: ""
    property bool focused: false
    property bool error: false
    property alias borderColor: root.border.color

    property string leadingIcon: ""
    property string trailingIcon: "↵"
    property bool trailingVisible: false
    property bool pill: false

    property real fontSize: Theme.fontSizeSm
    property int fontCapitalization: Font.MixedCase
    property color backgroundColor: Theme.surface

    signal submitted()
    signal escaped()

    function forceActiveFocus() { input.forceActiveFocus() }
    function blur() { input.focus = false }

    implicitWidth: 160
    implicitHeight: input.implicitHeight + Theme.spacingSm * 2
    radius: pill ? height / 2 : 1
    color: root.focused ? Theme.surface : root.backgroundColor
    border.width: 1
    border.color: {
        if (root.error) return Theme.warning
        if (root.focused) return Theme.accent
        return Theme.border
    }

    Text {
        id: leadingIconItem
        objectName: "leadingIconItem"
        visible: root.leadingIcon !== ""
        anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
        text: root.leadingIcon
        font.pixelSize: root.fontSize
        color: Theme.textMuted
    }

    Rectangle {
        id: trailingBtn
        objectName: "trailingBtn"
        visible: root.trailingVisible
        anchors { right: parent.right; rightMargin: 3; verticalCenter: parent.verticalCenter }
        width: 20; height: 20; radius: 10
        color: trailingArea.containsMouse ? Theme.border : "transparent"

        Text {
            objectName: "submitIcon"
            anchors.centerIn: parent
            text: root.trailingIcon
            font.pixelSize: root.fontSize
            color: Theme.success
        }

        MouseArea {
            id: trailingArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.submitted()
        }
    }

    TextInput {
        id: input
        objectName: "input"
        anchors {
            left: leadingIconItem.visible ? leadingIconItem.right : parent.left
            leftMargin: leadingIconItem.visible ? 4 : Theme.spacingSm
            right: trailingBtn.visible ? trailingBtn.left : parent.right
            rightMargin: trailingBtn.visible ? 2 : Theme.spacingSm
            verticalCenter: parent.verticalCenter
        }
        color: root.error ? Theme.warning : Theme.text
        font.family: Theme.fontFamily
        font.pixelSize: root.fontSize
        font.capitalization: root.fontCapitalization
        clip: true
        onActiveFocusChanged: root.focused = activeFocus

        Keys.priority: Keys.BeforeItem
        Keys.onReturnPressed: function(e) { e.accepted = true; root.submitted() }
        Keys.onEnterPressed:  function(e) { e.accepted = true; root.submitted() }
        Keys.onEscapePressed: function(e) { e.accepted = true; root.escaped() }

        Text {
            anchors.fill: parent
            visible: input.text.length === 0
            text: root.placeholderText
            color: Theme.textMuted
            font.family: Theme.fontFamily
            font.pixelSize: root.fontSize
            font.capitalization: root.fontCapitalization
        }
    }
}
