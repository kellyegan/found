import QtQuick

Item {
    id: root

    property bool canGoBack: false
    property string viewTitle: ""
    property bool filterActive: false
    property bool searchReadOnly: false
    property var activeFilters: []

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

        // Interactive mode: tag search field + filter icon (library/collection)
        TagSearchField {
            id: tagSearchField
            visible: !root.searchReadOnly
            anchors {
                left: parent.left; leftMargin: 8
                right: filterIconBtn.left; rightMargin: 4
                verticalCenter: parent.verticalCenter
            }
            height: 28
        }

        Item {
            id: filterIconBtn
            visible: !root.searchReadOnly
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

        // Read-only mode: non-interactive filter chips (image view)
        Flow {
            visible: root.searchReadOnly
            anchors {
                left: parent.left; leftMargin: 8
                right: parent.right; rightMargin: 8
                verticalCenter: parent.verticalCenter
            }
            spacing: 4

            Repeater {
                model: root.activeFilters

                delegate: Item {
                    required property var modelData
                    implicitWidth: roChipRow.implicitWidth + 20
                    height: 22

                    Rectangle {
                        anchors.fill: parent
                        radius: height / 2
                        color: modelData.mode === "exclude" ? "#2a1515" : "#152030"
                        border.color: modelData.mode === "exclude" ? "#884444" : "#446688"
                        border.width: 1

                        Row {
                            id: roChipRow
                            anchors {
                                left: parent.left; leftMargin: 8
                                right: parent.right; rightMargin: 8
                                verticalCenter: parent.verticalCenter
                            }
                            spacing: 4

                            Text {
                                text: modelData.mode === "exclude" ? "−" : "+"
                                font.pixelSize: 10
                                color: modelData.mode === "exclude" ? "#cc6666" : "#6699cc"
                                anchors.verticalCenter: parent.verticalCenter
                            }

                            Text {
                                text: modelData.name ?? ""
                                font.pixelSize: Theme.fontSizeSm
                                font.family: Theme.fontFamily
                                color: Theme.text
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                }
            }
        }
    }
}
