import QtQuick
import Found.Theme 1.0

// Reusable surface-styled dropdown: Surface rect → ListView → hover delegate.
// Caller controls visibility, anchoring, and z-order.
Rectangle {
    id: root

    property var model: []
    property int maxHeight: 160
    property alias borderColor: root.border.color

    signal itemSelected(string id, string name)

    implicitHeight: Math.min(_list.contentHeight + 8, root.maxHeight)

    radius: 4
    color: Theme.surface
    border.color: Theme.border
    border.width: 1
    clip: true

    ListView {
        id: _list
        anchors { fill: parent; topMargin: 4; bottomMargin: 4 }
        model: root.model
        clip: true

        delegate: Item {
            required property var modelData
            width: _list.width
            height: 26

            Rectangle {
                anchors.fill: parent
                color: _area.containsMouse ? Theme.border : "transparent"
                radius: 3
            }

            Text {
                anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                text: modelData.name ?? ""
                color: Theme.text
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
            }

            MouseArea {
                id: _area
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.itemSelected(modelData.id, modelData.name)
            }
        }
    }
}
