import QtQuick

Item {
    id: row

    property string label: ""
    property string value: ""
    property bool wrap: false

    width: parent ? parent.width : 0
    height: labelText.implicitHeight + valueText.implicitHeight + 12

    Text {
        id: labelText
        anchors { left: parent.left; top: parent.top; topMargin: 4 }
        text: row.label
        font.pixelSize: 10
        font.family: Theme.fontFamily
        color: "#666666"
        font.capitalization: Font.AllUppercase
        font.letterSpacing: 0.8
    }

    Text {
        id: valueText
        anchors { left: parent.left; right: parent.right; top: labelText.bottom; topMargin: 2 }
        text: row.value
        font.pixelSize: 12
        font.family: Theme.fontFamily
        color: "#cccccc"
        wrapMode: row.wrap ? Text.WrapAnywhere : Text.NoWrap
        maximumLineCount: row.wrap ? 0 : 1
        clip: !row.wrap
    }
}
