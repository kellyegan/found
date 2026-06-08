import QtQuick
import QtQuick.Window
import "../components"

Item {
    id: root

    property string collectionName: ""
    property var gridModel: null
    property string loadingState: "Idle"
    property bool leftPanelOpen: false
    property bool rightPanelOpen: false

    signal loadMoreRequested()
    signal removeImagesRequested(var imageIds, bool alsoFromLibrary)

    // Pending removal — drives the confirmation dialog below
    property var _removeIds: []
    property string _removeMessage: ""

    function _pluralize(count, noun) {
        return count + " " + noun + (count === 1 ? "" : "s")
    }

    function _requestRemoval(ids, message) {
        root._removeIds = ids
        root._removeMessage = message
        removeDialog.checkboxChecked = false
    }

    function _clearRemoval() {
        root._removeIds = []
        root._removeMessage = ""
        removeDialog.checkboxChecked = false
    }

    Shortcut {
        sequence: "Up"
        enabled: root.visible && !(Window.activeFocusItem instanceof TextInput)
        onActivated: if (root.loadingState === "Ready") thumbnailGrid.navigateActive("up")
    }

    Shortcut {
        sequence: "Down"
        enabled: root.visible && !(Window.activeFocusItem instanceof TextInput)
        onActivated: if (root.loadingState === "Ready") thumbnailGrid.navigateActive("down")
    }

    Shortcut {
        sequence: "Left"
        enabled: root.visible && !(Window.activeFocusItem instanceof TextInput)
        onActivated: if (root.loadingState === "Ready") thumbnailGrid.navigateActive("left")
    }

    Shortcut {
        sequence: "Right"
        enabled: root.visible && !(Window.activeFocusItem instanceof TextInput)
        onActivated: if (root.loadingState === "Ready") thumbnailGrid.navigateActive("right")
    }

    Shortcut {
        sequences: [StandardKey.Delete, "Backspace"]
        enabled: root.visible && !(Window.activeFocusItem instanceof TextInput)
        onActivated: {
            var ids = SelectionManager.selectedIds
            if (ids.length === 0) return
            root._requestRemoval(
                ids,
                "Are you sure you want to remove " + root._pluralize(ids.length, "selected item") + " from this collection?"
            )
        }
    }

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
        id: thumbnailGrid
        anchors.fill: parent
        visible: root.loadingState === "Ready"
        model: root.gridModel
        leftPanelOpen: root.leftPanelOpen
        rightPanelOpen: root.rightPanelOpen
        onLoadMoreRequested: root.loadMoreRequested()
        onRemoveRequested: function(imageId, filename) {
            root._requestRemoval([imageId], "Are you sure you want to remove " + filename + " from this collection?")
        }
    }

    ConfirmDialog {
        id: removeDialog
        anchors.fill: parent
        z: 50
        open: root._removeIds.length > 0
        message: root._removeMessage
        checkboxLabel: "Also remove from library"
        onConfirmed: {
            root.removeImagesRequested(root._removeIds, removeDialog.checkboxChecked)
            SelectionManager.clear()
            root._clearRemoval()
        }
        onCancelled: root._clearRemoval()
    }
}
