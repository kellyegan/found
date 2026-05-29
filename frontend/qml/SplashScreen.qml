import QtQuick

Item {
    id: root

    property string statusText: ""
    property bool hasError: false

    Rectangle {
        anchors.fill: parent
        color: Theme.background
    }

    // Title — centered
    Text {
        anchors.centerIn: parent
        text: "FOUND"
        font.pixelSize: 96
        font.weight: Font.Bold
        font.family: Theme.fontFamily
        color: Theme.text
        font.letterSpacing: 12
    }

    // Bottom row: version | status | license
    Item {
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            margins: Theme.spacingXl
        }
        height: 20

        Text {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            text: "Version " + Qt.application.version
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            color: Theme.textMuted
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            text: root.statusText
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            color: root.hasError ? "#ff4444" : Theme.textMuted
            visible: root.statusText.length > 0
        }

        Text {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            text: "© 2025 Found"
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            color: Theme.textMuted
        }
    }
}
