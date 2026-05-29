import QtQuick

Item {
    id: root
    anchors.fill: parent

    property string appState: "Launching"
    property string statusMessage: ""
    property bool hasError: false
    property string libraryLoadingState: "Loading"

    SplashScreen {
        anchors.fill: parent
        visible: root.appState !== "Ready"
        statusText: root.statusMessage
        hasError: root.hasError
    }

    LibraryView {
        anchors.fill: parent
        visible: root.appState === "Ready"
        loadingState: root.libraryLoadingState
        gridModel: LibraryState.gridModel
        onLoadMoreRequested: LibraryState.load_more()
    }
}
