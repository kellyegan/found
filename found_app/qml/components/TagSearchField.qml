import QtQuick
import "../primitives"

Item {
    id: root

    property bool _showDropdown: false

    function _commitFirstSuggestion() {
        var sug = TagSearchState.suggestions
        if (sug && sug.length > 0) {
            hideTimer.stop()
            TagSearchState.selectTag(sug[0].id, sug[0].name)
            inputField.text = ""
            root._showDropdown = false
        }
    }

    Timer {
        id: hideTimer
        interval: 200
        onTriggered: root._showDropdown = false
    }

    Connections {
        target: TagSearchState
        function onLoadingStateChanged(state) {
            if (state === "Ready") {
                hideTimer.stop()
                root._showDropdown = true
            } else if (state === "Idle" || state === "Error") {
                root._showDropdown = false
            }
        }
    }

    // ── Input field ──────────────────────────────────────────────────────────
    AppTextField {
        id: inputField
        objectName: "inputBg"
        anchors.fill: parent
        backgroundColor: "transparent"
        leadingIcon: "⌕"
        trailingVisible: root._showDropdown && TagSearchState.loadingState === "Ready"
        placeholderText: "Search tags…"
        onTextChanged: {
            if (text.trim().length > 0)
                TagSearchState.search(text)
            else
                TagSearchState.clear()
        }
        onFocusedChanged: {
            if (focused) hideTimer.stop()
            else hideTimer.start()
        }
        onSubmitted: root._commitFirstSuggestion()
        onEscaped: {
            text = ""
            TagSearchState.clear()
            root._showDropdown = false
            blur()
        }
    }

    // ── Suggestions dropdown — overflows TitleBar bounds via z:100 ───────────
    DropdownList {
        anchors { top: parent.bottom; left: parent.left; right: parent.right }
        visible: root._showDropdown && TagSearchState.loadingState === "Ready"
        maxHeight: 240
        z: 100
        model: TagSearchState.suggestions
        onItemSelected: function(id, name) {
            hideTimer.stop()
            TagSearchState.selectTag(id, name)
            inputField.text = ""
            root._showDropdown = false
        }
    }
}
