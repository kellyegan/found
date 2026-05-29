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
    context_ids: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "view": self.view,
            "collection_id": self.collection_id,
            "image_id": self.image_id,
            "scroll_x": self.scroll_x,
            "selection_ids": list(self.selection_ids),
            "primary_id": self.primary_id,
            "anchor_id": self.anchor_id,
            "context_ids": list(self.context_ids),
        }


class NavigationManager(QObject):
    navigationChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = NavigationEntry(view="library")
        self._stack: list[NavigationEntry] = []
        self._immersive: bool = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(bool, notify=navigationChanged)
    def canGoBack(self) -> bool:
        return len(self._stack) > 0

    @Property(bool, notify=navigationChanged)
    def hasNext(self) -> bool:
        ids = self._current.context_ids
        img = self._current.image_id
        if not ids or img not in ids:
            return False
        return ids.index(img) < len(ids) - 1

    @Property(bool, notify=navigationChanged)
    def hasPrev(self) -> bool:
        ids = self._current.context_ids
        img = self._current.image_id
        if not ids or img not in ids:
            return False
        return ids.index(img) > 0

    @Property(str, notify=navigationChanged)
    def currentView(self) -> str:
        return self._current.view

    @Property("QVariant", notify=navigationChanged)
    def currentEntry(self) -> dict:
        return self._current.as_dict()

    @Property(bool, notify=navigationChanged)
    def immersiveMode(self) -> bool:
        return self._immersive

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
            context_ids=list(params.get("context_ids") or []),
        )
        self.navigationChanged.emit()

    @Slot()
    def goBack(self) -> None:
        if not self._stack:
            return
        self._immersive = False
        self._current = self._stack.pop()
        self.navigationChanged.emit()

    @Slot()
    def toggleImmersive(self) -> None:
        self._immersive = not self._immersive
        self.navigationChanged.emit()

    @Slot(bool)
    def setImmersive(self, value: bool) -> None:
        if self._immersive != value:
            self._immersive = value
            self.navigationChanged.emit()

    @Slot()
    def goNext(self) -> None:
        ids = self._current.context_ids
        img = self._current.image_id
        if not ids or img not in ids:
            return
        idx = ids.index(img)
        if idx < len(ids) - 1:
            self._current.image_id = ids[idx + 1]
            self.navigationChanged.emit()

    @Slot()
    def goPrev(self) -> None:
        ids = self._current.context_ids
        img = self._current.image_id
        if not ids or img not in ids:
            return
        idx = ids.index(img)
        if idx > 0:
            self._current.image_id = ids[idx - 1]
            self.navigationChanged.emit()

    @Slot(float)
    def updateScrollX(self, x: float) -> None:
        self._current.scroll_x = x

    @Slot(list, str, str)
    def saveSelection(self, selection_ids: list, primary_id: str, anchor_id: str) -> None:
        self._current.selection_ids = list(selection_ids)
        self._current.primary_id = primary_id
        self._current.anchor_id = anchor_id
