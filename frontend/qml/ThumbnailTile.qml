import QtQuick

Item {
    id: root

    property string thumbnailUrl: ""
    property string fileStatus: "available"
    property bool selected: false

    Rectangle {
        anchors.fill: parent
        color: Theme.surface

        Image {
            id: img
            anchors.fill: parent
            source: root.thumbnailUrl
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            smooth: true
        }

        // Loading placeholder — visible while thumbnail is in flight or not yet assigned
        Rectangle {
            anchors.fill: parent
            color: Theme.surface
            visible: root.thumbnailUrl === "" || img.status === Image.Loading
        }

        // Failed placeholder — generic dark square when load fails
        Rectangle {
            anchors.fill: parent
            color: "#1e1e1e"
            visible: img.status === Image.Error

            Text {
                anchors.centerIn: parent
                text: "?"
                font.pixelSize: 18
                color: Theme.textMuted
            }
        }

        // Missing-image indicator overlay
        Rectangle {
            anchors.fill: parent
            color: "#000000"
            opacity: 0.45
            visible: root.fileStatus === "missing"

            Text {
                anchors.centerIn: parent
                text: "!"
                font.pixelSize: 16
                font.weight: Font.Bold
                color: "#ff8800"
            }
        }

        // Selection highlight
        Rectangle {
            anchors.fill: parent
            color: Theme.accent
            opacity: 0.30
            visible: root.selected
        }

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.color: Theme.accent
            border.width: root.selected ? 2 : 0
        }
    }
}
