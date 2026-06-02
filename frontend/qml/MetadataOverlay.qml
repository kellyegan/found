import QtQuick

Item {
    id: root

    property bool open: false

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

    signal toggleRequested()
    signal addTagRequested(string tagId, string tagName)
    signal removeTagRequested(string tagId)
    signal addTagByNameRequested(string name)

    implicitWidth: Theme.overlayWidth

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

    // ── Slide-in panel ───────────────────────────────────────────────────────
    Rectangle {
        id: panel
        width: root.implicitWidth
        height: parent.height
        x: root.open ? 0 : root.implicitWidth
        color: "#1a1a1a"
        clip: true

        Behavior on x { NumberAnimation { duration: 200; easing.type: Easing.InOutQuad } }

        // Prevents mouse events from reaching library content behind the panel
        MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }

        // Header
        Item {
            id: header
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: 48

            Text {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                text: "Info"
                font.pixelSize: 14
                font.weight: Font.Medium
                color: "#ffffff"
            }
        }

        // Divider
        Rectangle {
            id: divider
            anchors { top: header.bottom; left: parent.left; right: parent.right }
            height: 1
            color: "#2a2a2a"
        }

        // ── Scrollable content area ──────────────────────────────────────────
        Flickable {
            id: contentFlickable
            anchors {
                top: divider.bottom
                left: parent.left; right: parent.right; bottom: parent.bottom
            }
            contentHeight: contentCol.implicitHeight
            clip: true

            Column {
                id: contentCol
                width: contentFlickable.width - 32
                x: 16
                topPadding: 8
                bottomPadding: 16
                spacing: 0

                // Idle / empty selection
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

                // Loading
                Text {
                    visible: root.metaLoadingState === "Loading"
                    topPadding: 8
                    width: parent.width
                    text: "Loading…"
                    color: "#555555"
                    font.pixelSize: 12
                    font.family: Theme.fontFamily
                }

                // Error
                Text {
                    visible: root.metaLoadingState === "Error"
                    topPadding: 8
                    width: parent.width
                    text: "Failed to load metadata."
                    color: "#ff4444"
                    font.pixelSize: 12
                    font.family: Theme.fontFamily
                }

                // Fields — only shown when Ready
                Column {
                    visible: root.metaLoadingState === "Ready"
                    width: parent.width
                    spacing: 0

                    // Missing badge
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

                    // Spacer after missing badge
                    Item {
                        visible: root.metaIsMissing
                        height: 10
                        width: parent.width
                    }

                    MetaRow { label: "Filename"; value: root.metaFilename || "—" }
                    MetaRow { label: "Path";     value: root.metaPath || "—"; wrap: true }
                    MetaRow { label: "Dimensions"; value: root.metaDimensions || "—" }
                    MetaRow { label: "Size";     value: root._formatSize(root.metaFileSize) }
                    MetaRow { label: "Added";    value: root._formatDate(root.metaDateAdded) }
                }

                // ── Tag editor section ────────────────────────────────────────
                TagEditorSection {
                    visible: root.tagEditorSelectionMode !== "none"
                    width: parent.width
                }
            }
        }
    }

    // ── Edge tab — always visible, anchored to the panel's left edge ─────────
    Rectangle {
        id: edgeTab
        width: 16
        height: 72
        x: panel.x - width
        y: (parent.height - height) / 2
        color: "#1a1a1a"
        radius: 2
        z: 1

        Text {
            anchors.centerIn: parent
            text: root.open ? "▶" : "◀"
            font.pixelSize: 10
            color: "#888888"
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.toggleRequested()
        }
    }

    // ── Inline sub-component: a tag/value row in the tag editor ─────────────
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

            // Section separator
            Rectangle {
                width: parent.width
                height: 1
                color: "#2a2a2a"
            }

            // "TAGS" label row
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

            // "Add tag" search row
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

                    // Submit button — visible when suggestions are ready
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
                            right: tagSubmitBtn.left
                            rightMargin: 2
                            verticalCenter: parent.verticalCenter
                        }
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
                            if (activeFocus) {
                                tagHideTimer.stop()
                            } else {
                                tagHideTimer.start()
                            }
                        }

                        Keys.priority: Keys.BeforeItem

                        Keys.onReturnPressed: function(event) {
                            event.accepted = true
                            tagSection._commit()
                        }

                        Keys.onEnterPressed: function(event) {
                            event.accepted = true
                            tagSection._commit()
                        }

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

            // Suggestions dropdown (positioned inside panel, clip handles overflow)
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

                        Rectangle {
                            anchors.fill: parent
                            color: suggArea.containsMouse ? "#2a2a2a" : "transparent"
                            radius: 3
                        }

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

            // Multi-select note
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

            // Current tag chips — inline flow (single mode only)
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

            // Bottom spacer
            Item { width: parent.width; height: 8 }
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
}
