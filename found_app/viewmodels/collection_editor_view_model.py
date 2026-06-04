from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot


class CollectionEditorViewModel(QObject):
    collectionsChanged = Signal()
    loadingStateChanged = Signal(str)
    selectionModeChanged = Signal(str)
    modified = Signal()

    def __init__(
        self,
        image_collections_fetcher: Callable,
        collection_adder: Callable,
        collection_remover: Callable,
        selection_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        self._image_collections_fetcher = image_collections_fetcher
        self._collection_adder = collection_adder
        self._collection_remover = collection_remover
        self._selection_manager = selection_manager
        self._collections: list = []
        self._loading_state = "Idle"
        self._selection_mode = "none"
        self._primary_id: str = ""
        self._active_fetch_threads: list = []
        self._active_modify_threads: list = []

        if selection_manager is not None:
            selection_manager.selectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(list, notify=collectionsChanged)
    def collections(self) -> list:
        return list(self._collections)

    @Property(str, notify=loadingStateChanged)
    def loadingState(self) -> str:
        return self._loading_state

    @Property(str, notify=selectionModeChanged)
    def selectionMode(self) -> str:
        return self._selection_mode

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(str)
    def loadImage(self, image_id: str) -> None:
        self._primary_id = image_id
        self._set_state("Loading")
        for t in list(self._active_fetch_threads):
            try:
                t.result.disconnect(self._on_fetch_result)
            except RuntimeError:
                pass
        thread = _FetchThread(self._image_collections_fetcher, image_id)
        thread.result.connect(self._on_fetch_result)
        self._active_fetch_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_fetch_threads.remove(t) if t in self._active_fetch_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str, str)
    def addToCollection(self, collection_id: str, collection_name: str) -> None:
        if self._selection_manager:
            image_ids = list(self._selection_manager.selectedIds)
        elif self._primary_id:
            image_ids = [self._primary_id]
        else:
            return
        if not image_ids:
            return
        thread = _AddThread(self._collection_adder, collection_id, image_ids)
        thread.result.connect(
            lambda ok, _id=collection_id, _name=collection_name: self._on_add_result(ok, _id, _name)
        )
        self._active_modify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_modify_threads.remove(t) if t in self._active_modify_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str)
    def removeFromCollection(self, collection_id: str) -> None:
        if not self._primary_id:
            return
        thread = _RemoveThread(self._collection_remover, collection_id, self._primary_id)
        thread.result.connect(lambda ok, _id=collection_id: self._on_remove_result(ok, _id))
        self._active_modify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_modify_threads.remove(t) if t in self._active_modify_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot()
    def clear(self) -> None:
        self._collections = []
        self._primary_id = ""
        self.collectionsChanged.emit()
        self._set_state("Idle")

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:
        if not self._selection_manager:
            return
        count = self._selection_manager.selectionCount
        if count == 0:
            self._set_selection_mode("none")
            self.clear()
        elif count == 1:
            self._set_selection_mode("single")
            self.loadImage(self._selection_manager.primaryId)
        else:
            self._set_selection_mode("multi")
            self._collections = []
            self._primary_id = ""
            self.collectionsChanged.emit()
            self._set_state("Idle")

    def _on_fetch_result(self, data: list | None) -> None:
        if data is None:
            self._set_state("Error")
            return
        self._collections = list(data)
        self.collectionsChanged.emit()
        self._set_state("Ready")

    def _on_add_result(self, ok: bool, collection_id: str, collection_name: str) -> None:
        if ok:
            self.modified.emit()
            if self._selection_mode != "multi":
                if not any(c["id"] == collection_id for c in self._collections):
                    self._collections.append({"id": collection_id, "name": collection_name})
                    self.collectionsChanged.emit()

    def _on_remove_result(self, ok: bool, collection_id: str) -> None:
        if ok:
            self.modified.emit()
            self._collections = [c for c in self._collections if c["id"] != collection_id]
            self.collectionsChanged.emit()

    def _set_state(self, state: str) -> None:
        self._loading_state = state
        self.loadingStateChanged.emit(state)

    def _set_selection_mode(self, mode: str) -> None:
        if self._selection_mode != mode:
            self._selection_mode = mode
            self.selectionModeChanged.emit(mode)


class _FetchThread(QThread):
    result = Signal(object)

    def __init__(self, fetcher: Callable, image_id: str, parent=None):
        super().__init__(parent)
        self._fetcher = fetcher
        self._image_id = image_id

    def run(self) -> None:
        try:
            self.result.emit(self._fetcher(self._image_id))
        except Exception:
            self.result.emit(None)


class _AddThread(QThread):
    result = Signal(bool)

    def __init__(self, adder: Callable, collection_id: str, image_ids: list, parent=None):
        super().__init__(parent)
        self._adder = adder
        self._collection_id = collection_id
        self._image_ids = image_ids

    def run(self) -> None:
        try:
            ok = self._adder(self._collection_id, self._image_ids)
            self.result.emit(bool(ok))
        except Exception:
            self.result.emit(False)


class _RemoveThread(QThread):
    result = Signal(bool)

    def __init__(self, remover: Callable, collection_id: str, image_id: str, parent=None):
        super().__init__(parent)
        self._remover = remover
        self._collection_id = collection_id
        self._image_id = image_id

    def run(self) -> None:
        try:
            ok = self._remover(self._collection_id, self._image_id)
            self.result.emit(bool(ok))
        except Exception:
            self.result.emit(False)
