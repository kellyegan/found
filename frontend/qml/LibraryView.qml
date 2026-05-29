import QtQuick

Item {
    id: root

    property string loadingState: "Loading"
    property var gridModel: null
    property bool isFiltered: false

    signal loadMoreRequested()
    signal clearFilterRequested()

    // Keyboard shortcuts — active application-wide, no focus required
    Shortcut {
        sequence: "Escape"
        onActivated: SelectionManager.clear()
    }

    Shortcut {
        sequence: StandardKey.SelectAll
        onActivated: {
            if (root.loadingState === "Ready" && root.gridModel)
                SelectionManager.selectAll(root.gridModel.allIds)
        }
    }

    Shortcut {
        sequence: "Return"
        onActivated: {
            if (SelectionManager.primaryId !== "")
                SelectionManager.requestOpen(SelectionManager.primaryId)
        }
    }

    // Loading
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Loading"
        text: "Loading…"
        font.pixelSize: Theme.fontSizeMd
        font.family: Theme.fontFamily
        color: Theme.textMuted
    }

    // Empty library
    Column {
        anchors.centerIn: parent
        visible: root.loadingState === "Empty"
        spacing: Theme.spacingMd

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "NO IMAGES YET"
            font.pixelSize: Theme.fontSizeLg
            font.weight: Font.Bold
            font.family: Theme.fontFamily
            color: Theme.text
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "DRAG AND DROP HERE TO ADD"
            font.pixelSize: Theme.fontSizeMd
            font.family: Theme.fontFamily
            color: Theme.textMuted
        }
    }

    // "Showing recent import" filter bar
    Rectangle {
        id: filterBar
        anchors { top: parent.top; left: parent.left; right: parent.right }
        height: root.isFiltered ? 40 : 0
        visible: root.isFiltered
        color: "transparent"

        Rectangle {
            anchors { left: parent.left; verticalCenter: parent.verticalCenter; leftMargin: Theme.spacingMd }
            width: filterLabel.implicitWidth + clearBtn.width + Theme.spacingMd * 2 + 8
            height: 28
            radius: 14
            color: Theme.surface

            Text {
                id: filterLabel
                anchors { left: parent.left; verticalCenter: parent.verticalCenter; leftMargin: Theme.spacingMd }
                text: "Showing recent import"
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
                color: Theme.textMuted
            }

            Text {
                id: clearBtn
                anchors { right: parent.right; verticalCenter: parent.verticalCenter; rightMargin: Theme.spacingMd }
                text: "✕"
                font.pixelSize: Theme.fontSizeSm
                font.family: Theme.fontFamily
                color: Theme.textMuted

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.clearFilterRequested()
                }
            }
        }
    }

    // Thumbnail grid
    ThumbnailGrid {
        id: thumbnailGrid
        anchors { top: filterBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
        visible: root.loadingState === "Ready"
        model: root.gridModel
        onLoadMoreRequested: root.loadMoreRequested()
        onScrollXChanged: function(x) { NavigationManager.updateScrollX(x) }
    }

    function scrollToX(x) {
        thumbnailGrid.scrollToX(x)
    }

    // Error
    Text {
        anchors.centerIn: parent
        visible: root.loadingState === "Error"
        text: "Failed to load library."
        font.pixelSize: Theme.fontSizeMd
        font.family: Theme.fontFamily
        color: "#ff4444"
    }
}
