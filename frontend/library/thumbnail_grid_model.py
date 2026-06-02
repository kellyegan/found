from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Property, Signal, Slot


class ThumbnailGridModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    FilenameRole = Qt.UserRole + 2
    ThumbnailUrlRole = Qt.UserRole + 3
    FileStatusRole = Qt.UserRole + 4

    countChanged = Signal(int)
    hasMoreChanged = Signal(bool)
    missingCountChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[dict] = []
        self._cursor: str | None = None
        self._has_more = False
        self._missing_count = 0

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
        new_missing = sum(1 for it in items if it.get("file_status") == "missing")
        self.beginInsertRows(QModelIndex(), row, row + len(items) - 1)
        self._items.extend(items)
        self._cursor = next_cursor
        self._has_more = has_more
        self._missing_count += new_missing
        self.endInsertRows()
        self.countChanged.emit(len(self._items))
        self.hasMoreChanged.emit(has_more)
        if new_missing:
            self.missingCountChanged.emit(self._missing_count)

    @Slot()
    def clear(self) -> None:
        prev_missing = self._missing_count
        self.beginResetModel()
        self._items.clear()
        self._cursor = None
        self._has_more = False
        self._missing_count = 0
        self.endResetModel()
        self.countChanged.emit(0)
        self.hasMoreChanged.emit(False)
        if prev_missing:
            self.missingCountChanged.emit(0)

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)

    @Property(bool, notify=hasMoreChanged)
    def hasMore(self) -> bool:
        return self._has_more

    @Property(str)
    def cursor(self) -> str:
        return self._cursor or ""

    @Property(int, notify=missingCountChanged)
    def missingCount(self) -> int:
        return self._missing_count

    @Property(list, notify=countChanged)
    def allIds(self) -> list:
        return [item["id"] for item in self._items]
