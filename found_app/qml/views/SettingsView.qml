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
        height: content.implicitHeight + Theme.spacingMd * 2

        Column {
            id: content
            spacing: Theme.spacingSm

            AppText {
                id: heading
                variant: "heading"
                text: "Appearance"
            }

            AppText {
                variant: "label"
                text: "Theme"
            }

            Row {
                spacing: Theme.spacingSm

                Repeater {
                    id: themeRepeater
                    model: Theme.availableThemes()

                    AppButton {
                        required property var modelData
                        objectName: "themeOption_" + modelData
                        text: modelData
                        onClicked: Theme.setThemeName(modelData)
                    }
                }
            }
        }
    }
}
