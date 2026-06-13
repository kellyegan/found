import QtQuick
import Found.Theme 1.0

Rectangle {
    id: root

    property int padding: Theme.spacingMd
    property alias borderColor: root.border.color

    default property alias content: contentItem.data

    color: Theme.surface
    border.color: Theme.border
    border.width: 1
    radius: Theme.spacingXs

    Item {
        id: contentItem
        anchors.fill: parent
        anchors.margins: root.padding
    }
}
