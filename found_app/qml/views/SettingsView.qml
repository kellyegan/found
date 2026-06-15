import QtQuick
import Found.Theme 1.0
import "../primitives"

Item {
    id: root

    Surface {
        id: appearanceSection
        objectName: "appearanceSection"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: Theme.spacingLg
        height: heading.implicitHeight + Theme.spacingMd * 2

        AppText {
            id: heading
            variant: "heading"
            text: "Appearance"
        }
    }
}
