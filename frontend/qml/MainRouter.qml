import QtQuick

Item {
    id: root
    anchors.fill: parent

    property string appState: "Launching"
    property string statusMessage: ""
    property bool hasError: false

    SplashScreen {
        anchors.fill: parent
        visible: root.appState !== "Ready"
        statusText: root.statusMessage
        hasError: root.hasError
    }

    // LibraryView placeholder — replaced in Commit 9
    Item {
        anchors.fill: parent
        visible: root.appState === "Ready"
    }
}
