from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Property, Signal, Slot


class ThumbnailGridModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    FilenameRole = Qt.UserRole + 2
    ThumbnailUrlRole = Qt.UserRole + 3
    FileStatusRole = Qt.UserRole + 4

    countChanged = Signal(int)
    hasMoreChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[dict] = []
        self._cursor: str | None = None
        self._has_more = False

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._items):
            return None
        item = self._items[index.row()]
        match role:
            case self.IdRole:
                return str(item["id"])
            case self.FilenameRole:
                return item.get("filename", "")
            case self.ThumbnailUrlRole:
                return f"image://thumbnails/{item['id']}"
            case self.FileStatusRole:
                return str(item.get("file_status", "available"))
        return None

    def roleNames(self) -> dict:
        return {
            self.IdRole: b"imageId",
            self.FilenameRole: b"filename",
            self.ThumbnailUrlRole: b"thumbnailUrl",
            self.FileStatusRole: b"fileStatus",
        }

    @Slot(list, object, bool)
    def appendPage(self, items: list[dict], next_cursor: str | None, has_more: bool) -> None:
        if not items:
            return
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row + len(items) - 1)
        self._items.extend(items)
        self._cursor = next_cursor
        self._has_more = has_more
        self.endInsertRows()
        self.countChanged.emit(len(self._items))
        self.hasMoreChanged.emit(has_more)

    @Slot()
    def clear(self) -> None:
        self.beginResetModel()
        self._items.clear()
        self._cursor = None
        self._has_more = False
        self.endResetModel()
        self.countChanged.emit(0)
        self.hasMoreChanged.emit(False)

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)

    @Property(bool, notify=hasMoreChanged)
    def hasMore(self) -> bool:
        return self._has_more

    @Property(str)
    def cursor(self) -> str:
        return self._cursor or ""

    @Property(list, notify=countChanged)
    def allIds(self) -> list:
        return [item["id"] for item in self._items]
