import QtQuick

Item {
    id: root
    anchors.fill: parent

    property string appState: "Launching"

    SplashScreen {
        anchors.fill: parent
        visible: root.appState !== "Ready"
    }

    // LibraryView placeholder — replaced in Commit 9
    Item {
        anchors.fill: parent
        visible: root.appState === "Ready"
    }
}
