import QtQuick
import Found.Theme 1.0
import "../primitives"

// Generic search-input + chip-list section used for Tags and Categories.
// Pass searchState as the relevant context object (TagEditorSearchState or
// CategoryEditorSearchState). Set allowCreateNew: true for tags so that
// typing a name that has no match still creates a new item.
Item {
    id: root

    property string sectionLabel: ""
    property string selectionMode: "none"
    property var items: []
    property var searchState: null
    property bool allowCreateNew: false
    property string placeholder: ""
    property string multiSelectLabel: ""

    signal addRequested(string id, string name)
    signal removeRequested(string id)
    signal addByNameRequested(string name)

    implicitHeight: secCol.implicitHeight

    property bool _searchOpen: false

    function _commit() {
        var text = addField.text.trim()
        if (text.length === 0) return
        var sug = root.searchState ? root.searchState.suggestions : null
        hideTimer.stop()
        if (sug && sug.length > 0) {
            root.addRequested(sug[0].id, sug[0].name)
        } else if (root.allowCreateNew) {
            root.addByNameRequested(text)
        }
        if (root.searchState) root.searchState.clear()
        addField.text = ""
        root._searchOpen = false
    }

    function _selectSuggestion(id, name) {
        hideTimer.stop()
        root.addRequested(id, name)
        if (root.searchState) root.searchState.clear()
        addField.text = ""
        root._searchOpen = false
    }

    Timer {
        id: hideTimer
        interval: 200
        onTriggered: root._searchOpen = false
    }

    Connections {
        target: root.searchState
        function onLoadingStateChanged(state) {
            if (state === "Ready") {
                hideTimer.stop()
                root._searchOpen = true
            } else if (state === "Idle" || state === "Error") {
                root._searchOpen = false
            }
        }
    }

    Column {
        id: secCol
        width: parent.width
        spacing: 0

        // Section separator
        Rectangle { objectName: "sectionSeparator"; width: parent.width; height: 1; color: Theme.border }

        // Section label row
        Item {
            width: parent.width
            height: 32

            Text {
                objectName: "sectionLabel"
                anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                text: root.sectionLabel
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
                font.capitalization: Font.AllUppercase
                font.letterSpacing: 0.8
                color: Theme.textMuted
            }
        }

        // Search input row
        Item {
            width: secCol.width
            height: 32

            AppTextField {
                id: addField
                objectName: "addField"
                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter }
                height: 26
                pill: true
                leadingIcon: "+"
                trailingVisible: text.trim().length > 0
                placeholderText: root.placeholder
                onTextChanged: {
                    if (text.trim().length > 0 && root.searchState)
                        root.searchState.search(text)
                    else if (root.searchState)
                        root.searchState.clear()
                }
                onFocusedChanged: {
                    if (focused) hideTimer.stop()
                    else hideTimer.start()
                }
                onSubmitted: root._commit()
                onEscaped: {
                    text = ""
                    if (root.searchState) root.searchState.clear()
                    root._searchOpen = false
                    blur()
                }
            }
        }

        // Suggestions dropdown
        DropdownList {
            visible: root._searchOpen && root.searchState && root.searchState.loadingState === "Ready"
            width: secCol.width
            model: root.searchState ? root.searchState.suggestions : []
            onItemSelected: function(id, name) { root._selectSuggestion(id, name) }
        }

        // Multi-select note
        Text {
            visible: root.selectionMode === "multi"
            width: parent.width
            topPadding: 4; bottomPadding: 4
            text: root.multiSelectLabel
            color: Theme.textMuted; font.pixelSize: Theme.fontSizeSm; font.family: Theme.fontFamily; wrapMode: Text.WordWrap
        }

        // Current item chips — single selection mode only
        Flow {
            visible: root.selectionMode === "single"
            width: parent.width; spacing: 4; topPadding: 4; bottomPadding: 4

            Repeater {
                model: root.selectionMode === "single" ? root.items : []
                delegate: Chip {
                    required property var modelData
                    chipState: "assigned"
                    text: modelData.name ?? ""
                    removable: true
                    onRemoveRequested: root.removeRequested(modelData.id)
                }
            }
        }

        Item { width: parent.width; height: 8 }
    }
}
