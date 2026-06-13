import QtQuick
import Found.Theme 1.0

Text {
    id: root

    property string variant: "default"

    font.family: Theme.fontFamily
    font.pixelSize: {
        switch (root.variant) {
        case "heading": return Theme.fontSizeLg
        case "label": return Theme.fontSizeSm
        default: return Theme.fontSizeMd
        }
    }
    color: root.variant === "muted" ? Theme.textMuted : Theme.text
}
