import QtQuick

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
    Rectangle {
        id: inputBg
        anchors.fill: parent
        color: inputField.activeFocus ? "#242424" : "transparent"
        border.color: inputField.activeFocus ? "#555555" : "#333333"
        border.width: 1
        radius: 4

        Text {
            id: searchIcon
            anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
            text: "⌕"
            font.pixelSize: 14
            color: Theme.textMuted
        }

        // Submit button — visible when suggestions are ready
        Rectangle {
            id: submitBtn
            visible: root._showDropdown && TagSearchState.loadingState === "Ready"
            anchors { right: parent.right; rightMargin: 4; verticalCenter: parent.verticalCenter }
            width: 22
            height: 22
            radius: 11
            color: submitBtnArea.containsMouse ? "#3a5a3a" : "transparent"

            Text {
                anchors.centerIn: parent
                text: "↵"
                font.pixelSize: 11
                color: "#88cc88"
            }

            MouseArea {
                id: submitBtnArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root._commitFirstSuggestion()
            }
        }

        TextInput {
            id: inputField
            anchors {
                left: searchIcon.right; leftMargin: 4
                right: submitBtn.left
                rightMargin: 2
                verticalCenter: parent.verticalCenter
            }
            color: Theme.text
            font.pixelSize: Theme.fontSizeSm
            font.family: Theme.fontFamily
            clip: true

            Text {
                anchors.fill: parent
                visible: inputField.text.length === 0
                text: "Search tags…"
                color: "#555555"
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
            }

            onTextChanged: {
                if (text.trim().length > 0)
                    TagSearchState.search(text)
                else
                    TagSearchState.clear()
            }

            onActiveFocusChanged: {
                if (activeFocus) {
                    hideTimer.stop()
                } else {
                    hideTimer.start()
                }
            }

            Keys.priority: Keys.BeforeItem

            Keys.onReturnPressed: function(event) {
                event.accepted = true
                root._commitFirstSuggestion()
            }

            Keys.onEnterPressed: function(event) {
                event.accepted = true
                root._commitFirstSuggestion()
            }

            Keys.onEscapePressed: function(event) {
                event.accepted = true
                text = ""
                TagSearchState.clear()
                root._showDropdown = false
                focus = false
            }
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
                    color: delegateArea.containsMouse ? "#2a2a2a" : "transparent"
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
