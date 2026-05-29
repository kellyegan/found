import QtQuick

Item {
    id: root

    property bool canGoBack: false
    property string viewTitle: ""

    signal goBackRequested()

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
}
