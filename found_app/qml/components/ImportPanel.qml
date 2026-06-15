import QtQuick
import QtQuick.Controls
import Found.Theme 1.0

Item {
    id: root

    property string loadingState: "Idle"
    property int scanTotal: 0
    property var pendingFiles: []
    property var alreadyImportedFiles: []
    property var conflictFiles: []
    property int invalidCount: 0
    property int importedCount: 0
    property int updatedCount: 0
    property int skippedCount: 0
    property int errorCount: 0
    property double progress: 0.0

    signal confirmed()
    signal cancelled()
    signal conflictChoiceChanged(string path, string choice)

    visible: loadingState !== "Idle"

    // Backdrop
    Rectangle {
        objectName: "backdrop"
        anchors.fill: parent
        color: Theme.background
        opacity: 0.55

        MouseArea {
            anchors.fill: parent
            // Absorb clicks so content beneath isn't interactive
        }
    }

    // Centered modal
    Rectangle {
        id: sheet
        objectName: "sheet"
        anchors.centerIn: parent
        width: Math.min(parent.width - 80, 680)
        height: root.loadingState === "Previewing"
                ? Math.min(parent.height - 80, 560)
                : 180
        color: Theme.surface
        radius: 10

        // ── Scanning ──────────────────────────────────────────────────
        Column {
            anchors.centerIn: parent
            spacing: 16
            visible: root.loadingState === "Scanning"
            width: parent.width - 80

            Text {
                objectName: "scanText"
                anchors.horizontalCenter: parent.horizontalCenter
                text: root.scanTotal > 0
                      ? "Evaluating " + root.scanTotal + " " + (root.scanTotal === 1 ? "item" : "items") + " for import…"
                      : "Evaluating files for import…"
                color: Theme.text
                font.pixelSize: Theme.fontSizeMd
            }

            Rectangle {
                id: scanTrack
                objectName: "scanTrack"
                width: parent.width
                height: 4
                radius: 2
                color: Theme.border
                clip: true

                Rectangle {
                    id: scanBar
                    objectName: "scanBar"
                    width: scanTrack.width * 0.35
                    height: scanTrack.height
                    radius: scanTrack.radius
                    color: Theme.success

                    SequentialAnimation on x {
                        loops: Animation.Infinite
                        running: root.loadingState === "Scanning"
                        NumberAnimation {
                            from: -scanBar.width
                            to: scanTrack.width
                            duration: 1200
                            easing.type: Easing.InOutSine
                        }
                    }
                }
            }
        }

        // ── Previewing ────────────────────────────────────────────────
        Item {
            anchors { fill: parent; margins: 20 }
            visible: root.loadingState === "Previewing"

            Flickable {
                id: previewScroll
                anchors { top: parent.top; left: parent.left; right: parent.right; bottom: buttonRow.top; bottomMargin: 12 }
                contentWidth: width
                contentHeight: previewColumn.implicitHeight
                clip: true

                Column {
                    id: previewColumn
                    width: previewScroll.width
                    spacing: 20

                    // Already in library section
                    Column {
                        width: parent.width
                        spacing: 8
                        visible: root.alreadyImportedFiles.length > 0

                        Text {
                            objectName: "alreadyImportedText"
                            text: root.alreadyImportedFiles.length + " image" + (root.alreadyImportedFiles.length === 1 ? "" : "s") + " already in library, skipping."
                            color: Theme.textMuted
                            font.pixelSize: Theme.fontSizeSm
                        }

                        ListView {
                            width: parent.width
                            height: 60
                            orientation: ListView.Horizontal
                            spacing: 4
                            clip: true
                            model: root.alreadyImportedFiles
                            delegate: Rectangle {
                                required property var modelData
                                width: 60; height: 60
                                color: Theme.surface
                                radius: 3
                                clip: true
                                Image {
                                    anchors.fill: parent
                                    source: parent.modelData && parent.modelData.image_id
                                            ? "image://thumbnails/" + parent.modelData.image_id
                                            : ""
                                    fillMode: Image.PreserveAspectCrop
                                }
                            }
                        }
                    }

                    // Ready to import section
                    Column {
                        width: parent.width
                        spacing: 8
                        visible: root.pendingFiles.length > 0

                        Text {
                            objectName: "pendingText"
                            text: root.pendingFiles.length + " image" + (root.pendingFiles.length === 1 ? "" : "s") + " ready to import"
                            color: Theme.text
                            font.pixelSize: Theme.fontSizeSm
                            font.weight: Font.Medium
                        }

                        ListView {
                            width: parent.width
                            height: 60
                            orientation: ListView.Horizontal
                            spacing: 4
                            clip: true
                            model: root.pendingFiles
                            delegate: Rectangle {
                                required property var modelData
                                width: 60; height: 60
                                color: Theme.surface
                                radius: 3
                                clip: true

                                Image {
                                    id: pendingPreview
                                    anchors.fill: parent
                                    source: parent.modelData ? "file://" + parent.modelData : ""
                                    fillMode: Image.PreserveAspectCrop
                                    // Load in a Qt background thread so large files never
                                    // stall the render loop. sourceSize hints Qt to scale
                                    // while reading (effective for JPEG; no-op for TIFF).
                                    asynchronous: true
                                    sourceSize.width: 60
                                    sourceSize.height: 60
                                }

                                // Shown when Qt rejects the file (e.g. very large TIFF).
                                // The image will still import; this tile just can't preview it.
                                Text {
                                    anchors.centerIn: parent
                                    visible: pendingPreview.status === Image.Error
                                    text: "…"
                                    color: Theme.textMuted
                                    font.pixelSize: Theme.fontSizeMd
                                }
                            }
                        }
                    }

                    // Duplicates section
                    Column {
                        width: parent.width
                        spacing: 12
                        visible: root.conflictFiles.length > 0

                        Text {
                            objectName: "duplicatesHeaderText"
                            text: "These images are duplicates"
                            color: Theme.error
                            font.pixelSize: Theme.fontSizeSm
                            font.weight: Font.Medium
                        }

                        Repeater {
                            id: conflictRepeater
                            model: root.conflictFiles
                            delegate: Row {
                                id: conflictItem
                                width: parent.width
                                spacing: 12
                                property string currentChoice: "keep"
                                property var conflict: modelData

                                // Thumbnail of existing library image
                                Rectangle {
                                    width: 56; height: 56
                                    color: Theme.surface
                                    radius: 3
                                    clip: true
                                    Image {
                                        anchors.fill: parent
                                        source: conflictItem.conflict.existing_image_id ? "image://thumbnails/" + conflictItem.conflict.existing_image_id : ""
                                        fillMode: Image.PreserveAspectCrop
                                    }
                                }

                                // Keep / Replace options
                                Column {
                                    spacing: 8
                                    width: parent.width - 68
                                    anchors.verticalCenter: parent.verticalCenter

                                    Row {
                                        spacing: 8
                                        Rectangle {
                                            id: keepRadio
                                            objectName: "keepRadio"
                                            property alias borderColor: keepRadio.border.color
                                            width: 14; height: 14
                                            radius: 7
                                            anchors.verticalCenter: parent.verticalCenter
                                            color: conflictItem.currentChoice === "keep" ? Theme.error : "transparent"
                                            border.color: conflictItem.currentChoice === "keep" ? Theme.error : Theme.border
                                            border.width: 1
                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: {
                                                    conflictItem.currentChoice = "keep"
                                                    root.conflictChoiceChanged(conflictItem.conflict.path, "keep")
                                                }
                                            }
                                        }
                                        Text {
                                            objectName: "keepLabel"
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "Keep \"" + (conflictItem.conflict.existing_path || "") + "\""
                                            color: conflictItem.currentChoice === "keep" ? Theme.text : Theme.textMuted
                                            font.pixelSize: Theme.fontSizeSm
                                            elide: Text.ElideMiddle
                                            width: parent.parent.width - 22
                                        }
                                    }

                                    Row {
                                        spacing: 8
                                        Rectangle {
                                            id: replaceRadio
                                            objectName: "replaceRadio"
                                            property alias borderColor: replaceRadio.border.color
                                            width: 14; height: 14
                                            radius: 7
                                            anchors.verticalCenter: parent.verticalCenter
                                            color: conflictItem.currentChoice === "update" ? Theme.error : "transparent"
                                            border.color: conflictItem.currentChoice === "update" ? Theme.error : Theme.border
                                            border.width: 1
                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: {
                                                    conflictItem.currentChoice = "update"
                                                    root.conflictChoiceChanged(conflictItem.conflict.path, "update")
                                                }
                                            }
                                        }
                                        Text {
                                            objectName: "replaceLabel"
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "Replace with \"" + (conflictItem.conflict.path || "") + "\""
                                            color: conflictItem.currentChoice === "update" ? Theme.text : Theme.textMuted
                                            font.pixelSize: Theme.fontSizeSm
                                            elide: Text.ElideMiddle
                                            width: parent.parent.width - 22
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Row {
                id: buttonRow
                anchors { bottom: parent.bottom; right: parent.right }
                spacing: 10

                Rectangle {
                    id: cancelBtn
                    objectName: "cancelBtn"
                    property alias borderColor: cancelBtn.border.color
                    width: 80
                    height: 32
                    color: cancelHover.containsMouse ? Theme.border : "transparent"
                    border.color: Theme.border
                    border.width: 1
                    radius: 4

                    Text {
                        objectName: "cancelBtnText"
                        anchors.centerIn: parent
                        text: "Cancel"
                        color: Theme.textMuted
                        font.pixelSize: Theme.fontSizeSm
                    }

                    MouseArea {
                        id: cancelHover
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.cancelled()
                    }
                }

                Rectangle {
                    width: 80
                    height: 32
                    color: Qt.tint(Theme.surface, Qt.rgba(0, 1, 0, importHover.containsMouse ? 0.35 : 0.25))
                    radius: 4

                    Text {
                        objectName: "importBtnText"
                        anchors.centerIn: parent
                        text: "Import"
                        color: Theme.success
                        font.pixelSize: Theme.fontSizeSm
                        font.weight: Font.Medium
                    }

                    MouseArea {
                        id: importHover
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.confirmed()
                    }
                }
            }
        }

        // ── Importing ─────────────────────────────────────────────────
        Column {
            anchors.centerIn: parent
            spacing: 16
            visible: root.loadingState === "Importing"
            width: parent.width - 80

            Text {
                objectName: "importingText"
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Importing…"
                color: Theme.text
                font.pixelSize: Theme.fontSizeMd
            }

            Rectangle {
                id: importingTrack
                objectName: "importingTrack"
                width: parent.width
                height: 4
                radius: 2
                color: Theme.border

                Rectangle {
                    id: importingBar
                    objectName: "importingBar"
                    width: parent.width * root.progress
                    height: parent.height
                    radius: parent.radius
                    color: Theme.success

                    Behavior on width { NumberAnimation { duration: 200 } }
                }
            }

            Text {
                objectName: "importingPercentText"
                anchors.horizontalCenter: parent.horizontalCenter
                text: Math.round(root.progress * 100) + "%"
                color: Theme.textMuted
                font.pixelSize: Theme.fontSizeSm
            }
        }

        // ── Complete ──────────────────────────────────────────────────
        Item {
            anchors { fill: parent; margins: 24 }
            visible: root.loadingState === "Complete"

            Column {
                anchors.centerIn: parent
                spacing: 8

                Text {
                    objectName: "completeTitle"
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Import complete"
                    color: Theme.success
                    font.pixelSize: Theme.fontSizeMd
                    font.weight: Font.Medium
                }

                Text {
                    objectName: "completeSummaryText"
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: {
                        var parts = [root.importedCount + " imported"]
                        if (root.updatedCount > 0) parts.push(root.updatedCount + " updated")
                        if (root.skippedCount > 0) parts.push(root.skippedCount + " skipped")
                        if (root.errorCount > 0) parts.push(root.errorCount + " failed")
                        return parts.join(" · ")
                    }
                    color: Theme.textMuted
                    font.pixelSize: Theme.fontSizeSm
                }
            }

            Rectangle {
                objectName: "doneBtn"
                anchors { bottom: parent.bottom; right: parent.right }
                width: 80
                height: 32
                color: closeHover.containsMouse ? Theme.border : Theme.surface
                radius: 4

                Text {
                    objectName: "doneBtnText"
                    anchors.centerIn: parent
                    text: "Done"
                    color: Theme.text
                    font.pixelSize: Theme.fontSizeSm
                }

                MouseArea {
                    id: closeHover
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: root.cancelled()
                }
            }
        }

        // ── Error ─────────────────────────────────────────────────────
        Item {
            anchors { fill: parent; margins: 24 }
            visible: root.loadingState === "Error"

            Column {
                anchors.centerIn: parent
                spacing: 8

                Text {
                    objectName: "errorTitle"
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Import failed"
                    color: Theme.warning
                    font.pixelSize: Theme.fontSizeMd
                    font.weight: Font.Medium
                }

                Text {
                    objectName: "errorSubtext"
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Check your files and try again."
                    color: Theme.textMuted
                    font.pixelSize: Theme.fontSizeSm
                }
            }

            Rectangle {
                objectName: "closeBtn"
                anchors { bottom: parent.bottom; right: parent.right }
                width: 80
                height: 32
                color: Theme.surface
                radius: 4

                Text {
                    objectName: "closeBtnText"
                    anchors.centerIn: parent
                    text: "Close"
                    color: Theme.text
                    font.pixelSize: Theme.fontSizeSm
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: root.cancelled()
                }
            }
        }
    }
}
