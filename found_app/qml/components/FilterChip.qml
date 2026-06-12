import QtQuick
import Found.Theme 1.0

Item {
    id: root

    property string label: ""
    property string filterMode: "include"

    signal removeRequested()

    implicitWidth: chipRow.implicitWidth + 20
    implicitHeight: 26

    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: root.filterMode === "exclude" ? "#2a1515" : "#152030"
        border.color: root.filterMode === "exclude" ? "#884444" : "#446688"
        border.width: 1

        Row {
            id: chipRow
            anchors { left: parent.left; leftMargin: 8; right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
            spacing: 4

            Text {
                text: root.filterMode === "exclude" ? "−" : "+"
                font.pixelSize: 10
                color: root.filterMode === "exclude" ? "#cc6666" : "#6699cc"
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: root.label
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
                color: Theme.text
                anchors.verticalCenter: parent.verticalCenter
            }

            Item {
                width: 14
                height: chipRow.height
                anchors.verticalCenter: parent.verticalCenter

                Text {
                    anchors.centerIn: parent
                    text: "×"
                    font.pixelSize: 11
                    color: removeBtnArea.containsMouse ? Theme.text : Theme.textMuted
                }

                MouseArea {
                    id: removeBtnArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.removeRequested()
                }
            }
        }
    }
}
