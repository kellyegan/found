import QtQuick
import "../components"

Item {
    id: root

    property string loadingState: "Loading"
    property var gridModel: null
    property bool leftPanelOpen: false
    property bool rightPanelOpen: false

    signal loadMoreRequested()
    signal removeImagesRequested(var imageIds)
    signal locateRequested(string imageId)

    function scrollToX(x) { pane.scrollToX(x) }
    function scrollToActiveImage() { pane.scrollToActiveImage() }

    ImageGridPane {
        id: pane
        anchors.fill: parent
        loadingState: root.loadingState
        gridModel: root.gridModel
        leftPanelOpen: root.leftPanelOpen
        rightPanelOpen: root.rightPanelOpen
        emptyStateText: "NO IMAGES YET"
        emptyStateSubtext: "DRAG AND DROP HERE TO ADD"
        removeContextLabel: "the library"

        onLoadMoreRequested: root.loadMoreRequested()
        onRemoveImagesRequested: function(imageIds, _) { root.removeImagesRequested(imageIds) }
        onLocateRequested: function(imageId) { root.locateRequested(imageId) }
        onScrollXChanged: function(x) { NavigationManager.updateScrollX(x) }
    }
}
