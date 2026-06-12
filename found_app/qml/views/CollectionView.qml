import QtQuick
import Found.Theme 1.0
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
    signal viewportVerifyRequested(var imageIds)

    function scrollToActiveImage() { pane.scrollToActiveImage() }

    ImageGridPane {
        id: pane
        anchors.fill: parent
        loadingState: root.loadingState
        gridModel: root.gridModel
        leftPanelOpen: root.leftPanelOpen
        rightPanelOpen: root.rightPanelOpen
        emptyStateText: "No images in this collection"
        removeContextLabel: "this collection"
        removeCheckboxLabel: "Also remove from library"

        onLoadMoreRequested: root.loadMoreRequested()
        onRemoveImagesRequested: function(imageIds, alsoFromLibrary) {
            root.removeImagesRequested(imageIds, alsoFromLibrary)
        }
        onViewportVerifyRequested: function(imageIds) { root.viewportVerifyRequested(imageIds) }
    }
}
