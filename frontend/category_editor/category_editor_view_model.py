from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot


class CategoryEditorViewModel(QObject):
    categoriesChanged = Signal()
    loadingStateChanged = Signal(str)
    selectionModeChanged = Signal(str)

    def __init__(
        self,
        image_categories_fetcher: Callable,
        category_modifier: Callable,
        selection_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        self._image_categories_fetcher = image_categories_fetcher
        self._category_modifier = category_modifier
        self._selection_manager = selection_manager
        self._categories: list = []
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

    @Property(list, notify=categoriesChanged)
    def categories(self) -> list:
        return list(self._categories)

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
        thread = _FetchThread(self._image_categories_fetcher, image_id)
        thread.result.connect(self._on_fetch_result)
        self._active_fetch_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_fetch_threads.remove(t) if t in self._active_fetch_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str, str)
    def addCategory(self, category_id: str, category_name: str) -> None:
        if self._selection_manager:
            image_ids = list(self._selection_manager.selectedIds)
        elif self._primary_id:
            image_ids = [self._primary_id]
        else:
            return
        if not image_ids:
            return
        thread = _ModifyThread(self._category_modifier, image_ids, [category_id], [])
        thread.result.connect(
            lambda ok, _id=category_id, _name=category_name: self._on_add_result(ok, _id, _name)
        )
        self._active_modify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_modify_threads.remove(t) if t in self._active_modify_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str)
    def removeCategory(self, category_id: str) -> None:
        if not self._primary_id:
            return
        thread = _ModifyThread(self._category_modifier, [self._primary_id], [], [category_id])
        thread.result.connect(lambda ok, _id=category_id: self._on_remove_result(ok, _id))
        self._active_modify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_modify_threads.remove(t) if t in self._active_modify_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot()
    def clear(self) -> None:
        self._categories = []
        self._primary_id = ""
        self.categoriesChanged.emit()
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
            self._categories = []
            self._primary_id = ""
            self.categoriesChanged.emit()
            self._set_state("Idle")

    def _on_fetch_result(self, data: list | None) -> None:
        if data is None:
            self._set_state("Error")
            return
        self._categories = list(data)
        self.categoriesChanged.emit()
        self._set_state("Ready")

    def _on_add_result(self, ok: bool, category_id: str, category_name: str) -> None:
        if ok and self._selection_mode != "multi":
            if not any(c["id"] == category_id for c in self._categories):
                self._categories.append({"id": category_id, "name": category_name})
                self.categoriesChanged.emit()

    def _on_remove_result(self, ok: bool, category_id: str) -> None:
        if ok:
            self._categories = [c for c in self._categories if c["id"] != category_id]
            self.categoriesChanged.emit()

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


class _ModifyThread(QThread):
    result = Signal(bool)

    def __init__(
        self,
        modifier: Callable,
        image_ids: list,
        add_ids: list,
        remove_ids: list,
        parent=None,
    ):
        super().__init__(parent)
        self._modifier = modifier
        self._image_ids = image_ids
        self._add_ids = add_ids
        self._remove_ids = remove_ids

    def run(self) -> None:
        try:
            ok = self._modifier(self._image_ids, self._add_ids, self._remove_ids)
            self.result.emit(bool(ok))
        except Exception:
            self.result.emit(False)
