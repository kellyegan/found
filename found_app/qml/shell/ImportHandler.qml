import QtQuick
import Found.Theme 1.0
import "../components"
import "../primitives"

// Self-contained import workflow: drop-to-import area, deferred scan timer,
// and the import-panel overlay. Anchor this item to the zone the drop should
// cover; its children fill it.
Item {
    id: root

    // Deferred scan: show the modal immediately on drop, then build paths and
    // scan on the next event-loop tick so QML has one cycle to paint first.
    Timer {
        id: scanTimer
        interval: 0
        repeat: false
        property var pendingUrls: null
        onTriggered: {
            if (!pendingUrls) return
            var paths = []
            for (var i = 0; i < pendingUrls.length; i++) {
                paths.push(pendingUrls[i].toString().replace(/^file:\/\//, ""))
            }
            ImportState.scanPaths(paths)
            pendingUrls = null
        }
    }

    DropArea {
        anchors.fill: parent

        onEntered: function(drag) {
            drag.accepted = drag.hasUrls
        }

        onDropped: function(drop) {
            if (!drop.hasUrls) return
            ImportState.prepareImport(drop.urls.length)
            scanTimer.pendingUrls = drop.urls
            scanTimer.restart()
        }

        Rectangle {
            objectName: "dragHighlight"
            anchors.fill: parent
            color: Theme.text
            opacity: parent.containsDrag ? 0.08 : 0.0
            visible: opacity > 0

            Behavior on opacity { NumberAnimation { duration: 100 } }

            AppText {
                objectName: "dropHintText"
                anchors.centerIn: parent
                visible: parent.parent.containsDrag
                text: "Drop to import"
                variant: "heading"
                font.weight: Font.Medium
            }
        }
    }

    ImportPanel {
        anchors.fill: parent
        z: 30
        loadingState: ImportState.loadingState
        scanTotal: ImportState.scanTotal
        pendingFiles: ImportState.pendingFiles
        alreadyImportedFiles: ImportState.duplicateFiles
        conflictFiles: ImportState.conflictFiles
        invalidCount: ImportState.invalidFiles.length
        importedCount: ImportState.importedCount
        updatedCount: ImportState.updatedCount
        skippedCount: ImportState.skippedCount
        errorCount: ImportState.errorCount
        progress: ImportState.progress

        onConfirmed: ImportState.executeImport()
        onCancelled: ImportState.cancel()
        onConflictChoiceChanged: function(path, choice) {
            ImportState.setConflictChoice(path, choice)
        }
    }
}
