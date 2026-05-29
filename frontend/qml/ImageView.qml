import QtQuick

Item {
    id: root

    property string imageId: ""
    property string imageUrl: ""
    property string filename: ""
    property string fileStatus: "available"
    property bool hasNext: false
    property bool hasPrev: false

    // Arrow key navigation — Left/Right advance through context
    Shortcut {
        sequence: "Right"
        onActivated: if (root.hasNext) NavigationManager.goNext()
    }

    Shortcut {
        sequence: "Left"
        onActivated: if (root.hasPrev) NavigationManager.goPrev()
    }

    Rectangle {
        anchors.fill: parent
        color: "#111111"

        // Loading indicator — shown while image is in flight
        Item {
            anchors.centerIn: parent
            visible: img.status === Image.Loading && root.imageUrl !== ""

            Text {
                anchors.centerIn: parent
                text: "Loading…"
                color: "#888888"
                font.pixelSize: 14
            }
        }

        // Full-resolution image
        Image {
            id: img
            anchors.fill: parent
            source: root.imageUrl
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            smooth: true
            visible: img.status === Image.Ready
        }

        // Error state — image loaded but render failed
        Item {
            anchors.centerIn: parent
            visible: img.status === Image.Error

            Text {
                anchors.centerIn: parent
                text: "Failed to load image"
                color: "#ff4444"
                font.pixelSize: 14
            }
        }

        // Missing-file overlay
        Item {
            anchors.centerIn: parent
            visible: root.fileStatus === "missing"

            Column {
                anchors.centerIn: parent
                spacing: 8

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "!"
                    color: "#ff8800"
                    font.pixelSize: 48
                    font.weight: Font.Bold
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "File not found"
                    color: "#888888"
                    font.pixelSize: 14
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: root.filename
                    color: "#666666"
                    font.pixelSize: 12
                }
            }
        }
    }
}
