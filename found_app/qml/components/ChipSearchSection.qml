import QtQuick

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
        var text = addInput.text.trim()
        if (text.length === 0) return
        var sug = root.searchState ? root.searchState.suggestions : null
        hideTimer.stop()
        if (sug && sug.length > 0) {
            root.addRequested(sug[0].id, sug[0].name)
        } else if (root.allowCreateNew) {
            root.addByNameRequested(text)
        }
        if (root.searchState) root.searchState.clear()
        addInput.text = ""
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
        Rectangle { width: parent.width; height: 1; color: "#2a2a2a" }

        // Section label row
        Item {
            width: parent.width
            height: 32

            Text {
                anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                text: root.sectionLabel
                font.pixelSize: 10
                font.family: Theme.fontFamily
                font.capitalization: Font.AllUppercase
                font.letterSpacing: 0.8
                color: "#666666"
            }
        }

        // Search input row
        Item {
            width: secCol.width
            height: 32

            Rectangle {
                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter }
                height: 26
                radius: 13
                color: addInput.activeFocus ? "#242424" : "transparent"
                border.color: addInput.activeFocus ? "#555555" : "#333333"
                border.width: 1

                Text {
                    id: addIcon
                    anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                    text: "+"
                    font.pixelSize: 14
                    color: "#555555"
                }

                Rectangle {
                    id: submitBtn
                    visible: addInput.text.trim().length > 0
                    anchors { right: parent.right; rightMargin: 3; verticalCenter: parent.verticalCenter }
                    width: 20; height: 20; radius: 10
                    color: submitArea.containsMouse ? "#3a5a3a" : "transparent"

                    Text { anchors.centerIn: parent; text: "↵"; font.pixelSize: 10; color: "#88cc88" }

                    MouseArea {
                        id: submitArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root._commit()
                    }
                }

                TextInput {
                    id: addInput
                    anchors {
                        left: addIcon.right; leftMargin: 4
                        right: submitBtn.left; rightMargin: 2
                        verticalCenter: parent.verticalCenter
                    }
                    activeFocusOnTab: false
                    color: Theme.text
                    font.pixelSize: 11
                    font.family: Theme.fontFamily
                    clip: true

                    Text {
                        anchors.fill: parent
                        visible: addInput.text.length === 0
                        text: root.placeholder
                        color: "#555555"
                        font.pixelSize: 11
                        font.family: Theme.fontFamily
                    }

                    onTextChanged: {
                        if (text.trim().length > 0 && root.searchState)
                            root.searchState.search(text)
                        else if (root.searchState)
                            root.searchState.clear()
                    }

                    onActiveFocusChanged: {
                        if (activeFocus) hideTimer.stop()
                        else hideTimer.start()
                    }

                    Keys.priority: Keys.BeforeItem
                    Keys.onReturnPressed: function(event) { event.accepted = true; root._commit() }
                    Keys.onEnterPressed:  function(event) { event.accepted = true; root._commit() }
                    Keys.onEscapePressed: function(event) {
                        event.accepted = true
                        text = ""
                        if (root.searchState) root.searchState.clear()
                        root._searchOpen = false
                        focus = false
                    }
                }
            }
        }

        // Suggestions dropdown
        Rectangle {
            visible: root._searchOpen && root.searchState && root.searchState.loadingState === "Ready"
            width: secCol.width
            height: visible ? Math.min(suggList.contentHeight + 8, 160) : 0
            radius: 4
            color: "#242424"
            border.color: "#3a3a3a"
            border.width: 1
            clip: true

            ListView {
                id: suggList
                anchors { fill: parent; topMargin: 4; bottomMargin: 4 }
                model: root.searchState ? root.searchState.suggestions : []
                clip: true

                delegate: Item {
                    required property var modelData
                    width: suggList.width
                    height: 26

                    Rectangle { anchors.fill: parent; color: suggArea.containsMouse ? "#2a2a2a" : "transparent"; radius: 3 }

                    Text {
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: modelData.name ?? ""
                        color: Theme.text; font.pixelSize: 11; font.family: Theme.fontFamily
                    }

                    MouseArea {
                        id: suggArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            hideTimer.stop()
                            root.addRequested(modelData.id, modelData.name)
                            if (root.searchState) root.searchState.clear()
                            addInput.text = ""
                            root._searchOpen = false
                        }
                    }
                }
            }
        }

        // Multi-select note
        Text {
            visible: root.selectionMode === "multi"
            width: parent.width
            topPadding: 4; bottomPadding: 4
            text: root.multiSelectLabel
            color: "#666666"; font.pixelSize: 11; font.family: Theme.fontFamily; wrapMode: Text.WordWrap
        }

        // Current item chips — single selection mode only
        Flow {
            visible: root.selectionMode === "single"
            width: parent.width; spacing: 4; topPadding: 4; bottomPadding: 4

            Repeater {
                model: root.selectionMode === "single" ? root.items : []
                delegate: Rectangle {
                    required property var modelData
                    width: chipLabel.implicitWidth + 28; height: 22; radius: 11
                    color: "#232323"; border.color: "#3a3a3a"; border.width: 1

                    Text {
                        id: chipLabel
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: modelData.name ?? ""; font.pixelSize: 11; font.family: Theme.fontFamily; color: "#aaaaaa"
                    }

                    Text {
                        anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                        text: "×"; font.pixelSize: 12
                        color: chipRemoveArea.containsMouse ? "#ffffff" : "#666666"

                        MouseArea {
                            id: chipRemoveArea
                            anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: root.removeRequested(modelData.id)
                        }
                    }
                }
            }
        }

        Item { width: parent.width; height: 8 }
    }
}
