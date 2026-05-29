import QtQuick

Item {
    id: root

    property var model: null
    property int targetThumbnailSize: 180

    signal loadMoreRequested()

    GridView {
        id: grid
        anchors.fill: parent
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

        delegate: ThumbnailTile {
            width: grid.cellWidth
            height: grid.cellHeight
            thumbnailUrl: model.thumbnailUrl ?? ""
            fileStatus: model.fileStatus ?? "available"
        }

        // Trigger incremental load when right edge of content is within 3 viewport-widths
        onContentXChanged: _checkLoadMore()
        onCountChanged: _checkLoadMore()

        function _checkLoadMore() {
            if (!root.model || !root.model.hasMore) return
            var distanceToEnd = grid.contentWidth - grid.contentX - grid.width
            if (distanceToEnd < grid.width * 3) {
                root.loadMoreRequested()
            }
        }
    }
}
