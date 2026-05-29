import QtQuick

Item {
    id: root
    anchors.fill: parent

    property string appState: "Launching"
    property string statusMessage: ""
    property bool hasError: false
    property string libraryLoadingState: "Loading"

    SplashScreen {
        anchors.fill: parent
        visible: root.appState !== "Ready"
        statusText: root.statusMessage
        hasError: root.hasError
    }

    // Ready state — navigation bar + view router
    Item {
        anchors.fill: parent
        visible: root.appState === "Ready"

        NavigationBar {
            id: navBar
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: NavigationManager.immersiveMode ? 0 : 48
            visible: !NavigationManager.immersiveMode
            canGoBack: NavigationManager.canGoBack
            viewTitle: {
                switch (NavigationManager.currentView) {
                    case "library":    return "Library"
                    case "collection": return "Collection"
                    case "image":      return "Image"
                    default:           return ""
                }
            }
            onGoBackRequested: NavigationManager.goBack()
        }

        // Library view
        LibraryView {
            id: libraryView
            anchors { top: navBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "library"
            loadingState: root.libraryLoadingState
            gridModel: LibraryState.gridModel
            onLoadMoreRequested: LibraryState.load_more()
        }

        // Restore selection + scroll when navigating back to library
        Connections {
            target: NavigationManager
            function onNavigationChanged() {
                if (NavigationManager.currentView === "library") {
                    var entry = NavigationManager.currentEntry
                    SelectionManager.restore(
                        entry.selection_ids,
                        entry.primary_id,
                        entry.anchor_id
                    )
                    libraryView.scrollToX(entry.scroll_x)
                }
            }
        }

        // Double-click on an image: save state and push image view
        Connections {
            target: SelectionManager
            function onOpenRequested(imageId) {
                NavigationManager.saveSelection(
                    SelectionManager.selectedIds,
                    SelectionManager.primaryId,
                    SelectionManager.anchorId
                )
                NavigationManager.push("image", {
                    "image_id": imageId,
                    "context_ids": LibraryState.gridModel ? LibraryState.gridModel.allIds : []
                })
            }
        }

        // Placeholder — Collection view (Slice 8)
        Item {
            anchors { top: navBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "collection"
        }

        // Image view (Slice 5)
        ImageView {
            anchors { top: navBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "image"
            imageId:   NavigationManager.currentView === "image" ? (NavigationManager.currentEntry.image_id ?? "") : ""
            imageUrl:  NavigationManager.currentView === "image" && NavigationManager.currentEntry.image_id
                           ? baseUrl + "/api/v1/images/" + NavigationManager.currentEntry.image_id + "/file"
                           : ""
            fileStatus: NavigationManager.currentView === "image" ? (NavigationManager.currentEntry.file_status ?? "available") : "available"
            hasNext: NavigationManager.hasNext
            hasPrev: NavigationManager.hasPrev
        }
    }
}
