import QtQuick
import QtQuick.Window

Item {
    id: root

    property string loadingState: "Loading"
    property var gridModel: null
    property bool leftPanelOpen: false
    property bool rightPanelOpen: false
    property string emptyStateText: "No images"
    property string emptyStateSubtext: ""
    property string noResultsText: "NO IMAGES FOUND"
    property string noResultsSubtext: ""
    property string removeContextLabel: "the library"
    property string removeCheckboxLabel: ""

    signal loadMoreRequested()
    signal removeImagesRequested(var imageIds, bool alsoFromLibrary)
    signal scrollXChanged(real x)
    signal locateRequested(string imageId)
    signal viewportVerifyRequested(var imageIds)

    property var _removeIds: []
    property string _removeMessage: ""

    // While the remove-confirmation dialog is open, selection, dragging,
    // and keyboard shortcuts on the grid behind it must be blocked.
    readonly property bool _dialogOpen: root._removeIds.length > 0

    // Window.activeFocusItem is an attached property that requires its
    // attachee to derive from Item — read it here (root is an Item) rather
    // than inside the Shortcuts below (non-Item QQuickShortcut objects).
    readonly property bool _focusIsTextInput: Window.activeFocusItem instanceof TextInput

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

    function scrollToX(x) {
        thumbnailGrid.scrollToX(x)
    }

    function scrollToActiveImage() {
        var ids = root.gridModel ? root.gridModel.allIds : []
        thumbnailGrid.scrollToIndexAnimated(ids.indexOf(SelectionManager.primaryId))
    }

    Shortcut {
        sequence: "Escape"
        enabled: root.visible && !root._dialogOpen
        onActivated: SelectionManager.clear()
    }

    Shortcut {
        sequence: StandardKey.SelectAll
        enabled: root.visible && !root._dialogOpen
        onActivated: {
            if (root.loadingState === "Ready" && root.gridModel)
                SelectionManager.selectAll(root.gridModel.allIds)
        }
    }

    Shortcut {
        sequence: "Space"
        enabled: root.visible && !root._dialogOpen && !root._focusIsTextInput
        onActivated: {
            if (SelectionManager.primaryId !== "")
                SelectionManager.requestOpen(SelectionManager.primaryId)
        }
    }

    Shortcut {
        sequence: "Up"
        enabled: root.visible && !root._dialogOpen && !root._focusIsTextInput
        onActivated: if (root.loadingState === "Ready") thumbnailGrid.navigateActive("up")
    }

    Shortcut {
        sequence: "Down"
        enabled: root.visible && !root._dialogOpen && !root._focusIsTextInput
        onActivated: if (root.loadingState === "Ready") thumbnailGrid.navigateActive("down")
    }

    Shortcut {
        sequence: "Left"
        enabled: root.visible && !root._dialogOpen && !root._focusIsTextInput
        onActivated: if (root.loadingState === "Ready") thumbnailGrid.navigateActive("left")
    }

    Shortcut {
        sequence: "Right"
        enabled: root.visible && !root._dialogOpen && !root._focusIsTextInput
        onActivated: if (root.loadingState === "Ready") thumbnailGrid.navigateActive("right")
    }

    Shortcut {
        sequences: [StandardKey.Delete, "Backspace"]
        enabled: root.visible && !root._dialogOpen && !root._focusIsTextInput
        onActivated: {
            var ids = SelectionManager.selectedIds
            if (ids.length === 0) return
            root._requestRemoval(
                ids,
                "Are you sure you want to remove "
                    + root._pluralize(ids.length, "selected item")
                    + " from " + root.removeContextLabel + "?"
            )
        }
    }

    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Loading"
        text: "Loading…"
        font.pixelSize: Theme.fontSizeMd
        font.family: Theme.fontFamily
        color: Theme.textMuted
    }

    Column {
        anchors.centerIn: parent
        visible: root.loadingState === "Empty" || root.loadingState === "NoResults"
        spacing: Theme.spacingSm

        readonly property bool isNoResults: root.loadingState === "NoResults"

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: parent.isNoResults ? root.noResultsText : root.emptyStateText
            font.pixelSize: Theme.fontSizeLg
            font.weight: Font.DemiBold
            font.family: Theme.fontFamily
            color: Theme.textMuted
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            readonly property string subtext: parent.isNoResults ? root.noResultsSubtext : root.emptyStateSubtext
            visible: subtext !== ""
            text: subtext
            font.pixelSize: Theme.fontSizeMd
            font.family: Theme.fontFamily
            color: Theme.textMuted
        }
    }

    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Error"
        text: "Failed to load."
        font.pixelSize: Theme.fontSizeMd
        font.family: Theme.fontFamily
        color: Theme.warningColor
    }

    ThumbnailGrid {
        id: thumbnailGrid
        objectName: "thumbnailGrid"
        anchors { top: parent.top; left: parent.left; right: parent.right; bottom: parent.bottom }
        visible: root.loadingState === "Ready"
        enabled: !root._dialogOpen
        model: root.gridModel
        leftPanelOpen: root.leftPanelOpen
        rightPanelOpen: root.rightPanelOpen
        onLoadMoreRequested: root.loadMoreRequested()
        onScrollXChanged: { root.scrollXChanged(thumbnailGrid.scrollX) }
        onLocateRequested: function(imageId) { root.locateRequested(imageId) }
        onViewportVerifyRequested: function(imageIds) { root.viewportVerifyRequested(imageIds) }
        onRemoveRequested: function(imageId, filename) {
            root._requestRemoval(
                [imageId],
                "Are you sure you want to remove " + filename + " from " + root.removeContextLabel + "?"
            )
        }
    }

    ConfirmDialog {
        id: removeDialog
        anchors.fill: parent
        z: 50
        open: root._removeIds.length > 0
        message: root._removeMessage
        checkboxLabel: root.removeCheckboxLabel
        onConfirmed: {
            root.removeImagesRequested(root._removeIds, removeDialog.checkboxChecked)
            SelectionManager.clear()
            root._clearRemoval()
        }
        onCancelled: root._clearRemoval()
    }
}
