import QtQuick

SidePanel {
    id: root

    edge: "right"
    title: "Info"
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
                visible: root.metaLoadingState === "Idle"
                topPadding: 8
                width: parent.width
                text: "Select an image to view its details."
                color: "#555555"
                font.pixelSize: 12
                font.family: Theme.fontFamily
                wrapMode: Text.WordWrap
            }

            Text {
                visible: root.metaLoadingState === "Loading"
                topPadding: 8
                width: parent.width
                text: "Loading…"
                color: "#555555"
                font.pixelSize: 12
                font.family: Theme.fontFamily
            }

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

            // ── Inline sub-component: collection editor section ───────────────
            CollectionEditorSection {
                visible: root.collectionEditorSelectionMode !== "none"
                width: parent.width
            }
        }
    }

    // ── Inline sub-component: collection editor section ──────────────────────
    component CollectionEditorSection: Item {
        id: colSection
        implicitHeight: colSecCol.implicitHeight

        property bool _colDropdownOpen: false

        Column {
            id: colSecCol
            width: parent.width
            spacing: 0

            Rectangle { width: parent.width; height: 1; color: "#2a2a2a" }

            Item {
                width: parent.width
                height: 32

                Text {
                    anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                    text: "COLLECTIONS"
                    font.pixelSize: 10
                    font.family: Theme.fontFamily
                    font.capitalization: Font.AllUppercase
                    font.letterSpacing: 0.8
                    color: "#666666"
                }
            }

            Item {
                width: colSecCol.width
                height: 32

                Rectangle {
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter }
                    height: 26; radius: 13
                    color: colAddArea.containsMouse ? "#242424" : "transparent"
                    border.color: colSection._colDropdownOpen ? "#555555" : "#333333"
                    border.width: 1

                    Text {
                        anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                        text: "+"
                        font.pixelSize: 14; color: "#555555"
                    }

                    Text {
                        anchors { left: parent.left; leftMargin: 24; right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                        text: "Add to collection…"
                        color: "#555555"; font.pixelSize: 11; font.family: Theme.fontFamily
                        elide: Text.ElideRight
                    }

                    MouseArea {
                        id: colAddArea
                        anchors.fill: parent
                        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: colSection._colDropdownOpen = !colSection._colDropdownOpen
                    }
                }
            }

            Rectangle {
                visible: colSection._colDropdownOpen
                width: colSecCol.width
                height: visible ? Math.min(colDropList.contentHeight + 8, 160) : 0
                radius: 4; color: "#242424"; border.color: "#3a3a3a"; border.width: 1; clip: true

                ListView {
                    id: colDropList
                    anchors { fill: parent; topMargin: 4; bottomMargin: 4 }
                    model: {
                        var all = CollectionsState.collections
                        var assigned = root.collectionEditorCollections
                        var assignedIds = {}
                        for (var i = 0; i < assigned.length; i++) assignedIds[assigned[i].id] = true
                        return all.filter(function(c) { return !assignedIds[c.id] })
                    }
                    clip: true

                    delegate: Item {
                        required property var modelData
                        width: colDropList.width; height: 26

                        Rectangle { anchors.fill: parent; color: colDropArea.containsMouse ? "#2a2a2a" : "transparent"; radius: 3 }

                        Text {
                            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                            text: modelData.name ?? ""
                            color: Theme.text; font.pixelSize: 11; font.family: Theme.fontFamily
                        }

                        MouseArea {
                            id: colDropArea
                            anchors.fill: parent
                            hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                root.addToCollectionRequested(modelData.id, modelData.name)
                                colSection._colDropdownOpen = false
                            }
                        }
                    }
                }
            }

            Text {
                visible: root.collectionEditorSelectionMode === "multi"
                width: parent.width
                topPadding: 4; bottomPadding: 4
                text: "Adding to all selected images"
                color: "#666666"; font.pixelSize: 11; font.family: Theme.fontFamily; wrapMode: Text.WordWrap
            }

            Flow {
                visible: root.collectionEditorSelectionMode === "single"
                width: parent.width; spacing: 4; topPadding: 4; bottomPadding: 4

                Repeater {
                    model: root.collectionEditorSelectionMode === "single" ? root.collectionEditorCollections : []
                    delegate: Rectangle {
                        required property var modelData
                        width: colChipLabel.implicitWidth + 28; height: 22; radius: 11
                        color: "#232323"; border.color: "#3a3a3a"; border.width: 1

                        Text {
                            id: colChipLabel
                            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                            text: modelData.name ?? ""; font.pixelSize: 11; font.family: Theme.fontFamily; color: "#aaaaaa"
                        }

                        Text {
                            anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                            text: "×"; font.pixelSize: 12
                            color: colChipRemoveArea.containsMouse ? "#ffffff" : "#666666"

                            MouseArea {
                                id: colChipRemoveArea
                                anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: root.removeFromCollectionRequested(modelData.id)
                            }
                        }
                    }
                }
            }

            Item { width: parent.width; height: 8 }
        }
    }
}
