import QtQuick
import "../components"

Item {
    id: root

    property string collectionName: ""
    property var gridModel: null
    property string loadingState: "Idle"
    property bool leftPanelOpen: false
    property bool rightPanelOpen: false

    signal loadMoreRequested()

    // Loading state
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Loading"
        text: "Loading…"
        color: Theme.textMuted
        font.pixelSize: Theme.fontSizeMd
    }

    // Empty state
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Empty"
        text: "No images in this collection"
        color: Theme.textMuted
        font.pixelSize: Theme.fontSizeMd
    }

    // Error state
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Error"
        text: "Failed to load collection"
        color: Theme.warningColor
        font.pixelSize: Theme.fontSizeMd
    }

    // Image grid
    ThumbnailGrid {
        anchors.fill: parent
        visible: root.loadingState === "Ready"
        model: root.gridModel
        leftPanelOpen: root.leftPanelOpen
        rightPanelOpen: root.rightPanelOpen
        onLoadMoreRequested: root.loadMoreRequested()
    }
}
