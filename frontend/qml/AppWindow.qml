import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: root
    width: 1280
    height: 800
    minimumWidth: 800
    minimumHeight: 600
    visible: true
    color: Theme.background
    title: "Found"

    MainRouter {
        anchors.fill: parent
        appState: "Launching"
    }
}
