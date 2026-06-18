import QtQuick
import QtQuick.Dialogs
import "../components"

// Self-contained file-relocation workflow: handles LibraryState signals for
// locate/prefix-relocation, owns the confirmation dialogs, and the file picker.
Item {
    id: root

    readonly property bool prefixDialogOpen: _prefixAffectedCount > 0
    readonly property bool resultDialogOpen: _relocationResultMessage !== ""

    property string _pendingLocateImageId: ""
    property string _pendingLocatedOldPath: ""
    property int _prefixAffectedCount: 0
    property string _oldPrefix: ""
    property string _newPrefix: ""
    property string _relocationResultMessage: ""

    Connections {
        target: LibraryState
        function onLocateDialogRequested(imageId, imagePath) {
            root._pendingLocateImageId = imageId
            root._pendingLocatedOldPath = imagePath
            locateFileDialog.open()
        }
        function onImageRelocated(imageId, oldPath, newPath) {
            LibraryState.previewRelocation(oldPath, newPath)
        }
        function onRelocationPreviewReady(count, oldPrefix, newPrefix) {
            root._oldPrefix = oldPrefix
            root._newPrefix = newPrefix
            root._prefixAffectedCount = count
        }
        function onRelocationComplete(updated, notFound, conflicts, mismatched) {
            root._prefixAffectedCount = 0
            root._oldPrefix = ""
            root._newPrefix = ""
            var parts = []
            if (updated > 0)
                parts.push(updated + (updated === 1 ? " image relocated." : " images relocated."))
            if (notFound > 0)
                parts.push(notFound + (notFound === 1 ? " file not found at expected path." : " files not found at expected paths."))
            if (conflicts > 0)
                parts.push(conflicts + (conflicts === 1 ? " file already exists at target path." : " files already exist at target paths."))
            if (mismatched > 0)
                parts.push(mismatched + (mismatched === 1 ? " file did not match expected content." : " files did not match expected content."))
            if (updated === 0 && notFound === 0 && conflicts === 0 && mismatched === 0)
                parts.push("No images were relocated.")
            root._relocationResultMessage = parts.join("\n")
        }
    }

    ConfirmDialog {
        anchors.fill: parent
        z: 1
        open: root._prefixAffectedCount > 0
        message: {
            var n = root._prefixAffectedCount
            return "Found " + n + (n === 1 ? " other image" : " other images")
                + " in the same folder. Relocate them all to the new location?"
        }
        confirmLabel: "Relocate All"
        onConfirmed: {
            LibraryState.relocateByPrefix(root._oldPrefix, root._newPrefix)
            root._prefixAffectedCount = 0
        }
        onCancelled: {
            root._prefixAffectedCount = 0
            root._oldPrefix = ""
            root._newPrefix = ""
        }
    }

    ConfirmDialog {
        anchors.fill: parent
        z: 2
        open: root._relocationResultMessage !== ""
        message: root._relocationResultMessage
        confirmLabel: "OK"
        showCancel: false
        onConfirmed: root._relocationResultMessage = ""
    }

    FileDialog {
        id: locateFileDialog
        title: {
            var filename = root._pendingLocatedOldPath.split("/").pop()
            return filename ? "Locate “" + filename + "”" : "Locate file"
        }
        fileMode: FileDialog.OpenFile
        onAccepted: {
            var newPath = selectedFile.toString().replace(/^file:\/\//, "")
            LibraryState.relocateImage(
                root._pendingLocateImageId,
                root._pendingLocatedOldPath,
                newPath
            )
        }
    }
}
