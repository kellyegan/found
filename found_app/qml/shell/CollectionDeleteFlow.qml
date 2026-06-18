import QtQuick
import "../components"

// Manages the collection-deletion confirmation dialog.
// Call requestDelete(collectionId, collectionName) to open it.
Item {
    id: root

    readonly property bool open: _collectionId !== ""

    property string _collectionId: ""
    property string _collectionName: ""

    function requestDelete(collectionId, collectionName) {
        _collectionId = collectionId
        _collectionName = collectionName
        confirmDialog.checkboxChecked = false
    }

    ConfirmDialog {
        id: confirmDialog
        objectName: "confirmDialog"
        anchors.fill: parent
        open: root._collectionId !== ""
        message: "Delete the collection “" + root._collectionName + "”? Images in it will not be removed from your library."
        confirmLabel: "Delete"
        onConfirmed: {
            CollectionsState.deleteCollection(root._collectionId)
            root._collectionId = ""
            root._collectionName = ""
        }
        onCancelled: {
            root._collectionId = ""
            root._collectionName = ""
        }
    }
}
