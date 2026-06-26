import QtQuick
import Found.Theme 1.0

// Window-level strip housing all EdgeTabs at high z-value.
// Owns toggle and layout requests so tabs are never clipped by panel bodies.
Item {
    id: root

    // Panel IDs whose tabs should be rendered in this strip.
    property var availablePanels: []

    // Total tab count (left + right), exposed for tests.
    readonly property int tabCount: _leftRepeater.count + _rightRepeater.count

    // Left-edge tabs ordered by PanelLayout.order
    Column {
        id: leftCol
        anchors { left: parent.left; verticalCenter: parent.verticalCenter }
        spacing: 8

        Repeater {
            id: _leftRepeater
            model: {
                if (!PanelLayout || !PanelLayout.order || !PanelLayout.edges) return []
                return PanelLayout.order.filter(function(p) {
                    return PanelLayout.edges[p] === "left"
                        && root.availablePanels.indexOf(p) >= 0
                })
            }

            delegate: EdgeTab {
                panelId: modelData
                edge: "left"
                icon: root._iconFor(modelData)
                dragOpenKeys: root._dragKeysFor(modelData)
                open: PanelLayout && PanelLayout.openPanels
                      ? PanelLayout.openPanels["left"] === panelId : false
                onToggleRequested: if (PanelLayout) PanelLayout.togglePanel(panelId)
                onLayoutRequested: function(targetEdge, targetSideIndex) {
                    if (PanelLayout) PanelLayout.setLayout(panelId, targetEdge, targetSideIndex)
                }
            }
        }
    }

    // Right-edge tabs ordered by PanelLayout.order
    Column {
        id: rightCol
        anchors { right: parent.right; verticalCenter: parent.verticalCenter }
        spacing: 8

        Repeater {
            id: _rightRepeater
            model: {
                if (!PanelLayout || !PanelLayout.order || !PanelLayout.edges) return []
                return PanelLayout.order.filter(function(p) {
                    return PanelLayout.edges[p] === "right"
                        && root.availablePanels.indexOf(p) >= 0
                })
            }

            delegate: EdgeTab {
                panelId: modelData
                edge: "right"
                icon: root._iconFor(modelData)
                dragOpenKeys: root._dragKeysFor(modelData)
                open: PanelLayout && PanelLayout.openPanels
                      ? PanelLayout.openPanels["right"] === panelId : false
                onToggleRequested: if (PanelLayout) PanelLayout.togglePanel(panelId)
                onLayoutRequested: function(targetEdge, targetSideIndex) {
                    if (PanelLayout) PanelLayout.setLayout(panelId, targetEdge, targetSideIndex)
                }
            }
        }
    }

    function _iconFor(panelId) {
        var icons = { "collections": "☰", "metadata": "ⓘ" }
        return icons[panelId] || ""
    }

    function _dragKeysFor(panelId) {
        var keys = { "collections": ["found/image"] }
        return keys[panelId] || []
    }
}
