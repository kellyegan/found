import QtQuick
import Found.Theme 1.0
import "../views"
import "../components"
import "../primitives"

Item {
    id: root
    objectName: "mainRouter"
    anchors.fill: parent

    property string appState: "Launching"
    property string statusMessage: ""
    property bool hasError: false
    property string libraryLoadingState: "Loading"
    readonly property bool relocatePrefixDialogOpen: readyContainer.prefixDialogOpen
    readonly property bool relocationResultDialogOpen: readyContainer.resultDialogOpen

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
        objectName: "readyContainer"
        anchors.fill: parent
        visible: root.appState === "Ready" && splashDismissed

        property bool sidebarOpen: false
        property bool categoriesBarOpen: false
        property bool filterDropdownOpen: false
        property bool metadataSidebarOpen: false
        // Tracks last active view so navigation handler can save the departing state.
        // Initialised to "library" because that is always the starting view.
        property string _lastView: "library"
        property var _viewPanelState: ({
            library:    { sidebarOpen: false, categoriesBarOpen: false, metadataOpen: false },
            collection: { categoriesBarOpen: false, metadataOpen: false },
            image:      { metadataOpen: false }
        })

        // Pending collection deletion — drives the confirmation dialog below
        property string _removeCollectionId: ""
        property string _removeCollectionName: ""

        // Delegates for the relocation flow — owned by RelocationFlow below
        readonly property bool prefixDialogOpen: relocationFlow.prefixDialogOpen
        readonly property bool resultDialogOpen: relocationFlow.resultDialogOpen

        // Background click handler — clears selection when the user clicks any
        // area that no interactive element consumed (title bar background, panel
        // edges, empty window corners, etc.).  z: -1 places it behind every other
        // child so higher-z items (tiles, buttons, sidebars) consume their own
        // events first and this only fires when nothing else did.
        MouseArea {
            anchors.fill: parent
            z: -1
            onClicked: SelectionManager.clear()
        }

        TitleBar {
            id: titleBar
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: NavigationManager.immersiveMode ? 0 : 48
            visible: !NavigationManager.immersiveMode
            canGoBack: NavigationManager.canGoBack
            filterActive: FilterState.hasActiveFilters
            importState: ImportState.loadingState
            importProgress: ImportState.progress
            missingCount: LibraryState.missingCount
            backendConnected: BackendConnection.isConnected
            viewTitle: {
                switch (NavigationManager.currentView) {
                    case "library":    return "Library"
                    case "collection": return NavigationManager.currentEntry.collection_name ?? "Collection"
                    case "image":      return ""
                    case "settings":   return "Settings"
                    default:           return ""
                }
            }
            searchReadOnly: NavigationManager.currentView === "image" || NavigationManager.currentView === "settings"
            activeFilters: {
                if (NavigationManager.currentView === "settings") return []
                var result = []
                var catFilters = FilterState.categoryFilters
                var cats = CategoriesState.categories
                for (var i = 0; i < cats.length; i++) {
                    var catMode = catFilters[cats[i].id]
                    if (catMode && catMode !== "off")
                        result.push({ name: cats[i].name, mode: catMode })
                }
                var tagFilters = FilterState.tagFilters
                var tagNames = TagSearchState.tagNames
                for (var tid in tagFilters) {
                    var tagMode = tagFilters[tid]
                    if (tagMode && tagMode !== "off")
                        result.push({ name: tagNames[tid] ?? tid, mode: tagMode })
                }
                return result
            }
            onGoBackRequested: NavigationManager.goBack()
            onFilterToggleRequested: readyContainer.filterDropdownOpen = !readyContainer.filterDropdownOpen
            onSettingsRequested: NavigationManager.push("settings", {})
        }

        // Filter dropdown — anchored below TitleBar on the right, z above grid
        FilterDropdown {
            id: filterDropdown
            anchors { top: titleBar.bottom; right: parent.right; rightMargin: Theme.spacingMd }
            width: 280
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
            activeTags: {
                var result = []
                var tagFilters = FilterState.tagFilters
                var tagNames = TagSearchState.tagNames
                for (var tid in tagFilters) {
                    var mode = tagFilters[tid]
                    if (mode && mode !== "off")
                        result.push({id: tid, name: tagNames[tid] ?? tid, mode: mode})
                }
                return result
            }
            onClearAllRequested: {
                FilterState.clearAllFilters()
                readyContainer.filterDropdownOpen = false
            }
            onRemoveCategoryFilter: function(catId) { FilterState.setCategoryFilter(catId, "off") }
            onRemoveTagFilter: function(tagId) { FilterState.setTagFilter(tagId, "off") }
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
            leftPanelOpen: readyContainer.sidebarOpen
            rightPanelOpen: readyContainer.metadataSidebarOpen
            onLoadMoreRequested: LibraryState.load_more()
            onRemoveImagesRequested: function(imageIds) { LibraryState.removeImages(imageIds) }
            onLocateRequested: function(imageId) { LibraryState.requestLocate(imageId) }
            onViewportVerifyRequested: function(imageIds) { LibraryState.verifyBatch(imageIds) }
        }

        // Central navigation handler — persists per-view panel states and restores
        // selection/scroll on return to library or collection.
        Connections {
            target: NavigationManager
            function onNavigationChanged() {
                var view = NavigationManager.currentView
                var lastView = readyContainer._lastView
                var lastImg = NavigationManager.lastReturnedImageId

                // Save the departing view's panel state before switching.
                if (lastView === "library") {
                    readyContainer._viewPanelState.library.sidebarOpen = readyContainer.sidebarOpen
                    readyContainer._viewPanelState.library.categoriesBarOpen = readyContainer.categoriesBarOpen
                    readyContainer._viewPanelState.library.metadataOpen = readyContainer.metadataSidebarOpen
                } else if (lastView === "collection") {
                    readyContainer._viewPanelState.collection.categoriesBarOpen = readyContainer.categoriesBarOpen
                    readyContainer._viewPanelState.collection.metadataOpen = readyContainer.metadataSidebarOpen
                } else if (lastView === "image") {
                    readyContainer._viewPanelState.image.metadataOpen = readyContainer.metadataSidebarOpen
                }

                // Restore the entering view's saved panel state.
                if (view === "library") {
                    var libState = readyContainer._viewPanelState.library
                    readyContainer.sidebarOpen = libState.sidebarOpen
                    readyContainer.categoriesBarOpen = libState.categoriesBarOpen
                    readyContainer.metadataSidebarOpen = libState.metadataOpen
                } else if (view === "collection") {
                    var colState = readyContainer._viewPanelState.collection
                    readyContainer.categoriesBarOpen = colState.categoriesBarOpen
                    readyContainer.metadataSidebarOpen = colState.metadataOpen
                } else if (view === "image") {
                    if (lastView !== "image") {
                        // First entry into image view — restore its saved state (closed by default).
                        readyContainer.metadataSidebarOpen = readyContainer._viewPanelState.image.metadataOpen
                    } else {
                        // Navigating to a different image within image view —
                        // update the active image so the grid tracks it.
                        var newId = NavigationManager.currentEntry.image_id
                        if (newId) SelectionManager.select(newId)
                    }
                }

                // Restore selection/scroll on return to library or collection.
                if (view === "library") {
                    var entry = NavigationManager.currentEntry
                    if (lastImg !== "" && lastImg !== entry.primary_id) {
                        SelectionManager.select(lastImg)
                        libraryView.scrollToActiveImage()
                    } else {
                        SelectionManager.restore(
                            entry.selection_ids,
                            entry.primary_id,
                            entry.anchor_id
                        )
                        libraryView.scrollToX(entry.scroll_x)
                    }
                } else if (view === "collection") {
                    var colEntry = NavigationManager.currentEntry
                    if (lastImg !== "" && lastImg !== colEntry.primary_id) {
                        SelectionManager.select(lastImg)
                        collectionView.scrollToActiveImage()
                    }
                }

                readyContainer._lastView = view
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

        // Double-click on an image: save state and push image view.
        // When opened from within a collection, carry that collection's
        // identity along and browse its images (not the library's), so
        // prev/next and the removal dialog stay scoped to that collection.
        Connections {
            target: SelectionManager
            function onOpenRequested(imageId) {
                NavigationManager.saveSelection(
                    SelectionManager.selectedIds,
                    SelectionManager.primaryId,
                    SelectionManager.anchorId
                )
                var fromCollection = NavigationManager.currentView === "collection"
                var entry = NavigationManager.currentEntry
                NavigationManager.push("image", {
                    "image_id": imageId,
                    "context_ids": fromCollection && CollectionsState.collectionGridModel
                        ? CollectionsState.collectionGridModel.allIds
                        : (LibraryState.gridModel ? LibraryState.gridModel.allIds : []),
                    "collection_id": fromCollection ? entry.collection_id : null,
                    "collection_name": fromCollection ? entry.collection_name : null
                })
            }
        }

        // Collection view
        CollectionView {
            id: collectionView
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            anchors.bottomMargin: categoriesBar._tabHeight + categoriesBar._stripHeight
            visible: NavigationManager.currentView === "collection"
            collectionName: NavigationManager.currentView === "collection"
                            ? (NavigationManager.currentEntry.collection_name ?? "") : ""
            gridModel: CollectionsState.collectionGridModel
            loadingState: CollectionsState.loadingState
            leftPanelOpen: readyContainer.sidebarOpen
            rightPanelOpen: readyContainer.metadataSidebarOpen
            onRemoveImagesRequested: function(imageIds, alsoFromLibrary) {
                CollectionsState.removeImagesFromCollection(
                    NavigationManager.currentEntry.collection_id ?? "",
                    imageIds,
                    alsoFromLibrary
                )
            }
            onViewportVerifyRequested: function(imageIds) { LibraryState.verifyBatch(imageIds) }
        }

        // Image view (Slice 5)
        ImageView {
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "image"
            imageId:   NavigationManager.currentView === "image" ? (NavigationManager.currentEntry.image_id ?? "") : ""
            imageUrl:  NavigationManager.currentView === "image" && NavigationManager.currentEntry.image_id
                           ? baseUrl + "/api/v1/images/" + NavigationManager.currentEntry.image_id + "/file"
                           : ""
            filename: {
                if (NavigationManager.currentView !== "image" || !NavigationManager.currentEntry.image_id) return ""
                var imgId = NavigationManager.currentEntry.image_id
                var inCollection = (NavigationManager.currentEntry.collection_id ?? "") !== ""
                var srcModel = inCollection ? CollectionsState.collectionGridModel : LibraryState.gridModel
                return srcModel ? srcModel.filenameForId(imgId) : ""
            }
            collectionId: NavigationManager.currentView === "image" ? (NavigationManager.currentEntry.collection_id ?? "") : ""
            fileStatus: NavigationManager.currentView === "image" ? (NavigationManager.currentEntry.file_status ?? "available") : "available"
            hasNext: NavigationManager.hasNext
            hasPrev: NavigationManager.hasPrev
            leftInset: 40
            rightInset: 40
            rightPanelWidth: readyContainer.metadataSidebarOpen ? Theme.overlayWidth : 0
            onPrevRequested: NavigationManager.goPrev()
            onNextRequested: NavigationManager.goNext()
            onImageLoadFailed: function(imageId) { LibraryState.verifyImage(imageId) }
            onRemoveImageRequested: function(imageId, collectionId, alsoFromLibrary) {
                if (collectionId !== "")
                    CollectionsState.removeImagesFromCollection(collectionId, [imageId], alsoFromLibrary)
                else
                    LibraryState.removeImages([imageId])
            }
        }

        // Settings view
        SettingsView {
            id: settingsView
            objectName: "settingsView"
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "settings"
        }

        // Sidebar overlay — rendered above content, below nav bar
        CollectionsSidePanel {
            anchors { top: titleBar.bottom; left: parent.left; bottom: parent.bottom }
            anchors.bottomMargin: categoriesBar._tabHeight + categoriesBar._stripHeight
            width: implicitWidth
            visible: NavigationManager.currentView === "library"
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

            onRemoveCollectionRequested: function(collectionId, collectionName) {
                readyContainer._removeCollectionId = collectionId
                readyContainer._removeCollectionName = collectionName
                removeCollectionDialog.checkboxChecked = false
            }
        }

        // Relocation workflow — locate dialog, prefix bulk-relocate, result summary
        RelocationFlow {
            id: relocationFlow
            anchors.fill: parent
            z: 25
        }

        // Collection-deletion confirmation — images are kept, only the collection is removed
        ConfirmDialog {
            id: removeCollectionDialog
            anchors.fill: parent
            z: 25
            open: readyContainer._removeCollectionId !== ""
            message: "Delete the collection “" + readyContainer._removeCollectionName + "”? Images in it will not be removed from your library."
            confirmLabel: "Delete"
            onConfirmed: {
                CollectionsState.deleteCollection(readyContainer._removeCollectionId)
                readyContainer._removeCollectionId = ""
                readyContainer._removeCollectionName = ""
            }
            onCancelled: {
                readyContainer._removeCollectionId = ""
                readyContainer._removeCollectionName = ""
            }
        }



        // Metadata sidebar — right-edge collapsible panel; open by default, collapses in image view
        MetadataSidePanel {
            id: metadataSidebar
            anchors {
                top: titleBar.bottom
                right: parent.right
                bottom: parent.bottom
            }
            anchors.bottomMargin: (NavigationManager.currentView === "library" || NavigationManager.currentView === "collection")
                                  ? (categoriesBar._tabHeight + categoriesBar._stripHeight) : 0
            width: implicitWidth
            open: readyContainer.metadataSidebarOpen
            metaLoadingState: MetadataState.loadingState
            metaFilename: MetadataState.filename
            metaPath: MetadataState.path
            metaDimensions: MetadataState.dimensions
            metaFileSize: MetadataState.fileSize
            metaDateAdded: MetadataState.dateAdded
            metaIsMissing: MetadataState.isMissing
            tagEditorTags: TagEditorState.tags
            tagEditorLoadingState: TagEditorState.loadingState
            tagEditorSelectionMode: TagEditorState.selectionMode
            categoryEditorCategories: CategoryEditorState.categories
            categoryEditorLoadingState: CategoryEditorState.loadingState
            categoryEditorSelectionMode: CategoryEditorState.selectionMode
            collectionEditorCollections: CollectionEditorState.collections
            collectionEditorLoadingState: CollectionEditorState.loadingState
            collectionEditorSelectionMode: CollectionEditorState.selectionMode
            onToggleRequested: readyContainer.metadataSidebarOpen = !readyContainer.metadataSidebarOpen
            onRevealFileRequested: function(path) { PlatformService.revealFile(path) }
            onAddTagRequested: function(tagId, tagName) { TagEditorState.addTag(tagId, tagName) }
            onRemoveTagRequested: function(tagId) { TagEditorState.removeTag(tagId) }
            onAddTagByNameRequested: function(name) { TagEditorState.addTagByName(name) }
            onAddCategoryRequested: function(catId, catName) { CategoryEditorState.addCategory(catId, catName) }
            onRemoveCategoryRequested: function(catId) { CategoryEditorState.removeCategory(catId) }
            onAddToCollectionRequested: function(colId, colName) { CollectionEditorState.addToCollection(colId, colName) }
            onRemoveFromCollectionRequested: function(colId) { CollectionEditorState.removeFromCollection(colId) }
            z: 10
        }


        // Import workflow — drop area, deferred scan, and import panel overlay
        // Stops at categoriesBar.top so chip DropAreas are not blocked
        ImportHandler {
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: categoriesBar.top }
            visible: NavigationManager.currentView === "library"
            z: 20
        }
    }

    // Propagate image status changes from library verification to the active collection grid,
    // and refresh the metadata panel's missing-file banner if it's showing the same image.
    Connections {
        target: LibraryState
        function onImageStatusChanged(imageId, status) {
            CollectionsState.collectionGridModel.updateItemStatus(imageId, status)
            if (imageId === MetadataState.imageId) {
                MetadataState.updateFileStatus(status)
            }
        }
    }

    // Re-check a missing image's file when its metadata loads in the image view —
    // the file may have reappeared since the grid was last loaded.
    Connections {
        target: MetadataState
        function onMetadataChanged() {
            if (MetadataState.isMissing && NavigationManager.currentView === "image") {
                LibraryState.verifyImage(MetadataState.imageId)
            }
        }
    }

    // Periodically re-check images marked missing, in case their files have
    // reappeared (e.g. a removable drive was reconnected).
    Timer {
        id: missingPollTimer
        objectName: "missingPollTimer"
        interval: 120000
        repeat: true
        triggeredOnStart: true
        running: root.appState === "Ready"
        onTriggered: {
            if (LibraryState.missingCount > 0) {
                LibraryState.verifyMissing()
            }
        }
    }
}
