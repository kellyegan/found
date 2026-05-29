import QtQuick

Item {
    id: root

    property bool canGoBack: false
    property string viewTitle: ""
    property bool sidebarOpen: false

    signal goBackRequested()
    signal sidebarToggleRequested()

    // Back button — left side
    Item {
        id: backBtn
        width: visible ? 44 : 0
        height: parent.height
        visible: root.canGoBack

        Text {
            anchors.centerIn: parent
            text: "‹"
            font.pixelSize: 24
            color: Theme.text
        }

        MouseArea {
            anchors.fill: parent
            onClicked: root.goBackRequested()
        }
    }

    // View title
    Text {
        anchors {
            left: backBtn.right
            leftMargin: Theme.spacingMd
            verticalCenter: parent.verticalCenter
        }
        text: root.viewTitle
        font.pixelSize: Theme.fontSizeMd
        font.family: Theme.fontFamily
        font.weight: Font.Medium
        color: Theme.text
    }

    // Collections sidebar toggle — right side
    Item {
        id: sidebarBtn
        width: 44
        height: parent.height
        anchors.right: parent.right

        Text {
            anchors.centerIn: parent
            text: "☰"
            font.pixelSize: 16
            color: root.sidebarOpen ? "#88cc88" : Theme.text
        }

        MouseArea {
            anchors.fill: parent
            onClicked: root.sidebarToggleRequested()
        }
    }
}
