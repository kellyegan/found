from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtCore import QObject, Property, Signal, Slot


@dataclass
class NavigationEntry:
    view: str
    collection_id: Optional[str] = None
    image_id: Optional[str] = None
    scroll_x: float = 0.0
    selection_ids: list = field(default_factory=list)
    primary_id: str = ""
    anchor_id: str = ""

    def as_dict(self) -> dict:
        return {
            "view": self.view,
            "collection_id": self.collection_id,
            "image_id": self.image_id,
            "scroll_x": self.scroll_x,
            "selection_ids": list(self.selection_ids),
            "primary_id": self.primary_id,
            "anchor_id": self.anchor_id,
        }


class NavigationManager(QObject):
    navigationChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = NavigationEntry(view="library")
        self._stack: list[NavigationEntry] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(bool, notify=navigationChanged)
    def canGoBack(self) -> bool:
        return len(self._stack) > 0

    @Property(str, notify=navigationChanged)
    def currentView(self) -> str:
        return self._current.view

    @Property("QVariant", notify=navigationChanged)
    def currentEntry(self) -> dict:
        return self._current.as_dict()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(str, "QVariant")
    def push(self, view: str, params: dict = None) -> None:
        self._stack.append(self._current)
        params = params or {}
        self._current = NavigationEntry(
            view=view,
            image_id=params.get("image_id"),
            collection_id=params.get("collection_id"),
        )
        self.navigationChanged.emit()

    @Slot()
    def goBack(self) -> None:
        if not self._stack:
            return
        self._current = self._stack.pop()
        self.navigationChanged.emit()

    @Slot(float)
    def updateScrollX(self, x: float) -> None:
        self._current.scroll_x = x

    @Slot(list, str, str)
    def saveSelection(self, selection_ids: list, primary_id: str, anchor_id: str) -> None:
        self._current.selection_ids = list(selection_ids)
        self._current.primary_id = primary_id
        self._current.anchor_id = anchor_id
