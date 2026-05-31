import QtQuick

Item {
    id: root

    property string statusText: ""
    property bool hasError: false
    property string appVersion: ""
    property string appLicense: ""
    property bool isReady: false

    signal dismissed()

    Rectangle {
        anchors.fill: parent
        color: Theme.background
    }

    // Title block — centered, ~80% width
    Item {
        id: titleBlock
        width: parent.width * 0.8
        height: titleText.height
        anchors.centerIn: parent
        anchors.verticalCenterOffset: parent.height * 0.08

        Text {
            id: titleText
            width: parent.width
            anchors.centerIn: parent
            text: "FOUND"
            font.pixelSize: 400
            minimumPixelSize: 48
            fontSizeMode: Text.HorizontalFit
            font.weight: Font.Bold
            font.family: Theme.fontFamily
            color: Theme.text
            font.letterSpacing: 12
        }
    }

    // Full-screen click target — only active when backend is ready
    MouseArea {
        anchors.fill: parent
        enabled: root.isReady
        cursorShape: root.isReady ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: root.dismissed()
    }

    // Bottom row — version | status/ready | license aligned to title block edges
    Item {
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            bottomMargin: 25
        }
        height: 20

        Text {
            anchors.left: parent.left
            anchors.leftMargin: (parent.width - titleBlock.width) / 2
            anchors.verticalCenter: parent.verticalCenter
            text: root.appVersion.length > 0 ? "Version " + root.appVersion : ""
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            color: Theme.textMuted
            visible: root.appVersion.length > 0
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            text: root.isReady ? "Click to continue" : root.statusText
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            color: root.hasError ? "#ff4444" : Theme.textMuted
            visible: root.isReady || root.statusText.length > 0
        }

        Text {
            anchors.right: parent.right
            anchors.rightMargin: (parent.width - titleBlock.width) / 2
            anchors.verticalCenter: parent.verticalCenter
            text: root.appLicense.length > 0 ? "© 2025 Found — " + root.appLicense : ""
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            color: Theme.textMuted
            visible: root.appLicense.length > 0
        }
    }
}
