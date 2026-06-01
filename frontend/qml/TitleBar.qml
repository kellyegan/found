import QtQuick

Item {
    id: root

    property bool canGoBack: false
    property string viewTitle: ""
    property bool filterActive: false

    signal goBackRequested()
    signal filterToggleRequested()

    // ── Title zone (left) ────────────────────────────────────────────────────
    Item {
        id: titleZone
        anchors { top: parent.top; left: parent.left; bottom: parent.bottom }
        width: parent.width * 0.5

        Item {
            id: backBtn
            width: visible ? 44 : 0
            height: parent.height
            visible: root.canGoBack

            Text {
                anchors.centerIn: parent
                text: "‹"
                font.pixelSize: 24
                color: Theme.text
            }

            MouseArea {
                anchors.fill: parent
                onClicked: root.goBackRequested()
            }
        }

        Text {
            anchors {
                left: backBtn.right
                leftMargin: Theme.spacingMd
                verticalCenter: parent.verticalCenter
            }
            text: root.viewTitle
            font.pixelSize: Theme.fontSizeMd
            font.family: Theme.fontFamily
            font.weight: Font.Medium
            color: Theme.text
        }
    }

    // ── Status zone (center) ─────────────────────────────────────────────────
    Item {
        id: statusZone
        anchors {
            top: parent.top
            bottom: parent.bottom
            left: titleZone.right
        }
        width: parent.width * 0.2
        // Status indicators will be added in a later commit
    }

    // ── Search zone (right) ──────────────────────────────────────────────────
    Item {
        id: searchZone
        anchors {
            top: parent.top
            bottom: parent.bottom
            left: statusZone.right
            right: parent.right
        }

        // Tag search field — left of filter icon
        TagSearchField {
            id: tagSearchField
            anchors {
                left: parent.left; leftMargin: 8
                right: filterIconBtn.left; rightMargin: 4
                verticalCenter: parent.verticalCenter
            }
            height: 28
        }

        // Filter icon — grey when inactive, accent when filters are active
        Item {
            id: filterIconBtn
            width: 36
            height: parent.height
            anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }

            Text {
                anchors.centerIn: parent
                text: "⊟"
                font.pixelSize: 16
                color: root.filterActive ? Theme.accent : Theme.textMuted
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.filterToggleRequested()
            }
        }
    }
}
