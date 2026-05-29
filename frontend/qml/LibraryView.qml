import QtQuick

Item {
    id: root

    property string loadingState: "Loading"
    property var gridModel: null

    signal loadMoreRequested()

    // Keyboard shortcuts — active application-wide, no focus required
    Shortcut {
        sequence: "Escape"
        onActivated: SelectionManager.clear()
    }

    Shortcut {
        sequence: StandardKey.SelectAll
        onActivated: {
            if (root.loadingState === "Ready" && root.gridModel)
                SelectionManager.selectAll(root.gridModel.allIds)
        }
    }

    Shortcut {
        sequence: "Return"
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
        anchors.fill: parent
        visible: root.loadingState === "Ready"
        model: root.gridModel
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
