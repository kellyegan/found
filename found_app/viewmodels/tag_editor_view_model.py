from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot


class TagEditorViewModel(QObject):
    tagsChanged = Signal()
    loadingStateChanged = Signal(str)
    selectionModeChanged = Signal(str)
    modified = Signal()

    def __init__(
        self,
        image_tags_fetcher: Callable,
        tag_modifier: Callable,
        tag_creator: Optional[Callable] = None,
        selection_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        self._image_tags_fetcher = image_tags_fetcher
        self._tag_modifier = tag_modifier
        self._tag_creator = tag_creator
        self._selection_manager = selection_manager
        self._tags: list = []
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

    @Property(list, notify=tagsChanged)
    def tags(self) -> list:
        return list(self._tags)

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
        thread = _FetchThread(self._image_tags_fetcher, image_id)
        thread.result.connect(self._on_fetch_result)
        self._active_fetch_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_fetch_threads.remove(t) if t in self._active_fetch_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str, str)
    def addTag(self, tag_id: str, tag_name: str) -> None:
        if self._selection_manager:
            image_ids = list(self._selection_manager.selectedIds)
        elif self._primary_id:
            image_ids = [self._primary_id]
        else:
            return
        if not image_ids:
            return
        thread = _ModifyThread(self._tag_modifier, image_ids, [tag_id], [])
        thread.result.connect(
            lambda ok, _id=tag_id, _name=tag_name: self._on_add_result(ok, _id, _name)
        )
        self._active_modify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_modify_threads.remove(t) if t in self._active_modify_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str)
    def removeTag(self, tag_id: str) -> None:
        if not self._primary_id:
            return
        image_ids = [self._primary_id]
        thread = _ModifyThread(self._tag_modifier, image_ids, [], [tag_id])
        thread.result.connect(lambda ok, _id=tag_id: self._on_remove_result(ok, _id))
        self._active_modify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_modify_threads.remove(t) if t in self._active_modify_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str)
    def addTagByName(self, name: str) -> None:
        name = name.strip().lower()
        if not name or self._tag_creator is None:
            return
        if self._selection_manager:
            image_ids = list(self._selection_manager.selectedIds)
        elif self._primary_id:
            image_ids = [self._primary_id]
        else:
            return
        if not image_ids:
            return
        thread = _CreateAndAddThread(self._tag_creator, self._tag_modifier, name, image_ids)
        thread.result.connect(self._on_create_add_result)
        self._active_modify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_modify_threads.remove(t) if t in self._active_modify_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot()
    def clear(self) -> None:
        self._tags = []
        self._primary_id = ""
        self.tagsChanged.emit()
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
            self._tags = []
            self._primary_id = ""
            self.tagsChanged.emit()
            self._set_state("Idle")

    def _on_fetch_result(self, data: list | None) -> None:
        if data is None:
            self._set_state("Error")
            return
        self._tags = list(data)
        self.tagsChanged.emit()
        self._set_state("Ready")

    def _on_add_result(self, ok: bool, tag_id: str, tag_name: str) -> None:
        if ok:
            self.modified.emit()
            if self._selection_mode != "multi":
                if not any(t["id"] == tag_id for t in self._tags):
                    self._tags.append({"id": tag_id, "name": tag_name})
                    self.tagsChanged.emit()

    def _on_remove_result(self, ok: bool, tag_id: str) -> None:
        if ok:
            self.modified.emit()
            self._tags = [t for t in self._tags if t["id"] != tag_id]
            self.tagsChanged.emit()

    def _on_create_add_result(self, tag: dict | None) -> None:
        if tag is not None and self._selection_mode != "multi":
            if not any(t["id"] == tag["id"] for t in self._tags):
                self._tags.append(tag)
                self.tagsChanged.emit()

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


class _CreateAndAddThread(QThread):
    result = Signal(object)

    def __init__(
        self,
        tag_creator: Callable,
        tag_modifier: Callable,
        name: str,
        image_ids: list,
        parent=None,
    ):
        super().__init__(parent)
        self._tag_creator = tag_creator
        self._tag_modifier = tag_modifier
        self._name = name
        self._image_ids = image_ids

    def run(self) -> None:
        try:
            tag = self._tag_creator(self._name)
            if tag is None:
                self.result.emit(None)
                return
            self._tag_modifier(self._image_ids, [tag["id"]], [])
            self.result.emit(tag)
        except Exception:
            self.result.emit(None)
