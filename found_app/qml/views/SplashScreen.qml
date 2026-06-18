import QtQuick
import Found.Theme 1.0

Item {
    id: root

    property string statusText: ""
    property bool hasError: false
    property string appVersion: ""
    property string appLicense: ""
    property bool isReady: false
    property bool isDismissed: false

    signal dismissed()
    onDismissed: isDismissed = true

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
        anchors.verticalCenterOffset: parent.height * 0.04

        Text {
            id: titleText
            objectName: "titleText"
            width: parent.width
            anchors.centerIn: parent
            text: "found"
            font.pixelSize: Theme.fontSizeXl * 8
            minimumPixelSize: Theme.fontSizeXl
            fontSizeMode: Text.HorizontalFit
            font.weight: Font.Bold
            font.family: Theme.fontFamily
            color: Theme.text
            font.letterSpacing: 12
            font.capitalization: Font.AllUppercase
            renderType: Text.NativeRendering
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
            anchors.leftMargin: 20 + (parent.width - titleBlock.width) / 2
            anchors.verticalCenter: parent.verticalCenter
            text: root.appVersion.length > 0 ? "Version " + root.appVersion : ""
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            font.weight: Font.Medium
            color: Theme.textMuted
            visible: root.appVersion.length > 0
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            text: root.isReady ? "Click to continue" : root.statusText
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            color: root.hasError ? Theme.warning : Theme.textMuted
            visible: root.isReady || root.statusText.length > 0
        }

        Text {
            anchors.right: parent.right
            anchors.rightMargin: 30 + (parent.width - titleBlock.width) / 2
            anchors.verticalCenter: parent.verticalCenter
            text: root.appLicense.length > 0 ? "©2026 Kelly Egan. " + root.appLicense : ""
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            color: Theme.textMuted
            visible: root.appLicense.length > 0
        }
    }
}
