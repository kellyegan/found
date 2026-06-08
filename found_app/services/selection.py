from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QJSValue


class SelectionManager(QObject):
    selectionChanged = Signal()
    openRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected: set[str] = set()
        self._primary: str = ""
        self._anchor: str = ""
        self._revision: int = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(int, notify=selectionChanged)
    def selectionRevision(self) -> int:
        return self._revision

    @Property(int, notify=selectionChanged)
    def selectionCount(self) -> int:
        return len(self._selected)

    @Property(str, notify=selectionChanged)
    def primaryId(self) -> str:
        return self._primary

    @Property(str, notify=selectionChanged)
    def anchorId(self) -> str:
        return self._anchor

    @Property(list, notify=selectionChanged)
    def selectedIds(self) -> list:
        return list(self._selected)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(str)
    def select(self, image_id: str) -> None:
        self._selected = {image_id}
        self._primary = image_id
        self._anchor = image_id
        self._bump()

    @Slot(str)
    def toggle(self, image_id: str) -> None:
        if image_id in self._selected:
            self._selected.discard(image_id)
            if self._primary == image_id:
                self._primary = next(iter(self._selected), "")
        else:
            self._selected.add(image_id)
            self._primary = image_id
            self._anchor = image_id
        self._bump()

    @Slot(str, list)
    def extendTo(self, image_id: str, all_ids: list) -> None:
        if not self._anchor or self._anchor not in all_ids or image_id not in all_ids:
            self.select(image_id)
            return
        anchor_idx = all_ids.index(self._anchor)
        target_idx = all_ids.index(image_id)
        start = min(anchor_idx, target_idx)
        end = max(anchor_idx, target_idx) + 1
        self._selected = set(all_ids[start:end])
        self._primary = image_id
        self._bump()

    @Slot(list)
    def selectAll(self, all_ids: list) -> None:
        self._selected = set(all_ids)
        self._primary = all_ids[-1] if all_ids else ""
        self._anchor = all_ids[0] if all_ids else ""
        self._bump()

    @Slot()
    def clear(self) -> None:
        self._selected.clear()
        self._primary = ""
        self._anchor = ""
        self._bump()

    @Slot(str, result=bool)
    def isSelected(self, image_id: str) -> bool:
        return image_id in self._selected

    @Slot(str)
    def requestOpen(self, image_id: str) -> None:
        self.openRequested.emit(image_id)

    @Slot(str, list, int)
    def navigateInGrid(self, direction: str, all_ids: list, row_count: int) -> None:
        if not all_ids or row_count <= 0:
            return
        if self._primary not in all_ids:
            self.select(all_ids[0])
            return
        idx = all_ids.index(self._primary)
        count = len(all_ids)
        row = idx % row_count
        col = idx // row_count
        new_idx = idx
        if direction == "up":
            if row > 0:
                new_idx = idx - 1
        elif direction == "down":
            if row < row_count - 1 and idx + 1 < count:
                new_idx = idx + 1
        elif direction == "left":
            if col > 0:
                new_idx = (col - 1) * row_count + row
        elif direction == "right":
            next_col_start = (col + 1) * row_count
            if next_col_start < count:
                new_idx = min(next_col_start + row, count - 1)
        if new_idx != idx:
            self.select(all_ids[new_idx])

    @Slot("QVariant", str, str)
    def restore(self, selection_ids, primary_id: str, anchor_id: str) -> None:
        if isinstance(selection_ids, QJSValue):
            selection_ids = selection_ids.toVariant() or []
        self._selected = set(selection_ids or [])
        self._primary = primary_id
        self._anchor = anchor_id
        self._bump()


    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _bump(self) -> None:
        self._revision += 1
        self.selectionChanged.emit()
