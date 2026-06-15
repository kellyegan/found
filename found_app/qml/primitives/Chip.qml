import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property string chipState: "off"
    property alias borderColor: root.border.color

    radius: height / 2
    border.width: 1

    color: {
        switch (root.chipState) {
        case "include": return Theme.accent
        case "exclude": return Theme.warning
        case "mixed": return Theme.surface
        case "drag-hover": return Theme.accent
        default: return Theme.border
        }
    }
    border.color: root.color
}
