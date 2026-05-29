from PySide6.QtCore import QObject, Property, Signal, Slot


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

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _bump(self) -> None:
        self._revision += 1
        self.selectionChanged.emit()
