import QtQuick

Item {
    id: root

    property bool open: false

    // Metadata properties — bound from MetadataState in MainRouter
    property string metaLoadingState: "Idle"
    property string metaFilename: ""
    property string metaPath: ""
    property string metaDimensions: ""
    property int metaFileSize: 0
    property string metaDateAdded: ""
    property bool metaIsMissing: false

    signal toggleRequested()

    implicitWidth: 260

    function _formatSize(bytes) {
        if (bytes <= 0) return "—"
        if (bytes < 1024) return bytes + " B"
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB"
        return (bytes / 1048576).toFixed(1) + " MB"
    }

    function _formatDate(isoDate) {
        if (!isoDate) return "—"
        return isoDate.substring(0, 10)
    }

    // ── Slide-in panel ───────────────────────────────────────────────────────
    Rectangle {
        id: panel
        width: root.implicitWidth
        height: parent.height
        x: root.open ? 0 : root.implicitWidth
        color: "#1a1a1a"
        clip: true

        Behavior on x { NumberAnimation { duration: 200; easing.type: Easing.InOutQuad } }

        // Header
        Item {
            id: header
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: 48

            Text {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                text: "Info"
                font.pixelSize: 14
                font.weight: Font.Medium
                color: "#ffffff"
            }
        }

        // Divider
        Rectangle {
            id: divider
            anchors { top: header.bottom; left: parent.left; right: parent.right }
            height: 1
            color: "#2a2a2a"
        }

        // ── Content area ─────────────────────────────────────────────────────
        Item {
            anchors {
                top: divider.bottom
                left: parent.left; right: parent.right; bottom: parent.bottom
                margins: 16
            }

            // Idle / empty selection
            Text {
                anchors.top: parent.top
                topPadding: 8
                visible: root.metaLoadingState === "Idle"
                text: "Select an image to view its details."
                color: "#555555"
                font.pixelSize: 12
                font.family: Theme.fontFamily
                wrapMode: Text.WordWrap
                width: parent.width
            }

            // Loading
            Text {
                anchors.top: parent.top
                topPadding: 8
                visible: root.metaLoadingState === "Loading"
                text: "Loading…"
                color: "#555555"
                font.pixelSize: 12
                font.family: Theme.fontFamily
            }

            // Error
            Text {
                anchors.top: parent.top
                topPadding: 8
                visible: root.metaLoadingState === "Error"
                text: "Failed to load metadata."
                color: "#ff4444"
                font.pixelSize: 12
                font.family: Theme.fontFamily
            }

            // Fields — only shown when Ready
            Column {
                visible: root.metaLoadingState === "Ready"
                width: parent.width
                spacing: 0

                // Missing badge
                Rectangle {
                    visible: root.metaIsMissing
                    width: parent.width
                    height: 28
                    radius: 4
                    color: "#2a1515"
                    border.color: "#884444"
                    border.width: 1
                    anchors.margins: 0

                    Text {
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: "⚠  File missing"
                        font.pixelSize: 11
                        color: "#cc6666"
                    }

                    Rectangle { height: 8; width: 1; color: "transparent"; visible: true }
                }

                // Spacer after missing badge
                Rectangle {
                    visible: root.metaIsMissing
                    height: 10
                    width: 1
                    color: "transparent"
                }

                // Filename
                MetaRow { label: "Filename"; value: root.metaFilename || "—" }

                // Path — wraps onto multiple lines
                MetaRow { label: "Path"; value: root.metaPath || "—"; wrap: true }

                // Dimensions
                MetaRow { label: "Dimensions"; value: root.metaDimensions || "—" }

                // File size
                MetaRow { label: "Size"; value: root._formatSize(root.metaFileSize) }

                // Date added
                MetaRow { label: "Added"; value: root._formatDate(root.metaDateAdded) }
            }
        }
    }

    // ── Edge tab — always visible, anchored to the panel's left edge ─────────
    Rectangle {
        id: edgeTab
        width: 16
        height: 72
        x: panel.x - width
        y: (parent.height - height) / 2
        color: "#1a1a1a"
        radius: 2
        z: 1

        Text {
            anchors.centerIn: parent
            text: root.open ? "►" : "◄"
            font.pixelSize: 10
            color: "#888888"
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.toggleRequested()
        }
    }

    // ── Inline sub-component: a label/value row ───────────────────────────────
    component MetaRow: Item {
        id: row
        property string label: ""
        property string value: ""
        property bool wrap: false

        width: parent ? parent.width : 0
        height: labelText.implicitHeight + valueText.implicitHeight + 12

        Text {
            id: labelText
            anchors { left: parent.left; top: parent.top; topMargin: 4 }
            text: row.label
            font.pixelSize: 10
            font.family: Theme.fontFamily
            color: "#666666"
            font.capitalization: Font.AllUppercase
            font.letterSpacing: 0.8
        }

        Text {
            id: valueText
            anchors { left: parent.left; right: parent.right; top: labelText.bottom; topMargin: 2 }
            text: row.value
            font.pixelSize: 12
            font.family: Theme.fontFamily
            color: "#cccccc"
            wrapMode: row.wrap ? Text.WrapAnywhere : Text.NoWrap
            maximumLineCount: row.wrap ? 0 : 1
            clip: !row.wrap
        }
    }
}
