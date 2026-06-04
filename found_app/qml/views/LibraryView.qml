import QtQuick
import QtQuick.Window
import "../components"

Item {
    id: root

    property string loadingState: "Loading"
    property var gridModel: null
    property bool leftPanelOpen: false
    property bool rightPanelOpen: false

    signal loadMoreRequested()

    // Keyboard shortcuts — scoped to this view via root.visible
    Shortcut {
        sequence: "Escape"
        enabled: root.visible
        onActivated: SelectionManager.clear()
    }

    Shortcut {
        sequence: StandardKey.SelectAll
        enabled: root.visible
        onActivated: {
            if (root.loadingState === "Ready" && root.gridModel)
                SelectionManager.selectAll(root.gridModel.allIds)
        }
    }

    Shortcut {
        sequence: "Space"
        enabled: root.visible && !(Window.activeFocusItem instanceof TextInput)
        onActivated: {
            if (SelectionManager.primaryId !== "")
                SelectionManager.requestOpen(SelectionManager.primaryId)
        }
    }

    // Loading
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Loading"
        text: "Loading…"
        font.pixelSize: Theme.fontSizeMd
        font.family: Theme.fontFamily
        color: Theme.textMuted
    }

    // Empty library
    Column {
        anchors.centerIn: parent
        visible: root.loadingState === "Empty"
        spacing: Theme.spacingMd

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "NO IMAGES YET"
            font.pixelSize: Theme.fontSizeLg
            font.weight: Font.Bold
            font.family: Theme.fontFamily
            color: Theme.text
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "DRAG AND DROP HERE TO ADD"
            font.pixelSize: Theme.fontSizeMd
            font.family: Theme.fontFamily
            color: Theme.textMuted
        }
    }

    // Thumbnail grid
    ThumbnailGrid {
        id: thumbnailGrid
        anchors { top: parent.top; left: parent.left; right: parent.right; bottom: parent.bottom }
        visible: root.loadingState === "Ready"
        model: root.gridModel
        leftPanelOpen: root.leftPanelOpen
        rightPanelOpen: root.rightPanelOpen
        onLoadMoreRequested: root.loadMoreRequested()
        onScrollXChanged: function(x) { NavigationManager.updateScrollX(x) }
    }

    function scrollToX(x) {
        thumbnailGrid.scrollToX(x)
    }

    // Error
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Error"
        text: "Failed to load library."
        font.pixelSize: Theme.fontSizeMd
        font.family: Theme.fontFamily
        color: "#ff4444"
    }
}
