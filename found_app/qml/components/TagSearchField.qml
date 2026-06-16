import QtQuick
import Found.Theme 1.0
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
    Rectangle {
        id: dropdown
        anchors { top: parent.bottom; left: parent.left; right: parent.right }
        visible: root._showDropdown && TagSearchState.loadingState === "Ready"
        height: visible ? Math.min(suggestionList.contentHeight + 8, 240) : 0
        z: 100
        color: Theme.surface
        border.color: Theme.border
        border.width: 1
        radius: 4
        clip: true

        ListView {
            id: suggestionList
            anchors { fill: parent; topMargin: 4; bottomMargin: 4 }
            model: TagSearchState.suggestions
            clip: true

            delegate: Item {
                required property var modelData
                width: suggestionList.width
                height: 28

                Rectangle {
                    anchors.fill: parent
                    color: delegateArea.containsMouse ? Theme.border : "transparent"
                    radius: 3
                }

                Text {
                    anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                    text: modelData.name ?? ""
                    color: Theme.text
                    font.pixelSize: Theme.fontSizeSm
                    font.family: Theme.fontFamily
                }

                MouseArea {
                    id: delegateArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        hideTimer.stop()
                        TagSearchState.selectTag(modelData.id, modelData.name)
                        inputField.text = ""
                        root._showDropdown = false
                    }
                }
            }
        }
    }
}
