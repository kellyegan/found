from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot


class MetadataViewModel(QObject):
    metadataChanged = Signal()
    loadingStateChanged = Signal(str)

    def __init__(
        self,
        image_fetcher: Callable,
        selection_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        self._image_fetcher = image_fetcher
        self._loading_state = "Idle"
        self._image_id = ""
        self._filename = ""
        self._path = ""
        self._dimensions = ""
        self._file_size = 0
        self._date_added = ""
        self._is_missing = False
        self._active_fetch_threads: list = []

        if selection_manager is not None:
            selection_manager.selectionChanged.connect(self._on_selection_changed)
            self._selection_manager = selection_manager
        else:
            self._selection_manager = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(str, notify=loadingStateChanged)
    def loadingState(self) -> str:
        return self._loading_state

    @Property(str, notify=metadataChanged)
    def imageId(self) -> str:
        return self._image_id

    @Property(str, notify=metadataChanged)
    def filename(self) -> str:
        return self._filename

    @Property(str, notify=metadataChanged)
    def path(self) -> str:
        return self._path

    @Property(str, notify=metadataChanged)
    def dimensions(self) -> str:
        return self._dimensions

    @Property(int, notify=metadataChanged)
    def fileSize(self) -> int:
        return self._file_size

    @Property(str, notify=metadataChanged)
    def dateAdded(self) -> str:
        return self._date_added

    @Property(bool, notify=metadataChanged)
    def isMissing(self) -> bool:
        return self._is_missing

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(str)
    def loadImage(self, image_id: str) -> None:
        self._set_state("Loading")
        for t in list(self._active_fetch_threads):
            try:
                t.result.disconnect(self._on_result)
            except RuntimeError:
                pass
        thread = _FetchThread(self._image_fetcher, image_id)
        thread.result.connect(self._on_result)
        self._active_fetch_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_fetch_threads.remove(t) if t in self._active_fetch_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str)
    def updateFileStatus(self, status: str) -> None:
        self._is_missing = status == "missing"
        self.metadataChanged.emit()

    @Slot()
    def clear(self) -> None:
        self._reset_fields()
        self.metadataChanged.emit()
        self._set_state("Idle")

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:
        if self._selection_manager is None:
            return
        count = self._selection_manager.selectionCount
        if count == 1:
            self.loadImage(self._selection_manager.primaryId)
        else:
            self.clear()

    def _on_result(self, data: dict | None) -> None:
        if data is None:
            self._reset_fields()
            self.metadataChanged.emit()
            self._set_state("Error")
            return

        width = data.get("width", 0)
        height = data.get("height", 0)

        self._image_id = data.get("id", "")
        self._filename = data.get("filename", "")
        self._path = data.get("path", "")
        self._dimensions = f"{width} × {height}" if width and height else ""
        self._file_size = data.get("file_size", 0)
        self._date_added = data.get("imported_date", "")
        self._is_missing = data.get("file_status") == "missing"

        self.metadataChanged.emit()
        self._set_state("Ready")

    def _reset_fields(self) -> None:
        self._image_id = ""
        self._filename = ""
        self._path = ""
        self._dimensions = ""
        self._file_size = 0
        self._date_added = ""
        self._is_missing = False

    def _set_state(self, state: str) -> None:
        self._loading_state = state
        self.loadingStateChanged.emit(state)


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
