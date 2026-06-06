import QtQuick

SidePanel {
    id: root

    edge: "right"
    title: {
        if (metaLoadingState === "Ready") return "Info"
        if (metaLoadingState === "Loading") return "Loading…"
        if (metaLoadingState === "Idle") return "Select image…"
        if (metaLoadingState === "Error") return "ERROR"
        return "Info"
    }
    panelIcon: "ⓘ"

    // Metadata properties — bound from MetadataState in MainRouter
    property string metaLoadingState: "Idle"
    property string metaFilename: ""
    property string metaPath: ""
    property string metaDimensions: ""
    property int metaFileSize: 0
    property string metaDateAdded: ""
    property bool metaIsMissing: false

    // Tag editor properties — bound from TagEditorState in MainRouter
    property var tagEditorTags: []
    property string tagEditorLoadingState: "Idle"
    property string tagEditorSelectionMode: "none"

    // Category editor properties — bound from CategoryEditorState in MainRouter
    property var categoryEditorCategories: []
    property string categoryEditorLoadingState: "Idle"
    property string categoryEditorSelectionMode: "none"

    // Collection editor properties — bound from CollectionEditorState in MainRouter
    property var collectionEditorCollections: []
    property string collectionEditorLoadingState: "Idle"
    property string collectionEditorSelectionMode: "none"

    signal addTagRequested(string tagId, string tagName)
    signal removeTagRequested(string tagId)
    signal addTagByNameRequested(string name)
    signal addCategoryRequested(string categoryId, string categoryName)
    signal removeCategoryRequested(string categoryId)
    signal addToCollectionRequested(string collectionId, string collectionName)
    signal removeFromCollectionRequested(string collectionId)

    function _formatSize(bytes) {
        if (bytes <= 0) return "—"
        if (bytes < 1024) return bytes + " B"
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB"
        return (bytes / 1048576).toFixed(1) + " MB"
    }

    function _formatDate(isoDate) {
        if (!isoDate) return "—"
        return isoDate.substring(0, 10)
    }

    // ── Scrollable content ───────────────────────────────────────────────────
    Flickable {
        id: contentFlickable
        anchors.fill: parent
        contentHeight: contentCol.implicitHeight
        clip: true

        Column {
            id: contentCol
            width: contentFlickable.width - 32
            x: 16
            topPadding: 8
            bottomPadding: 16
            spacing: 0

            Text {
                visible: root.metaLoadingState === "Error"
                topPadding: 8
                width: parent.width
                text: "Failed to load metadata."
                color: "#ff4444"
                font.pixelSize: 12
                font.family: Theme.fontFamily
            }

            Column {
                visible: root.metaLoadingState === "Ready"
                width: parent.width
                spacing: 0

                Rectangle {
                    visible: root.metaIsMissing
                    width: parent.width
                    height: 28
                    radius: 4
                    color: "#2a1515"
                    border.color: "#884444"
                    border.width: 1

                    Text {
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: "⚠  File missing"
                        font.pixelSize: 11
                        color: "#cc6666"
                    }
                }

                Item {
                    visible: root.metaIsMissing
                    height: 10
                    width: parent.width
                }

                MetaRow { label: "Filename";   value: root.metaFilename || "—" }
                MetaRow { label: "Path";       value: root.metaPath || "—"; wrap: true }
                MetaRow { label: "Dimensions"; value: root.metaDimensions || "—" }
                MetaRow { label: "Size";       value: root._formatSize(root.metaFileSize) }
                MetaRow { label: "Added";      value: root._formatDate(root.metaDateAdded) }
            }

            ChipSearchSection {
                visible: root.tagEditorSelectionMode !== "none"
                width: parent.width
                sectionLabel: "Tags"
                selectionMode: root.tagEditorSelectionMode
                items: root.tagEditorTags
                searchState: TagEditorSearchState
                allowCreateNew: true
                placeholder: "Add tag…"
                multiSelectLabel: "Adding tags to all selected images"
                onAddRequested: (id, name) => root.addTagRequested(id, name)
                onRemoveRequested: (id) => root.removeTagRequested(id)
                onAddByNameRequested: (name) => root.addTagByNameRequested(name)
            }

            ChipSearchSection {
                visible: root.categoryEditorSelectionMode !== "none"
                width: parent.width
                sectionLabel: "Categories"
                selectionMode: root.categoryEditorSelectionMode
                items: root.categoryEditorCategories
                searchState: CategoryEditorSearchState
                allowCreateNew: false
                placeholder: "Add category…"
                multiSelectLabel: "Adding categories to all selected images"
                onAddRequested: (id, name) => root.addCategoryRequested(id, name)
                onRemoveRequested: (id) => root.removeCategoryRequested(id)
            }

            CollectionEditorSection {
                visible: root.collectionEditorSelectionMode !== "none"
                width: parent.width
                selectionMode: root.collectionEditorSelectionMode
                collections: root.collectionEditorCollections
                multiSelectLabel: "Adding to all selected images"
                onAddToCollectionRequested: (id, name) => root.addToCollectionRequested(id, name)
                onRemoveFromCollectionRequested: (id) => root.removeFromCollectionRequested(id)
            }
        }
    }
}
