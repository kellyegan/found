import QtQuick
import Found.Theme 1.0

Item {
    id: row

    property string label: ""
    property string value: ""
    property bool wrap: false
    property string linkUrl: ""
    property bool clickable: linkUrl !== ""

    signal clicked()

    width: parent ? parent.width : 0
    height: labelText.implicitHeight + valueText.implicitHeight + 12

    Text {
        id: labelText
        objectName: "labelText"
        anchors { left: parent.left; top: parent.top; topMargin: 4 }
        text: row.label
        font.pixelSize: Theme.fontSizeSm
        font.family: Theme.fontFamily
        color: Theme.textMuted
        font.capitalization: Font.AllUppercase
        font.letterSpacing: 0.8
    }

    Text {
        id: valueText
        objectName: "valueText"
        anchors { left: parent.left; right: parent.right; top: labelText.bottom; topMargin: 2 }
        text: row.value
        font.pixelSize: Theme.fontSizeSm
        font.family: Theme.fontFamily
        color: row.clickable ? (linkArea.containsMouse ? Theme.text : Theme.accent) : Theme.text
        wrapMode: row.wrap ? Text.WrapAnywhere : Text.NoWrap
        maximumLineCount: row.wrap ? 0 : 1
        clip: !row.wrap
    }

    MouseArea {
        id: linkArea
        anchors.fill: valueText
        visible: row.clickable
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            if (row.linkUrl) Qt.openUrlExternally(row.linkUrl)
            row.clicked()
        }
    }
}
