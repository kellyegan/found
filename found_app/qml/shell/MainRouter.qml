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
        objectName: "splashScreen"
        anchors.fill: parent
        visible: !splashScreen.isDismissed
        statusText: root.statusMessage
        hasError: root.hasError
        appVersion: foundVersion
        appLicense: foundLicense
        isReady: root.appState === "Ready"
        z: 1
    }

    // Ready state — navigation bar + view router
    Item {
        id: readyContainer
        objectName: "readyContainer"
        anchors.fill: parent
        visible: root.appState === "Ready" && splashScreen.isDismissed

        // ── Properties ───────────────────────────────────────────────────────

        readonly property bool leftPanelOpen:  PanelLayout ? PanelLayout.openPanels["left"]  !== "" : false
        readonly property bool rightPanelOpen: PanelLayout ? PanelLayout.openPanels["right"] !== "" : false
        // Tracks last active view so the navigation handler can saveViewState on departure.
        // Initialised to "library" because that is always the starting view.
        property string _lastView: "library"

        // Delegates for the relocation flow — owned by RelocationFlow below
        readonly property bool prefixDialogOpen: relocationFlow.prefixDialogOpen
        readonly property bool resultDialogOpen: relocationFlow.resultDialogOpen

        // ── Layer -1: Background ─────────────────────────────────────────────
        // Clears selection when the user clicks any area no interactive element
        // consumed. z: -1 ensures higher-z items consume their own events first.

        MouseArea {
            anchors.fill: parent
            z: -1
            onClicked: SelectionManager.clear()
        }

        // ── Layer 0: Content views ───────────────────────────────────────────

        LibraryView {
            id: libraryView
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "library"
            loadingState: root.libraryLoadingState
            gridModel: LibraryState.gridModel
            leftPanelOpen: readyContainer.leftPanelOpen
            rightPanelOpen: readyContainer.rightPanelOpen
            onLoadMoreRequested: LibraryState.load_more()
            onRemoveImagesRequested: function(imageIds) { LibraryState.removeImages(imageIds) }
            onLocateRequested: function(imageId) { LibraryState.requestLocate(imageId) }
            onViewportVerifyRequested: function(imageIds) { LibraryState.verifyBatch(imageIds) }
        }

        CollectionView {
            id: collectionView
            objectName: "collectionView"
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "collection"
            collectionName: NavigationManager.currentView === "collection"
                            ? (NavigationManager.currentEntry.collection_name ?? "") : ""
            gridModel: CollectionsState.collectionGridModel
            loadingState: CollectionsState.loadingState
            leftPanelOpen: false
            rightPanelOpen: readyContainer.rightPanelOpen
            onRemoveImagesRequested: function(imageIds, alsoFromLibrary) {
                CollectionsState.removeImagesFromCollection(
                    NavigationManager.currentEntry.collection_id ?? "",
                    imageIds,
                    alsoFromLibrary
                )
            }
            onViewportVerifyRequested: function(imageIds) { LibraryState.verifyBatch(imageIds) }
        }

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
            rightPanelWidth: readyContainer.rightPanelOpen ? Theme.overlayWidth : 0
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

        SettingsView {
            id: settingsView
            objectName: "settingsView"
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "settings"
        }

        // ── Layer 0: Chrome ──────────────────────────────────────────────────

        TitleBar {
            id: titleBar
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: NavigationManager.immersiveMode ? 0 : 48
            visible: !NavigationManager.immersiveMode
            z: 15
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
            onSettingsRequested: NavigationManager.push("settings", {})
        }

        // ── Layer 10: Side panels ────────────────────────────────────────────

        CollectionsSidePanel {
            anchors.top: titleBar.bottom
            anchors.bottom: parent.bottom
            anchors.left: (!PanelLayout || PanelLayout.edges["collections"] === "left") ? parent.left : undefined
            anchors.right: (PanelLayout && PanelLayout.edges["collections"] === "right") ? parent.right : undefined
            width: implicitWidth
            visible: NavigationManager.currentView === "library"
            collections: CollectionsState.collections
            z: 10
            onCollectionClicked: function(collectionId, collectionName) {
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
                if (SelectionManager.isSelected(imageId))
                    CollectionEditorState.reload()
            }
            onRemoveCollectionRequested: function(collectionId, collectionName) {
                collectionDeleteFlow.requestDelete(collectionId, collectionName)
            }
        }

        MetadataSidePanel {
            id: metadataSidebar
            anchors.top: titleBar.bottom
            anchors.bottom: parent.bottom
            anchors.left: (PanelLayout && PanelLayout.edges["metadata"] === "left") ? parent.left : undefined
            anchors.right: (!PanelLayout || PanelLayout.edges["metadata"] === "right") ? parent.right : undefined
            width: implicitWidth
            z: 10
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
            collectionEditorCollections: CollectionEditorState.collections
            collectionEditorLoadingState: CollectionEditorState.loadingState
            collectionEditorSelectionMode: CollectionEditorState.selectionMode
            onRevealFileRequested: function(path) { PlatformService.revealFile(path) }
            onAddTagRequested: function(tagId, tagName) { TagEditorState.addTag(tagId, tagName) }
            onRemoveTagRequested: function(tagId) { TagEditorState.removeTag(tagId) }
            onAddTagByNameRequested: function(name) { TagEditorState.addTagByName(name) }
            onAddToCollectionRequested: function(colId, colName) { CollectionEditorState.addToCollection(colId, colName) }
            onRemoveFromCollectionRequested: function(colId) { CollectionEditorState.removeFromCollection(colId) }
        }

        // ── Layer 20: Import overlay ─────────────────────────────────────────
        // Anchored above categoriesBar so chip DropAreas are not blocked.

        ImportHandler {
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            visible: NavigationManager.currentView === "library"
            z: 20
        }

        // ── Layer 30: Panel tab strip (above panels, never clipped by bodies) ─

        PanelTabStrip {
            anchors { top: titleBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
            availablePanels: NavigationManager.currentView === "library"
                             ? ["collections", "metadata"]
                             : ["metadata"]
            z: 30
        }

        // ── Layer 25: Modal flows ────────────────────────────────────────────

        RelocationFlow {
            id: relocationFlow
            anchors.fill: parent
            z: 25
        }

        CollectionDeleteFlow {
            id: collectionDeleteFlow
            anchors.fill: parent
            z: 25
        }

        // ── Connections ──────────────────────────────────────────────────────

        // Central navigation handler — persists per-view panel states via PanelLayout
        // and restores selection/scroll on return to library or collection.
        Connections {
            target: NavigationManager
            function onNavigationChanged() {
                var view = NavigationManager.currentView
                var lastView = readyContainer._lastView
                var lastImg = NavigationManager.lastReturnedImageId

                // Save departing view's panel state; restore entering view's.
                if (PanelLayout) PanelLayout.saveViewState(lastView)
                var available = (view === "library")
                    ? ["collections", "metadata"] : ["metadata"]
                if (PanelLayout) PanelLayout.restoreViewState(view, available)

                // Same-view image navigation: keep open state, update active selection.
                if (view === "image" && lastView === "image") {
                    var newId = NavigationManager.currentEntry.image_id
                    if (newId) SelectionManager.select(newId)
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

        // Load collections when app becomes ready
        Connections {
            target: AppState
            function onStateNameChanged(name) {
                if (name === "Ready") {
                    CollectionsState.load()
                }
            }
        }

        // Double-click on an image: save state and push image view.
        // When opened from within a collection, carry that collection's identity
        // so prev/next and removal stay scoped to that collection.
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
    }

    // ── Root-level connections ────────────────────────────────────────────────
    // These react to app-wide state changes that outlive any single view.

    // Propagate image status changes from library verification to the active
    // collection grid, and refresh the metadata panel's missing-file banner.
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
