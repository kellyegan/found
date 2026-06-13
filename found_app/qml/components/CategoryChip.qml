import QtQuick
import Found.Theme 1.0
import "../primitives"

Chip {
    id: root

    property string categoryId: ""
    property string categoryName: ""
    property string filterState: "off"
    property bool isDropTarget: false

    signal filterToggled(string categoryId)

    width: chipLabel.implicitWidth + 24
    height: parent ? parent.height : 32

    chipState: root.isDropTarget ? "drag-hover" : root.filterState

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
