import QtQuick

Item {
    id: root

    property var model: null
    property int targetThumbnailSize: 180
    property int tileGap: 20
    property int gridEdgeMargin: 40
    property bool leftPanelOpen: false
    property bool rightPanelOpen: false
    readonly property real scrollX: grid.contentX

    signal loadMoreRequested()

    function scrollToX(x) {
        grid.contentX = x
    }

    GridView {
        id: grid
        anchors {
            fill: parent
            topMargin: Theme.spacingMd
            bottomMargin: Theme.spacingMd
        }
        leftMargin: root.leftPanelOpen ? Theme.overlayWidth : root.gridEdgeMargin
        rightMargin: root.rightPanelOpen ? Theme.overlayWidth : root.gridEdgeMargin
        model: root.model

        // Horizontal multi-row layout: items fill top-to-bottom, columns flow left-to-right
        flow: GridView.FlowTopToBottom

        // Row count derived from viewport height and target thumbnail size (spec §5.2)
        readonly property int rowCount: height > 0
            ? Math.max(2, Math.round(height / root.targetThumbnailSize))
            : 2
        readonly property real tileSize: height > 0 ? height / rowCount : root.targetThumbnailSize

        cellWidth: tileSize
        cellHeight: tileSize

        clip: true
        boundsBehavior: Flickable.StopAtBounds

        // Convert vertical mouse-wheel to horizontal scroll; trackpad horizontal swipe
        // is already handled by the Flickable natively.
        WheelHandler {
            target: null
            onWheel: function(event) {
                if (event.angleDelta.y !== 0 && event.angleDelta.x === 0) {
                    var delta = -event.angleDelta.y / 120 * 80
                    var minX = -grid.leftMargin
                    var maxX = Math.max(minX, grid.contentWidth - grid.width + grid.rightMargin)
                    grid.contentX = Math.max(minX, Math.min(grid.contentX + delta, maxX))
                    event.accepted = true
                }
            }
        }

        delegate: ThumbnailTile {
            width: grid.cellWidth
            height: grid.cellHeight
            inset: root.tileGap / 2
            imageId: model.imageId ?? ""
            thumbnailUrl: model.thumbnailUrl ?? ""
            fileStatus: model.fileStatus ?? "available"
            selected: {
                var _rev = SelectionManager.selectionRevision
                return SelectionManager.isSelected(model.imageId ?? "")
            }
            onTileClicked: function(id, mods) {
                if (mods & Qt.ControlModifier)
                    SelectionManager.toggle(id)
                else if (mods & Qt.ShiftModifier)
                    SelectionManager.extendTo(id, root.model ? root.model.allIds : [])
                else
                    SelectionManager.select(id)
            }
            onTileDoubleClicked: function(id) {
                SelectionManager.requestOpen(id)
            }
        }

        // Trigger incremental load when right edge of content is within 3 viewport-widths
        onContentXChanged: _checkLoadMore()
        onCountChanged: _checkLoadMore()

        function _checkLoadMore() {
            if (!root.model || !root.model.hasMore) return
            var distanceToEnd = grid.contentWidth - grid.rightMargin - (grid.contentX + grid.width)
            if (distanceToEnd < grid.width * 3) {
                root.loadMoreRequested()
            }
        }
    }
}
