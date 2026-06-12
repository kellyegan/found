import QtQuick
import QtQuick.Controls
import QtQuick.Window
import Found.Theme 1.0

ApplicationWindow {
    id: root
    width: 1280
    height: 800
    minimumWidth: 800
    minimumHeight: 600
    visible: true
    color: Theme.background
    title: "Found"

    // Toggle fullscreen with immersive mode
    visibility: NavigationManager.immersiveMode ? Window.FullScreen : Window.Windowed

    MainRouter {
        anchors.fill: parent
        appState: AppState.stateName
        statusMessage: AppState.statusMessage
        hasError: AppState.hasError
        libraryLoadingState: LibraryState.loadingState
    }
}
