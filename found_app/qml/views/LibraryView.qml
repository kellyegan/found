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
    signal removeImagesRequested(var imageIds)

    // Pending removal — drives the confirmation dialog below
    property var _removeIds: []
    property string _removeMessage: ""

    function _pluralize(count, noun) {
        return count + " " + noun + (count === 1 ? "" : "s")
    }

    function _requestRemoval(ids, message) {
        root._removeIds = ids
        root._removeMessage = message
    }

    function _clearRemoval() {
        root._removeIds = []
        root._removeMessage = ""
    }

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

    Shortcut {
        sequences: [StandardKey.Delete, "Backspace"]
        enabled: root.visible && !(Window.activeFocusItem instanceof TextInput)
        onActivated: {
            var ids = SelectionManager.selectedIds
            if (ids.length === 0) return
            root._requestRemoval(
                ids,
                "Are you sure you want to remove " + root._pluralize(ids.length, "selected item") + " from library?"
            )
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
        spacing: Theme.spacingSm

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "NO IMAGES YET"
            font.pixelSize: Theme.fontSizeLg
            font.weight: Font.DemiBold
            font.family: Theme.fontFamily
            color: Theme.textMuted
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
        onRemoveRequested: function(imageId, filename) {
            root._requestRemoval([imageId], "Are you sure you want to remove " + filename + " from the library?")
        }
    }

    function scrollToX(x) {
        thumbnailGrid.scrollToX(x)
    }

    ConfirmDialog {
        id: removeDialog
        anchors.fill: parent
        z: 50
        open: root._removeIds.length > 0
        message: root._removeMessage
        onConfirmed: {
            root.removeImagesRequested(root._removeIds)
            SelectionManager.clear()
            root._clearRemoval()
        }
        onCancelled: root._clearRemoval()
    }

    // Error
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Error"
        text: "Failed to load library."
        font.pixelSize: Theme.fontSizeMd
        font.family: Theme.fontFamily
        color: Theme.warningColor
    }
}
