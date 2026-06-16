import QtQuick
import Found.Theme 1.0

Item {
    id: root

    property bool open: false
    property string message: ""
    property string confirmLabel: "Confirm"
    property string cancelLabel: "Cancel"
    property bool showCancel: true
    property string checkboxLabel: ""
    property bool checkboxChecked: false

    signal confirmed()
    signal cancelled()

    visible: root.open

    // Backdrop — absorbs clicks so content beneath isn't interactive
    Rectangle {
        objectName: "backdrop"
        anchors.fill: parent
        color: Theme.background
        opacity: 0.55

        MouseArea {
            anchors.fill: parent
        }
    }

    // Centered modal sheet
    Rectangle {
        id: sheet
        objectName: "sheet"
        anchors.centerIn: parent
        width: Math.min((root.parent ? root.parent.width : 420) - 80, 380)
        height: contentCol.implicitHeight + 48
        color: Theme.surface
        radius: 10

        focus: root.open
        Keys.onEscapePressed: root.cancelled()
        Keys.onReturnPressed: root.confirmed()
        Keys.onEnterPressed: root.confirmed()

        // Absorb clicks on the sheet itself so they don't fall through to the
        // backdrop. Button/checkbox MouseAreas inside contentCol are declared
        // after this and so take priority.
        MouseArea {
            anchors.fill: parent
        }

        Column {
            id: contentCol
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: Theme.spacingLg }
            spacing: 18

            Text {
                objectName: "messageText"
                width: parent.width
                text: root.message
                color: Theme.text
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
                wrapMode: Text.WordWrap
            }

            Item {
                width: parent.width
                height: checkboxRow.implicitHeight
                visible: root.checkboxLabel !== ""

                Row {
                    id: checkboxRow
                    spacing: 8

                    Rectangle {
                        id: checkboxBox
                        objectName: "checkboxBox"
                        property alias borderColor: checkboxBox.border.color
                        width: 16
                        height: 16
                        radius: 3
                        y: (parent.height - height) / 2
                        color: root.checkboxChecked ? Theme.accent : "transparent"
                        border.color: root.checkboxChecked ? Theme.accent : Theme.textMuted
                        border.width: 1

                        Text {
                            objectName: "checkmarkText"
                            anchors.centerIn: parent
                            visible: root.checkboxChecked
                            text: "✓"
                            color: Theme.background
                            font.pixelSize: Theme.fontSizeSm
                        }
                    }

                    Text {
                        objectName: "checkboxLabelText"
                        text: root.checkboxLabel
                        color: Theme.textMuted
                        font.pixelSize: Theme.fontSizeSm
                        font.family: Theme.fontFamily
                        y: (parent.height - height) / 2
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: root.checkboxChecked = !root.checkboxChecked
                }
            }

            Row {
                anchors.right: parent.right
                spacing: 10

                Rectangle {
                    id: cancelBtn
                    objectName: "cancelBtn"
                    property alias borderColor: cancelBtn.border.color
                    width: 80
                    height: 32
                    radius: 4
                    color: cancelArea.containsMouse ? Theme.border : "transparent"
                    border.color: Theme.border
                    border.width: 1
                    visible: root.showCancel

                    Text {
                        objectName: "cancelLabelText"
                        anchors.centerIn: parent
                        text: root.cancelLabel
                        color: Theme.textMuted
                        font.pixelSize: Theme.fontSizeSm
                        font.family: Theme.fontFamily
                    }

                    MouseArea {
                        id: cancelArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.cancelled()
                    }
                }

                Rectangle {
                    id: confirmBtn
                    objectName: "confirmBtn"
                    property alias borderColor: confirmBtn.border.color
                    width: 80
                    height: 32
                    radius: 4
                    color: Qt.tint(Theme.surface, Qt.rgba(1, 0, 0, confirmArea.containsMouse ? 0.35 : 0.25))
                    border.color: Theme.warning
                    border.width: 1

                    Text {
                        objectName: "confirmLabelText"
                        anchors.centerIn: parent
                        text: root.confirmLabel
                        color: Theme.warning
                        font.pixelSize: Theme.fontSizeSm
                        font.family: Theme.fontFamily
                        font.weight: Font.Medium
                    }

                    MouseArea {
                        id: confirmArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.confirmed()
                    }
                }
            }
        }

        onVisibleChanged: if (visible) forceActiveFocus()
    }
}
