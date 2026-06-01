import QtQuick

Item {
    id: root
    anchors.fill: parent

    property string appState: "Launching"
    property string statusMessage: ""
    property bool hasError: false
    property string libraryLoadingState: "Loading"

    SplashScreen {
        id: splashScreen
        anchors.fill: parent
        visible: !splashDismissed
        statusText: root.statusMessage
        hasError: root.hasError
        appVersion: foundVersion
        appLicense: foundLicense
        isReady: root.appState === "Ready"
        onDismissed: splashDismissed = true
        z: 1
    }

    property bool splashDismissed: false

    // Ready state — navigation bar + view router
    Item {
        id: readyContainer
        anchors.fill: parent
        visible: root.appState === "Ready" && splashDismissed

        property bool sidebarOpen: false
        property bool categoriesBarOpen: false
        property bool filterDropdownOpen: false
        property bool metadataOverlayOpen: false

        TitleBar {
            id: titleBar
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: NavigationManager.immersiveMode ? 0 : 48
            visible: !NavigationManager.immersiveMode
            canGoBack: NavigationManager.canGoBack
            filterActive: FilterState.hasActiveFilters
            viewTitle: {
                switch (NavigationManager.currentView) {
                    case "library":    return "Library"
                    case "collection": return "Collection"
                    case "image":      return "Image"
                    default:           return ""
                }
            }
            onGoBackRequested: NavigationManager.goBack()
            onFilterToggleRequested: readyContainer.filterDropdownOpen = !readyContainer.filterDropdownOpen
        }

        // Filter dropdown — anchored below TitleBar on the right, z above grid
        FilterDropdown {
            id: filterDropdown
            anchors { top: titleBar.bottom; right: parent.right; rightMargin: Theme.spacingMd }
            width: 280
            implicitHeight: 160
            open: readyContainer.filterDropdownOpen
            showMissingOnly: FilterState.showMissingOnly
            importJobActive: FilterState.importJobId !== ""
            activeCategories: {
                var result = []
                var filters = FilterState.categoryFilters
                var cats = CategoriesState.categories
                for (var i = 0; i < cats.length; i++) {
                    var mode = filters[cats[i].id]
                    if (mode && mode !== "off")
                        result.push({id: cats[i].id, name: cats[i].name, mode: mode})
                }
                return result
            }
            onClearAllRequested: {
                FilterState.clearAllFilters()
                readyContainer.filterDropdownOpen = false
            }
            onRemoveCategoryFilter: function(catId) { FilterState.setCategoryFilter(catId, "off") }
            onToggleMissingOnlyRequested: FilterState.setShowMissingOnly(!FilterState.showMissingOnly)
            z: 40
        }

        // Categories bar — structural bottom zone for library/collection views
        CategoriesBar {
            id: categoriesBar
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            open: readyContainer.categoriesBarOpen
            visible: NavigationManager.currentView === "library" || NavigationManager.currentView === "collection"
            categories: CategoriesState.categories
            onToggleRequested: readyContainer.categoriesBarOpen = !readyContainer.categoriesBarOpen
            onFilterToggled: function(categoryId) { CategoriesState.cycleFilter(categoryId) }
            onCreateCategoryRequested: function(name) { CategoriesState.createCategory(name) }
            onImageDropped: function(categoryId, imageId) {
                var ids = SelectionManager.isSelected(imageId)
                    ? SelectionManager.selectedIds
                    : [imageId]
                CategoriesState.addImagesToCategory(categoryId, ids)
            }
            z: 5
        }

        // Library view
        LibraryView {
            id: libraryView
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            anchors.bottomMargin: categoriesBar._tabHeight + categoriesBar._stripHeight
            visible: NavigationManager.currentView === "library"
            loadingState: root.libraryLoadingState
            gridModel: LibraryState.gridModel
            onLoadMoreRequested: LibraryState.load_more()
        }

        // After import completes, filter library to show only the new images
        Connections {
            target: ImportState
            function onLoadingStateChanged(state) {
                if (state === "Complete") {
                    FilterState.setImportJobFilter(ImportState.jobId)
                }
            }
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

        // Load collections and categories when app becomes ready
        Connections {
            target: AppState
            function onStateNameChanged(name) {
                if (name === "Ready") {
                    CollectionsState.load()
                    CategoriesState.load()
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

        // Collection view
        CollectionView {
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            anchors.bottomMargin: categoriesBar._tabHeight + categoriesBar._stripHeight
            visible: NavigationManager.currentView === "collection"
            collectionName: NavigationManager.currentView === "collection"
                            ? (NavigationManager.currentEntry.collection_name ?? "") : ""
            gridModel: CollectionsState.collectionGridModel
            loadingState: CollectionsState.loadingState
        }

        // Image view (Slice 5)
        ImageView {
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "image"
            imageId:   NavigationManager.currentView === "image" ? (NavigationManager.currentEntry.image_id ?? "") : ""
            imageUrl:  NavigationManager.currentView === "image" && NavigationManager.currentEntry.image_id
                           ? baseUrl + "/api/v1/images/" + NavigationManager.currentEntry.image_id + "/file"
                           : ""
            fileStatus: NavigationManager.currentView === "image" ? (NavigationManager.currentEntry.file_status ?? "available") : "available"
            hasNext: NavigationManager.hasNext
            hasPrev: NavigationManager.hasPrev
        }

        // Sidebar overlay — rendered above content, below nav bar
        CollectionsSidebar {
            anchors { top: titleBar.bottom; left: parent.left; bottom: parent.bottom }
            width: implicitWidth
            open: readyContainer.sidebarOpen
            collections: CollectionsState.collections
            z: 10

            onToggleRequested: readyContainer.sidebarOpen = !readyContainer.sidebarOpen

            onCollectionClicked: function(collectionId, collectionName) {
                readyContainer.sidebarOpen = false
                NavigationManager.push("collection", { "collection_id": collectionId, "collection_name": collectionName })
                CollectionsState.loadCollectionImages(collectionId)
            }

            onCreateCollectionRequested: function(name) {
                CollectionsState.createCollection(name)
            }

            onImageDropped: function(collectionId, imageId) {
                var ids = SelectionManager.isSelected(imageId)
                    ? SelectionManager.selectedIds
                    : [imageId]
                CollectionsState.addImagesToCollection(collectionId, ids)
            }
        }

        // Dim overlay behind sidebar
        Rectangle {
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            color: "#000000"
            opacity: readyContainer.sidebarOpen ? 0.4 : 0.0
            z: 9
            visible: opacity > 0

            Behavior on opacity { NumberAnimation { duration: 200 } }

            MouseArea {
                anchors.fill: parent
                enabled: readyContainer.sidebarOpen
                onClicked: readyContainer.sidebarOpen = false
            }
        }

        // Metadata overlay — right-edge collapsible panel; open by default, collapses in image view
        MetadataOverlay {
            id: metadataOverlay
            anchors {
                top: titleBar.bottom
                right: parent.right
                bottom: parent.bottom
            }
            anchors.bottomMargin: (NavigationManager.currentView === "library" || NavigationManager.currentView === "collection")
                                  ? (categoriesBar._tabHeight + categoriesBar._stripHeight) : 0
            width: implicitWidth
            open: readyContainer.metadataOverlayOpen
            metaLoadingState: MetadataState.loadingState
            metaFilename: MetadataState.filename
            metaPath: MetadataState.path
            metaDimensions: MetadataState.dimensions
            metaFileSize: MetadataState.fileSize
            metaDateAdded: MetadataState.dateAdded
            metaIsMissing: MetadataState.isMissing
            onToggleRequested: readyContainer.metadataOverlayOpen = !readyContainer.metadataOverlayOpen
            z: 10
        }

        // Collapse metadata overlay when entering image view
        Connections {
            target: NavigationManager
            function onCurrentViewChanged() {
                if (NavigationManager.currentView === "image") {
                    readyContainer.metadataOverlayOpen = false
                }
            }
        }

        // File drop area — accepts files/directories dragged from Finder/Explorer
        // Stops at categoriesBar.top so chip DropAreas are not blocked by this higher-z area
        DropArea {
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: categoriesBar.top }
            visible: NavigationManager.currentView === "library"
            z: 20

            onEntered: function(drag) {
                drag.accepted = drag.hasUrls
            }

            onDropped: function(drop) {
                if (!drop.hasUrls) return
                var paths = []
                for (var i = 0; i < drop.urls.length; i++) {
                    var s = drop.urls[i].toString()
                    // Strip file:// prefix; handle file:///path on macOS/Linux
                    paths.push(s.replace(/^file:\/\//, ""))
                }
                ImportState.scanPaths(paths)
            }

            // Drag-over highlight
            Rectangle {
                anchors.fill: parent
                color: "#ffffff"
                opacity: parent.containsDrag ? 0.08 : 0.0
                visible: opacity > 0

                Behavior on opacity { NumberAnimation { duration: 100 } }

                Text {
                    anchors.centerIn: parent
                    visible: parent.parent.containsDrag
                    text: "Drop to import"
                    color: "#cccccc"
                    font.pixelSize: 18
                    font.weight: Font.Medium
                }
            }
        }

        // Import panel overlay
        ImportPanel {
            anchors.fill: parent
            z: 30
            loadingState: ImportState.loadingState
            pendingFiles: ImportState.pendingFiles
            conflictFiles: ImportState.conflictFiles
            duplicateCount: ImportState.duplicateFiles.length
            conflictCount: ImportState.conflictFiles.length
            invalidCount: ImportState.invalidFiles.length
            importedCount: ImportState.importedCount
            updatedCount: ImportState.updatedCount
            skippedCount: ImportState.skippedCount
            errorCount: ImportState.errorCount
            progress: ImportState.progress

            onConfirmed: ImportState.executeImport()
            onCancelled: ImportState.cancel()
            onConflictChoiceChanged: function(path, choice) {
                ImportState.setConflictChoice(path, choice)
            }
        }
    }
}
