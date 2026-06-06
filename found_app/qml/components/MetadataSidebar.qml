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

            TagEditorSection {
                visible: root.tagEditorSelectionMode !== "none"
                width: parent.width
            }

            CategoryEditorSection {
                visible: root.categoryEditorSelectionMode !== "none"
                width: parent.width
            }

            CollectionEditorSection {
                visible: root.collectionEditorSelectionMode !== "none"
                width: parent.width
            }
        }
    }

    // ── Inline sub-component: a label/value row ───────────────────────────────
    component MetaRow: Item {
        id: row
        property string label: ""
        property string value: ""
        property bool wrap: false

        width: parent ? parent.width : 0
        height: labelText.implicitHeight + valueText.implicitHeight + 12

        Text {
            id: labelText
            anchors { left: parent.left; top: parent.top; topMargin: 4 }
            text: row.label
            font.pixelSize: 10
            font.family: Theme.fontFamily
            color: "#666666"
            font.capitalization: Font.AllUppercase
            font.letterSpacing: 0.8
        }

        Text {
            id: valueText
            anchors { left: parent.left; right: parent.right; top: labelText.bottom; topMargin: 2 }
            text: row.value
            font.pixelSize: 12
            font.family: Theme.fontFamily
            color: "#cccccc"
            wrapMode: row.wrap ? Text.WrapAnywhere : Text.NoWrap
            maximumLineCount: row.wrap ? 0 : 1
            clip: !row.wrap
        }
    }

    // ── Inline sub-component: tag editor section ──────────────────────────────
    component TagEditorSection: Item {
        id: tagSection
        implicitHeight: tagSecCol.implicitHeight

        property bool _tagSearchOpen: false

        function _commit() {
            var text = tagAddInput.text.trim()
            if (text.length === 0) return
            var sug = TagEditorSearchState.suggestions
            tagHideTimer.stop()
            if (sug && sug.length > 0) {
                root.addTagRequested(sug[0].id, sug[0].name)
            } else {
                root.addTagByNameRequested(text)
            }
            TagEditorSearchState.clear()
            tagAddInput.text = ""
            tagSection._tagSearchOpen = false
        }

        Timer {
            id: tagHideTimer
            interval: 200
            onTriggered: tagSection._tagSearchOpen = false
        }

        Connections {
            target: TagEditorSearchState
            function onLoadingStateChanged(state) {
                if (state === "Ready") {
                    tagHideTimer.stop()
                    tagSection._tagSearchOpen = true
                } else if (state === "Idle" || state === "Error") {
                    tagSection._tagSearchOpen = false
                }
            }
        }

        Column {
            id: tagSecCol
            width: parent.width
            spacing: 0

            Rectangle { width: parent.width; height: 1; color: "#2a2a2a" }

            Item {
                width: parent.width
                height: 32

                Text {
                    anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                    text: "TAGS"
                    font.pixelSize: 10
                    font.family: Theme.fontFamily
                    font.capitalization: Font.AllUppercase
                    font.letterSpacing: 0.8
                    color: "#666666"
                }
            }

            Item {
                width: tagSecCol.width
                height: 32

                Rectangle {
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter }
                    height: 26
                    radius: 13
                    color: tagAddInput.activeFocus ? "#242424" : "transparent"
                    border.color: tagAddInput.activeFocus ? "#555555" : "#333333"
                    border.width: 1

                    Text {
                        id: tagAddIcon
                        anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                        text: "+"
                        font.pixelSize: 14
                        color: "#555555"
                    }

                    Rectangle {
                        id: tagSubmitBtn
                        visible: tagAddInput.text.trim().length > 0
                        anchors { right: parent.right; rightMargin: 3; verticalCenter: parent.verticalCenter }
                        width: 20
                        height: 20
                        radius: 10
                        color: tagSubmitArea.containsMouse ? "#3a5a3a" : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: "↵"
                            font.pixelSize: 10
                            color: "#88cc88"
                        }

                        MouseArea {
                            id: tagSubmitArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: tagSection._commit()
                        }
                    }

                    TextInput {
                        id: tagAddInput
                        anchors {
                            left: tagAddIcon.right; leftMargin: 4
                            right: tagSubmitBtn.left; rightMargin: 2
                            verticalCenter: parent.verticalCenter
                        }
                        activeFocusOnTab: false
                        color: Theme.text
                        font.pixelSize: 11
                        font.family: Theme.fontFamily
                        clip: true

                        Text {
                            anchors.fill: parent
                            visible: tagAddInput.text.length === 0
                            text: "Add tag…"
                            color: "#555555"
                            font.pixelSize: 11
                            font.family: Theme.fontFamily
                        }

                        onTextChanged: {
                            if (text.trim().length > 0)
                                TagEditorSearchState.search(text)
                            else
                                TagEditorSearchState.clear()
                        }

                        onActiveFocusChanged: {
                            if (activeFocus) tagHideTimer.stop()
                            else tagHideTimer.start()
                        }

                        Keys.priority: Keys.BeforeItem
                        Keys.onReturnPressed: function(event) { event.accepted = true; tagSection._commit() }
                        Keys.onEnterPressed:  function(event) { event.accepted = true; tagSection._commit() }
                        Keys.onEscapePressed: function(event) {
                            event.accepted = true
                            text = ""
                            TagEditorSearchState.clear()
                            tagSection._tagSearchOpen = false
                            focus = false
                        }
                    }
                }
            }

            Rectangle {
                visible: tagSection._tagSearchOpen && TagEditorSearchState.loadingState === "Ready"
                width: tagSecCol.width
                height: visible ? Math.min(tagSuggList.contentHeight + 8, 160) : 0
                radius: 4
                color: "#242424"
                border.color: "#3a3a3a"
                border.width: 1
                clip: true

                ListView {
                    id: tagSuggList
                    anchors { fill: parent; topMargin: 4; bottomMargin: 4 }
                    model: TagEditorSearchState.suggestions
                    clip: true

                    delegate: Item {
                        required property var modelData
                        width: tagSuggList.width
                        height: 26

                        Rectangle { anchors.fill: parent; color: suggArea.containsMouse ? "#2a2a2a" : "transparent"; radius: 3 }

                        Text {
                            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                            text: modelData.name ?? ""
                            color: Theme.text
                            font.pixelSize: 11
                            font.family: Theme.fontFamily
                        }

                        MouseArea {
                            id: suggArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                tagHideTimer.stop()
                                root.addTagRequested(modelData.id, modelData.name)
                                TagEditorSearchState.clear()
                                tagAddInput.text = ""
                                tagSection._tagSearchOpen = false
                            }
                        }
                    }
                }
            }

            Text {
                visible: root.tagEditorSelectionMode === "multi"
                width: parent.width
                topPadding: 4
                bottomPadding: 4
                text: "Adding tags to all selected images"
                color: "#666666"
                font.pixelSize: 11
                font.family: Theme.fontFamily
                wrapMode: Text.WordWrap
            }

            Flow {
                visible: root.tagEditorSelectionMode === "single"
                width: parent.width
                spacing: 4
                topPadding: 4
                bottomPadding: 4

                Repeater {
                    model: root.tagEditorSelectionMode === "single" ? root.tagEditorTags : []
                    delegate: Rectangle {
                        required property var modelData
                        width: chipLabel.implicitWidth + 28
                        height: 22
                        radius: 11
                        color: "#232323"
                        border.color: "#3a3a3a"
                        border.width: 1

                        Text {
                            id: chipLabel
                            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                            text: modelData.name ?? ""
                            font.pixelSize: 11
                            font.family: Theme.fontFamily
                            color: "#aaaaaa"
                        }

                        Text {
                            anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                            text: "×"
                            font.pixelSize: 12
                            color: chipRemoveArea.containsMouse ? "#ffffff" : "#666666"

                            MouseArea {
                                id: chipRemoveArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.removeTagRequested(modelData.id)
                            }
                        }
                    }
                }
            }

            Item { width: parent.width; height: 8 }
        }
    }

    // ── Inline sub-component: category editor section ────────────────────────
    component CategoryEditorSection: Item {
        id: catSection
        implicitHeight: catSecCol.implicitHeight

        property bool _catSearchOpen: false

        function _commit() {
            var text = catAddInput.text.trim()
            if (text.length === 0) return
            var sug = CategoryEditorSearchState.suggestions
            catHideTimer.stop()
            if (sug && sug.length > 0) {
                root.addCategoryRequested(sug[0].id, sug[0].name)
            }
            CategoryEditorSearchState.clear()
            catAddInput.text = ""
            catSection._catSearchOpen = false
        }

        Timer {
            id: catHideTimer
            interval: 200
            onTriggered: catSection._catSearchOpen = false
        }

        Connections {
            target: CategoryEditorSearchState
            function onLoadingStateChanged(state) {
                if (state === "Ready") {
                    catHideTimer.stop()
                    catSection._catSearchOpen = true
                } else if (state === "Idle" || state === "Error") {
                    catSection._catSearchOpen = false
                }
            }
        }

        Column {
            id: catSecCol
            width: parent.width
            spacing: 0

            Rectangle { width: parent.width; height: 1; color: "#2a2a2a" }

            Item {
                width: parent.width
                height: 32

                Text {
                    anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                    text: "CATEGORIES"
                    font.pixelSize: 10
                    font.family: Theme.fontFamily
                    font.capitalization: Font.AllUppercase
                    font.letterSpacing: 0.8
                    color: "#666666"
                }
            }

            Item {
                width: catSecCol.width
                height: 32

                Rectangle {
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter }
                    height: 26
                    radius: 13
                    color: catAddInput.activeFocus ? "#242424" : "transparent"
                    border.color: catAddInput.activeFocus ? "#555555" : "#333333"
                    border.width: 1

                    Text {
                        id: catAddIcon
                        anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                        text: "+"
                        font.pixelSize: 14
                        color: "#555555"
                    }

                    Rectangle {
                        id: catSubmitBtn
                        visible: catAddInput.text.trim().length > 0
                        anchors { right: parent.right; rightMargin: 3; verticalCenter: parent.verticalCenter }
                        width: 20; height: 20; radius: 10
                        color: catSubmitArea.containsMouse ? "#3a5a3a" : "transparent"

                        Text { anchors.centerIn: parent; text: "↵"; font.pixelSize: 10; color: "#88cc88" }

                        MouseArea {
                            id: catSubmitArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: catSection._commit()
                        }
                    }

                    TextInput {
                        id: catAddInput
                        anchors {
                            left: catAddIcon.right; leftMargin: 4
                            right: catSubmitBtn.left; rightMargin: 2
                            verticalCenter: parent.verticalCenter
                        }
                        activeFocusOnTab: false
                        color: Theme.text
                        font.pixelSize: 11
                        font.family: Theme.fontFamily
                        clip: true

                        Text {
                            anchors.fill: parent
                            visible: catAddInput.text.length === 0
                            text: "Add category…"
                            color: "#555555"
                            font.pixelSize: 11
                            font.family: Theme.fontFamily
                        }

                        onTextChanged: {
                            if (text.trim().length > 0)
                                CategoryEditorSearchState.search(text)
                            else
                                CategoryEditorSearchState.clear()
                        }

                        onActiveFocusChanged: {
                            if (activeFocus) catHideTimer.stop()
                            else catHideTimer.start()
                        }

                        Keys.priority: Keys.BeforeItem
                        Keys.onReturnPressed: function(e) { e.accepted = true; catSection._commit() }
                        Keys.onEnterPressed:  function(e) { e.accepted = true; catSection._commit() }
                        Keys.onEscapePressed: function(e) {
                            e.accepted = true
                            text = ""
                            CategoryEditorSearchState.clear()
                            catSection._catSearchOpen = false
                            focus = false
                        }
                    }
                }
            }

            Rectangle {
                visible: catSection._catSearchOpen && CategoryEditorSearchState.loadingState === "Ready"
                width: catSecCol.width
                height: visible ? Math.min(catSuggList.contentHeight + 8, 160) : 0
                radius: 4; color: "#242424"; border.color: "#3a3a3a"; border.width: 1; clip: true

                ListView {
                    id: catSuggList
                    anchors { fill: parent; topMargin: 4; bottomMargin: 4 }
                    model: CategoryEditorSearchState.suggestions
                    clip: true

                    delegate: Item {
                        required property var modelData
                        width: catSuggList.width; height: 26

                        Rectangle { anchors.fill: parent; color: catSuggArea.containsMouse ? "#2a2a2a" : "transparent"; radius: 3 }

                        Text {
                            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                            text: modelData.name ?? ""
                            color: Theme.text; font.pixelSize: 11; font.family: Theme.fontFamily
                        }

                        MouseArea {
                            id: catSuggArea
                            anchors.fill: parent
                            hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                catHideTimer.stop()
                                root.addCategoryRequested(modelData.id, modelData.name)
                                CategoryEditorSearchState.clear()
                                catAddInput.text = ""
                                catSection._catSearchOpen = false
                            }
                        }
                    }
                }
            }

            Text {
                visible: root.categoryEditorSelectionMode === "multi"
                width: parent.width
                topPadding: 4; bottomPadding: 4
                text: "Adding categories to all selected images"
                color: "#666666"; font.pixelSize: 11; font.family: Theme.fontFamily; wrapMode: Text.WordWrap
            }

            Flow {
                visible: root.categoryEditorSelectionMode === "single"
                width: parent.width; spacing: 4; topPadding: 4; bottomPadding: 4

                Repeater {
                    model: root.categoryEditorSelectionMode === "single" ? root.categoryEditorCategories : []
                    delegate: Rectangle {
                        required property var modelData
                        width: catChipLabel.implicitWidth + 28; height: 22; radius: 11
                        color: "#232323"; border.color: "#3a3a3a"; border.width: 1

                        Text {
                            id: catChipLabel
                            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                            text: modelData.name ?? ""; font.pixelSize: 11; font.family: Theme.fontFamily; color: "#aaaaaa"
                        }

                        Text {
                            anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                            text: "×"; font.pixelSize: 12
                            color: catChipRemoveArea.containsMouse ? "#ffffff" : "#666666"

                            MouseArea {
                                id: catChipRemoveArea
                                anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: root.removeCategoryRequested(modelData.id)
                            }
                        }
                    }
                }
            }

            Item { width: parent.width; height: 8 }
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
