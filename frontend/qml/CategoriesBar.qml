import QtQuick

Item {
    id: root

    property bool open: true
    property var categories: []

    signal toggleRequested()
    signal filterToggled(string categoryId)

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

        ListView {
            id: chipList
            anchors { fill: parent; leftMargin: 12; rightMargin: 12; topMargin: 6; bottomMargin: 6 }
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
    }
}
