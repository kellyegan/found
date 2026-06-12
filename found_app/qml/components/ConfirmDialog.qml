import QtQuick

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
        anchors.fill: parent
        color: "#000000"
        opacity: 0.55

        MouseArea {
            anchors.fill: parent
        }
    }

    // Centered modal sheet
    Rectangle {
        id: sheet
        anchors.centerIn: parent
        width: Math.min((root.parent ? root.parent.width : 420) - 80, 380)
        height: contentCol.implicitHeight + 48
        color: "#1c1c1c"
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
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            spacing: 18

            Text {
                width: parent.width
                text: root.message
                color: "#cccccc"
                font.pixelSize: 13
                font.family: Theme.fontFamily
                wrapMode: Text.WordWrap
            }

            Row {
                spacing: 8
                visible: root.checkboxLabel !== ""

                Rectangle {
                    width: 16
                    height: 16
                    radius: 3
                    anchors.verticalCenter: parent.verticalCenter
                    color: root.checkboxChecked ? Theme.accent : "transparent"
                    border.color: root.checkboxChecked ? Theme.accent : "#666666"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        visible: root.checkboxChecked
                        text: "✓"
                        color: "#111111"
                        font.pixelSize: 11
                    }
                }

                Text {
                    text: root.checkboxLabel
                    color: "#aaaaaa"
                    font.pixelSize: 12
                    font.family: Theme.fontFamily
                    anchors.verticalCenter: parent.verticalCenter
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
                    width: 80
                    height: 32
                    radius: 4
                    color: cancelArea.containsMouse ? "#2a2a2a" : "transparent"
                    border.color: "#444444"
                    border.width: 1
                    visible: root.showCancel

                    Text {
                        anchors.centerIn: parent
                        text: root.cancelLabel
                        color: "#888888"
                        font.pixelSize: 13
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
                    width: 80
                    height: 32
                    radius: 4
                    color: confirmArea.containsMouse ? "#7a2a2a" : "#5a1e1e"
                    border.color: "#cc6666"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: root.confirmLabel
                        color: "#ffaaaa"
                        font.pixelSize: 13
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
