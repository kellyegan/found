import QtQuick

Item {
    id: root

    property string loadingState: "Idle"
    property var pendingFiles: []
    property var conflictFiles: []
    property int duplicateCount: 0
    property int conflictCount: 0
    property int invalidCount: 0
    property int importedCount: 0
    property int skippedCount: 0
    property int errorCount: 0
    property double progress: 0.0

    signal confirmed()
    signal cancelled()
    signal conflictChoiceChanged(string path, string choice)

    visible: loadingState !== "Idle"

    // Backdrop
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.55

        MouseArea {
            anchors.fill: parent
            // Absorb clicks so content beneath isn't interactive
        }
    }

    // Sheet slides up from bottom
    Rectangle {
        id: sheet
        anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
        height: 340
        color: "#1c1c1c"
        radius: 10

        // Rounded top corners only — cover the bottom corners
        Rectangle {
            anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
            height: parent.radius
            color: parent.color
        }

        // ── Scanning ──────────────────────────────────────────────────
        Column {
            anchors.centerIn: parent
            spacing: 12
            visible: root.loadingState === "Scanning"

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Scanning files…"
                color: "#cccccc"
                font.pixelSize: 15
            }
        }

        // ── Previewing ────────────────────────────────────────────────
        Item {
            anchors { fill: parent; margins: 20 }
            visible: root.loadingState === "Previewing"

            Text {
                id: previewTitle
                anchors { top: parent.top; left: parent.left }
                text: root.pendingFiles.length + " file" + (root.pendingFiles.length === 1 ? "" : "s") + " ready to import"
                color: "#ffffff"
                font.pixelSize: 15
                font.weight: Font.Medium
            }

            // Summary chips
            Row {
                id: chipsRow
                anchors { top: previewTitle.bottom; left: parent.left; topMargin: 10 }
                spacing: 8

                Repeater {
                    model: [
                        { label: root.duplicateCount + " duplicate" + (root.duplicateCount === 1 ? "" : "s"), show: root.duplicateCount > 0, color: "#555555" },
                        { label: root.invalidCount + " unsupported", show: root.invalidCount > 0, color: "#663333" },
                    ]
                    delegate: Rectangle {
                        visible: modelData.show
                        height: 22
                        width: chipLabel.width + 16
                        radius: 11
                        color: modelData.color

                        Text {
                            id: chipLabel
                            anchors.centerIn: parent
                            text: modelData.label
                            color: "#cccccc"
                            font.pixelSize: 11
                        }
                    }
                }
            }

            // New files list (only shown when no conflicts need resolving)
            Rectangle {
                id: newFilesList
                anchors { top: chipsRow.bottom; topMargin: 8; left: parent.left; right: parent.right; bottom: buttonRow.top; bottomMargin: 12 }
                visible: root.conflictFiles.length === 0
                color: "#141414"
                radius: 4

                ListView {
                    anchors { fill: parent; margins: 8 }
                    clip: true
                    model: root.pendingFiles
                    delegate: Text {
                        width: parent ? parent.width : 0
                        text: {
                            var parts = modelData.split("/")
                            return parts[parts.length - 1]
                        }
                        color: "#888888"
                        font.pixelSize: 11
                        elide: Text.ElideRight
                    }
                }
            }

            // Conflict resolution list
            Column {
                anchors { top: chipsRow.bottom; topMargin: 8; left: parent.left; right: parent.right; bottom: buttonRow.top; bottomMargin: 12 }
                visible: root.conflictFiles.length > 0
                spacing: 0

                Text {
                    width: parent.width
                    text: root.conflictFiles.length + " conflict" + (root.conflictFiles.length === 1 ? "" : "s") + " — choose how to handle each:"
                    color: "#ccaa44"
                    font.pixelSize: 12
                    bottomPadding: 8
                }

                Rectangle {
                    width: parent.width
                    height: parent.height - 28
                    color: "#141414"
                    radius: 4

                    ListView {
                        anchors { fill: parent; margins: 8 }
                        clip: true
                        model: root.conflictFiles
                        spacing: 8

                        delegate: Item {
                            id: conflictDelegate
                            width: parent ? parent.width : 0
                            height: conflictContent.implicitHeight + 4

                            property string currentChoice: "keep"
                            property string conflictPath: modelData.path || ""

                            Column {
                                id: conflictContent
                                width: parent.width
                                spacing: 2

                                Text {
                                    width: parent.width
                                    text: {
                                        var parts = conflictDelegate.conflictPath.split("/")
                                        return parts[parts.length - 1]
                                    }
                                    color: "#cccccc"
                                    font.pixelSize: 11
                                    elide: Text.ElideRight
                                }

                                Text {
                                    width: parent.width
                                    text: "Existing: " + (modelData.existing_filename || "")
                                    color: "#666666"
                                    font.pixelSize: 10
                                    elide: Text.ElideRight
                                }

                                Row {
                                    spacing: 6
                                    topPadding: 2

                                    Rectangle {
                                        height: 20
                                        width: keepLabel.implicitWidth + 14
                                        radius: 10
                                        color: conflictDelegate.currentChoice === "keep" ? "#885500" : "#2a2a2a"
                                        border.color: conflictDelegate.currentChoice === "keep" ? "#cc8800" : "#444444"
                                        border.width: 1

                                        Text {
                                            id: keepLabel
                                            anchors.centerIn: parent
                                            text: "Keep existing"
                                            color: conflictDelegate.currentChoice === "keep" ? "#ffcc66" : "#888888"
                                            font.pixelSize: 10
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                conflictDelegate.currentChoice = "keep"
                                                root.conflictChoiceChanged(conflictDelegate.conflictPath, "keep")
                                            }
                                        }
                                    }

                                    Rectangle {
                                        height: 20
                                        width: updateLabel.implicitWidth + 14
                                        radius: 10
                                        color: conflictDelegate.currentChoice === "update" ? "#885500" : "#2a2a2a"
                                        border.color: conflictDelegate.currentChoice === "update" ? "#cc8800" : "#444444"
                                        border.width: 1

                                        Text {
                                            id: updateLabel
                                            anchors.centerIn: parent
                                            text: "Update path"
                                            color: conflictDelegate.currentChoice === "update" ? "#ffcc66" : "#888888"
                                            font.pixelSize: 10
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                conflictDelegate.currentChoice = "update"
                                                root.conflictChoiceChanged(conflictDelegate.conflictPath, "update")
                                            }
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
                    width: 80
                    height: 32
                    color: cancelHover.containsMouse ? "#2a2a2a" : "transparent"
                    border.color: "#444444"
                    border.width: 1
                    radius: 4

                    Text {
                        anchors.centerIn: parent
                        text: "Cancel"
                        color: "#888888"
                        font.pixelSize: 13
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
                    color: importHover.containsMouse ? "#2a5a2a" : "#1e4a1e"
                    radius: 4

                    Text {
                        anchors.centerIn: parent
                        text: "Import"
                        color: "#88cc88"
                        font.pixelSize: 13
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
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Importing…"
                color: "#cccccc"
                font.pixelSize: 15
            }

            // Progress track
            Rectangle {
                width: parent.width
                height: 4
                radius: 2
                color: "#333333"

                Rectangle {
                    width: parent.width * root.progress
                    height: parent.height
                    radius: parent.radius
                    color: "#88cc88"

                    Behavior on width { NumberAnimation { duration: 200 } }
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Math.round(root.progress * 100) + "%"
                color: "#666666"
                font.pixelSize: 12
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
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Import complete"
                    color: "#88cc88"
                    font.pixelSize: 16
                    font.weight: Font.Medium
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: root.importedCount + " imported" +
                          (root.skippedCount > 0 ? " · " + root.skippedCount + " skipped" : "") +
                          (root.errorCount > 0 ? " · " + root.errorCount + " failed" : "")
                    color: "#888888"
                    font.pixelSize: 13
                }
            }

            Rectangle {
                anchors { bottom: parent.bottom; right: parent.right }
                width: 80
                height: 32
                color: closeHover.containsMouse ? "#2a2a2a" : "#252525"
                radius: 4

                Text {
                    anchors.centerIn: parent
                    text: "Done"
                    color: "#cccccc"
                    font.pixelSize: 13
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
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Import failed"
                    color: "#cc4444"
                    font.pixelSize: 15
                    font.weight: Font.Medium
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Check your files and try again."
                    color: "#888888"
                    font.pixelSize: 12
                }
            }

            Rectangle {
                anchors { bottom: parent.bottom; right: parent.right }
                width: 80
                height: 32
                color: "#252525"
                radius: 4

                Text {
                    anchors.centerIn: parent
                    text: "Close"
                    color: "#cccccc"
                    font.pixelSize: 13
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: root.cancelled()
                }
            }
        }
    }
}
