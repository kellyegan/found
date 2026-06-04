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
        color: "#888888"
        font.pixelSize: 14
    }

    // Empty state
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Empty"
        text: "No images in this collection"
        color: "#555555"
        font.pixelSize: 14
    }

    // Error state
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Error"
        text: "Failed to load collection"
        color: "#cc4444"
        font.pixelSize: 14
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
