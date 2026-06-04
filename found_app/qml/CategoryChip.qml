import QtQuick

Rectangle {
    id: root

    property string categoryId: ""
    property string categoryName: ""
    property string filterState: "off"
    property bool isDropTarget: false

    signal filterToggled(string categoryId)

    width: chipLabel.implicitWidth + 24
    height: parent ? parent.height : 32
    radius: height / 2

    color: {
        if (isDropTarget)                    return "#2a3a4a"
        if (filterState === "include")       return "#2a5a2a"
        if (filterState === "exclude")       return "#5a2a2a"
        return Theme.surface2 ?? "#2a2a2a"
    }

    border.color: {
        if (isDropTarget)                    return "#4488cc"
        if (filterState === "include")       return "#44aa44"
        if (filterState === "exclude")       return "#aa4444"
        return "#444444"
    }
    border.width: 1

    Behavior on color { ColorAnimation { duration: 80 } }

    Text {
        id: chipLabel
        anchors.centerIn: parent
        text: root.categoryName
        font.pixelSize: Theme.fontSizeSm
        font.family: Theme.fontFamily
        color: (root.filterState === "off" && !root.isDropTarget) ? Theme.textMuted : Theme.text
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.filterToggled(root.categoryId)
    }
}
