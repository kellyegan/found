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
    signal removeRequested(string imageId, string filename)
    signal locateRequested(string imageId)
    signal viewportVerifyRequested(var imageIds)

    property var _pendingMissingIds: []

    function _queueMissingVerify(imageId) {
        if (!imageId || root._pendingMissingIds.indexOf(imageId) !== -1) return
        root._pendingMissingIds.push(imageId)
        missingVerifyTimer.restart()
    }

    // Debounce viewport-entry verification so a fast scroll through many
    // missing tiles results in one batched check, not one per tile.
    Timer {
        id: missingVerifyTimer
        interval: 600
        repeat: false
        onTriggered: {
            if (root._pendingMissingIds.length > 0) {
                root.viewportVerifyRequested(root._pendingMissingIds)
                root._pendingMissingIds = []
            }
        }
    }

    function scrollToX(x) {
        grid.contentX = x
    }

    function navigateActive(direction) {
        if (!root.model) return
        var ids = root.model.allIds
        SelectionManager.navigateInGrid(direction, ids, grid.rowCount)
        var newIdx = ids.indexOf(SelectionManager.primaryId)
        if (newIdx >= 0) scrollToIndexAnimated(newIdx)
    }

    // Scroll to idx with a smooth animation. Uses positionViewAtIndex to
    // compute the target contentX, then animates from the current position.
    function scrollToIndexAnimated(idx) {
        if (idx < 0 || !root.model) return
        var fromX = grid.contentX
        grid.positionViewAtIndex(idx, GridView.Contain)
        var toX = grid.contentX
        if (Math.abs(toX - fromX) < 1) return
        grid.contentX = fromX
        scrollAnim.from = fromX
        scrollAnim.to = toX
        scrollAnim.restart()
    }

    NumberAnimation {
        id: scrollAnim
        target: grid
        property: "contentX"
        duration: 350
        easing.type: Easing.InOutCubic
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
            active: {
                var _rev = SelectionManager.selectionRevision
                return SelectionManager.primaryId === (model.imageId ?? "")
            }
            onTileClicked: function(id, mods) {
                if (mods & Qt.ControlModifier)
                    SelectionManager.toggle(id)
                else if (mods & Qt.ShiftModifier)
                    SelectionManager.extendTo(id, root.model ? root.model.allIds : [], grid.rowCount)
                else
                    SelectionManager.select(id)
            }
            onTileDoubleClicked: function(id) {
                SelectionManager.requestOpen(id)
            }
            onRemoveRequested: function(id) {
                root.removeRequested(id, model.filename ?? "")
            }
            onLocateRequested: function(id) { root.locateRequested(id) }

            Component.onCompleted: {
                if ((model.fileStatus ?? "available") === "missing") {
                    root._queueMissingVerify(model.imageId ?? "")
                }
            }
        }

        // Tap on any empty area (margins, space past last row) clears selection.
        // indexAt uses content coordinates; TapHandler fires even when a tile
        // MouseArea handles the same tap, so the index check is required.
        TapHandler {
            onTapped: function(eventPoint) {
                var cx = eventPoint.position.x + grid.contentX
                var cy = eventPoint.position.y + grid.contentY
                if (grid.indexAt(cx, cy) < 0)
                    SelectionManager.clear()
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
