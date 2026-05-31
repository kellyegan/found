import QtQuick

Item {
    id: root

    property bool open: true
    property var categories: []

    signal toggleRequested()
    signal filterToggled(string categoryId)
    signal createCategoryRequested(string name)

    readonly property int _stripHeight: 44
    readonly property int _tabHeight: 16

    height: open ? _tabHeight + _stripHeight : _tabHeight
    Behavior on height { NumberAnimation { duration: 200; easing.type: Easing.InOutQuad } }

    // ── Toggle tab — sits at the top of the bar ──────────────────────────────
    Rectangle {
        id: toggleTab
        width: 48
        height: root._tabHeight
        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top }
        color: "#1a1a1a"
        radius: 3

        Text {
            anchors.centerIn: parent
            text: root.open ? "▼" : "▲"
            font.pixelSize: 8
            color: "#666666"
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.toggleRequested()
        }
    }

    // ── Chip strip — below the tab ───────────────────────────────────────────
    Rectangle {
        id: strip
        anchors { top: toggleTab.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
        color: Theme.surface
        clip: true
        opacity: root.open ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 150 } }

        // Fixed "+" button — always visible on the left, does not scroll
        Rectangle {
            id: addBtn
            anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
            width: 28
            height: 28
            radius: 14
            color: addBtnArea.containsMouse ? "#333333" : "transparent"
            z: 2

            Text {
                anchors.centerIn: parent
                text: "+"
                font.pixelSize: 18
                color: "#888888"
            }

            MouseArea {
                id: addBtnArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    newCategoryInput.text = ""
                    createOverlay.visible = true
                    newCategoryInput.forceActiveFocus()
                }
            }
        }

        ListView {
            id: chipList
            anchors {
                fill: parent
                leftMargin: addBtn.width + 16
                rightMargin: 12
                topMargin: 6
                bottomMargin: 6
            }
            orientation: ListView.Horizontal
            spacing: 8
            clip: true
            model: root.categories

            delegate: Rectangle {
                id: chip
                required property var modelData
                width: chipLabel.implicitWidth + 24
                height: parent ? parent.height : 32
                radius: height / 2
                color: {
                    if (modelData.filterState === "include") return "#2a5a2a"
                    if (modelData.filterState === "exclude") return "#5a2a2a"
                    return Theme.surface2 ?? "#2a2a2a"
                }
                border.color: {
                    if (modelData.filterState === "include") return "#44aa44"
                    if (modelData.filterState === "exclude") return "#aa4444"
                    return "#444444"
                }
                border.width: 1

                Text {
                    id: chipLabel
                    anchors.centerIn: parent
                    text: modelData.name
                    font.pixelSize: Theme.fontSizeSm
                    font.family: Theme.fontFamily
                    color: modelData.filterState === "off" ? Theme.textMuted : Theme.text
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.filterToggled(modelData.id)
                }
            }
        }

        // ── Create overlay — dims chips, shows centered input ─────────────────
        Rectangle {
            id: createOverlay
            anchors.fill: parent
            color: "#cc1a1a1a"
            visible: false
            z: 3

            // Dismiss on click outside — z:0 so inputContainer sits above it
            MouseArea {
                anchors.fill: parent
                z: 0
                onClicked: {
                    createOverlay.visible = false
                    newCategoryInput.text = ""
                }
            }

            Rectangle {
                id: inputContainer
                anchors.centerIn: parent
                width: Math.min(320, parent.width - 32)
                height: 32
                radius: 16
                color: "#2a2a2a"
                border.color: "#555555"
                border.width: 1
                z: 1

                TextInput {
                    id: newCategoryInput
                    anchors {
                        left: parent.left; leftMargin: 14
                        right: submitBtn.left; rightMargin: 6
                        verticalCenter: parent.verticalCenter
                    }
                    color: Theme.text
                    font.pixelSize: Theme.fontSizeSm
                    font.family: Theme.fontFamily
                    clip: true

                    Text {
                        anchors.fill: parent
                        text: "New category name…"
                        color: "#555555"
                        font.pixelSize: Theme.fontSizeSm
                        font.family: Theme.fontFamily
                        visible: newCategoryInput.text.length === 0
                    }

                    Keys.priority: Keys.BeforeItem
                    Keys.onReturnPressed: function(event) {
                        event.accepted = true
                        inputContainer._submit()
                    }
                    Keys.onEnterPressed: function(event) {
                        event.accepted = true
                        inputContainer._submit()
                    }
                    Keys.onEscapePressed: function(event) {
                        event.accepted = true
                        createOverlay.visible = false
                        text = ""
                    }
                }

                Rectangle {
                    id: submitBtn
                    anchors { right: parent.right; rightMargin: 4; verticalCenter: parent.verticalCenter }
                    width: 24
                    height: 24
                    radius: 12
                    color: submitBtnArea.containsMouse && newCategoryInput.text.trim().length > 0
                           ? "#3a5a3a" : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "↵"
                        font.pixelSize: 12
                        color: newCategoryInput.text.trim().length > 0 ? "#88cc88" : "#555555"
                    }

                    MouseArea {
                        id: submitBtnArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: inputContainer._submit()
                    }
                }

                function _submit() {
                    var name = newCategoryInput.text.trim()
                    if (name.length > 0) {
                        root.createCategoryRequested(name)
                    }
                    createOverlay.visible = false
                    newCategoryInput.text = ""
                }
            }
        }
    }
}
