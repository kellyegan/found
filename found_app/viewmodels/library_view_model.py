from enum import Enum, auto
from typing import Callable

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot
from PySide6.QtQml import QJSValue

from found_app.models.thumbnail_grid_model import ThumbnailGridModel


class LibraryLoadingState(Enum):
    Loading = auto()
    Empty = auto()
    Ready = auto()
    Error = auto()


class LibraryViewModel(QObject):
    loadingStateChanged = Signal(str)
    missingCountChanged = Signal(int)
    imageStatusChanged = Signal(str, str)           # image_id, status
    imageRelocated = Signal(str, str, str)          # image_id, old_path, new_path
    relocationComplete = Signal(int, int, int, int) # updated, not_found, conflicts, mismatched
    locateDialogRequested = Signal(str, str)        # image_id, image_path
    relocationPreviewReady = Signal(int, str, str)  # affected_count, old_prefix, new_prefix

    def __init__(
        self,
        page_fetcher: Callable[..., dict | None],
        filter_state=None,
        image_verifier: Callable | None = None,
        batch_verifier: Callable | None = None,
        missing_id_fetcher: Callable | None = None,
        bulk_deleter: Callable | None = None,
        path_patcher: Callable | None = None,
        prefix_relocator: Callable | None = None,
        image_fetcher: Callable | None = None,
        preview_relocator: Callable | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._page_fetcher = page_fetcher
        self._image_verifier = image_verifier
        self._batch_verifier = batch_verifier
        self._missing_id_fetcher = missing_id_fetcher
        self._bulk_deleter = bulk_deleter
        self._path_patcher = path_patcher
        self._prefix_relocator = prefix_relocator
        self._image_fetcher = image_fetcher
        self._preview_relocator = preview_relocator
        self._loading_state = LibraryLoadingState.Loading
        self._grid_model = ThumbnailGridModel(parent=self)
        self._grid_model.missingCountChanged.connect(self.missingCountChanged)
        self._thread: _PageThread | None = None
        self._verify_threads: list = []
        self._verifying_ids: set = set()
        self._batch_verify_threads: list = []
        self._batch_verify_in_progress = False
        self._verify_missing_threads: list = []
        self._verify_missing_in_progress = False
        self._delete_threads: list = []
        self._relocate_threads: list = []
        self._relocate_prefix_threads: list = []
        self._locate_threads: list = []
        self._preview_threads: list = []
        self._is_fetching = False
        self._filter_state = filter_state
        if filter_state is not None:
            filter_state.filtersChanged.connect(self.load)

    @Property(str, notify=loadingStateChanged)
    def loadingState(self) -> str:
        return self._loading_state.name

    @Property(int, notify=missingCountChanged)
    def missingCount(self) -> int:
        return self._grid_model.missingCount

    @Property(QObject, constant=True)
    def gridModel(self) -> ThumbnailGridModel:
        return self._grid_model

    def load(self) -> None:
        self._grid_model.clear()
        if self._loading_state != LibraryLoadingState.Loading:
            self._set_state(LibraryLoadingState.Loading)
        self._start_fetch(cursor=None, is_initial=True)

    @Slot()
    def reload(self) -> None:
        self.load()

    @Slot(str)
    def verifyImage(self, image_id: str) -> None:
        if self._image_verifier is None:
            return
        if image_id in self._verifying_ids:
            return
        self._verifying_ids.add(image_id)
        thread = _VerifyThread(self._image_verifier, image_id)
        thread.result.connect(lambda status, iid=image_id: self._on_verify_result(iid, status))
        self._verify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._verify_threads.remove(t) if t in self._verify_threads else None)
        thread.finished.connect(lambda iid=image_id: self._verifying_ids.discard(iid))
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot("QVariant")
    def verifyBatch(self, image_ids) -> None:
        if self._batch_verifier is None:
            return
        if isinstance(image_ids, QJSValue):
            image_ids = image_ids.toVariant() or []
        image_ids = list(image_ids)
        if not image_ids or self._batch_verify_in_progress:
            return
        self._batch_verify_in_progress = True
        thread = _BatchVerifyThread(self._batch_verifier, image_ids)
        thread.result.connect(self._on_batch_verify_result)
        self._batch_verify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._batch_verify_threads.remove(t) if t in self._batch_verify_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot()
    def verifyMissing(self) -> None:
        if self._missing_id_fetcher is None:
            return
        if self._verify_missing_in_progress:
            return
        self._verify_missing_in_progress = True
        thread = _VerifyMissingThread(self._missing_id_fetcher)
        thread.result.connect(self._on_verify_missing_result)
        self._verify_missing_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._verify_missing_threads.remove(t) if t in self._verify_missing_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str, str, str)
    def relocateImage(self, image_id: str, old_path: str, new_path: str) -> None:
        if self._path_patcher is None:
            return
        thread = _RelocateImageThread(self._path_patcher, image_id, new_path)
        thread.result.connect(
            lambda data, iid=image_id, op=old_path, np=new_path:
                self._on_relocate_result(iid, op, np, data)
        )
        self._relocate_threads.append(thread)
        thread.finished.connect(
            lambda t=thread: self._relocate_threads.remove(t) if t in self._relocate_threads else None
        )
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str, str)
    def relocateByPrefix(self, old_prefix: str, new_prefix: str) -> None:
        if self._prefix_relocator is None:
            return
        thread = _RelocateByPrefixThread(self._prefix_relocator, old_prefix, new_prefix)
        thread.result.connect(self._on_relocate_by_prefix_result)
        self._relocate_prefix_threads.append(thread)
        thread.finished.connect(
            lambda t=thread: self._relocate_prefix_threads.remove(t)
            if t in self._relocate_prefix_threads else None
        )
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str)
    def requestLocate(self, image_id: str) -> None:
        if self._image_fetcher is None:
            return
        thread = _RequestLocateThread(self._image_fetcher, image_id)
        thread.result.connect(lambda data, iid=image_id: self._on_request_locate_result(iid, data))
        self._locate_threads.append(thread)
        thread.finished.connect(
            lambda t=thread: self._locate_threads.remove(t) if t in self._locate_threads else None
        )
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot(str, str)
    def previewRelocation(self, old_path: str, new_path: str) -> None:
        if self._preview_relocator is None:
            return
        thread = _PreviewRelocationThread(self._preview_relocator, old_path, new_path)
        thread.result.connect(self._on_preview_relocation_result)
        self._preview_threads.append(thread)
        thread.finished.connect(
            lambda t=thread: self._preview_threads.remove(t) if t in self._preview_threads else None
        )
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot("QVariant")
    def removeImages(self, image_ids) -> None:
        if isinstance(image_ids, QJSValue):
            image_ids = image_ids.toVariant() or []
        image_ids = list(image_ids)
        if not image_ids or self._bulk_deleter is None:
            return
        thread = _DeleteThread(self._bulk_deleter, image_ids)
        thread.result.connect(self._on_delete_result)
        self._delete_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._delete_threads.remove(t) if t in self._delete_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _on_delete_result(self, ok: bool) -> None:
        if ok:
            self.reload()

    @Slot()
    def load_more(self) -> None:
        if not self._grid_model.hasMore or self._is_fetching:
            return
        self._start_fetch(cursor=self._grid_model.cursor or None, is_initial=False)

    def _start_fetch(self, cursor: str | None, is_initial: bool) -> None:
        self._is_fetching = True
        fetch_kwargs: dict = {"cursor": cursor, "limit": 100}
        if self._filter_state is not None:
            fetch_kwargs.update(self._filter_state.queryParams)
        self._thread = _PageThread(self._page_fetcher, fetch_kwargs)
        self._thread.result.connect(lambda page: self._on_result(page, is_initial))
        self._thread.start()

    def _on_verify_result(self, image_id: str, status: str | None) -> None:
        if status:
            self._grid_model.updateItemStatus(image_id, status)
            self.imageStatusChanged.emit(image_id, status)

    def _on_batch_verify_result(self, results: list) -> None:
        self._batch_verify_in_progress = False
        for item in results:
            image_id = item.get("id")
            status = item.get("file_status")
            if image_id and status:
                self._grid_model.updateItemStatus(image_id, status)
                self.imageStatusChanged.emit(image_id, status)

    def _on_verify_missing_result(self, page: dict | None) -> None:
        self._verify_missing_in_progress = False
        if not page:
            return
        image_ids = [item["id"] for item in page.get("items", []) if item.get("id")]
        if image_ids:
            self.verifyBatch(image_ids)

    def _on_relocate_result(
        self, image_id: str, old_path: str, new_path: str, data: dict | None
    ) -> None:
        if data is None:
            return
        self._grid_model.updateItemStatus(image_id, "available")
        self.imageRelocated.emit(image_id, old_path, new_path)

    def _on_relocate_by_prefix_result(self, data: dict | None) -> None:
        if data is not None:
            self.relocationComplete.emit(
                data.get("updated", 0),
                data.get("not_found", 0),
                data.get("conflicts", 0),
                data.get("mismatched", 0),
            )
        self.reload()

    def _on_request_locate_result(self, image_id: str, data: dict | None) -> None:
        if data is None:
            return
        path = data.get("path", "")
        if path:
            self.locateDialogRequested.emit(image_id, path)

    def _on_preview_relocation_result(self, data: dict | None) -> None:
        if data is None:
            return
        self.relocationPreviewReady.emit(
            data.get("affected_count", 0),
            data.get("old_prefix", ""),
            data.get("new_prefix", ""),
        )

    def _on_result(self, page: dict | None, is_initial: bool) -> None:
        self._is_fetching = False
        if page is None:
            if is_initial:
                self._set_state(LibraryLoadingState.Error)
            return

        items = page.get("items", [])
        cursor = page.get("next_cursor")
        has_more = page.get("has_more", False)
        self._grid_model.appendPage(items, cursor, has_more)

        if is_initial:
            new_state = LibraryLoadingState.Empty if not items else LibraryLoadingState.Ready
            self._set_state(new_state)

    def shutdown(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            self._thread.wait(3000)

    def _set_state(self, state: LibraryLoadingState) -> None:
        self._loading_state = state
        self.loadingStateChanged.emit(state.name)


class _PageThread(QThread):
    result = Signal(object)  # dict | None

    def __init__(self, fetcher: Callable, fetch_kwargs: dict, parent=None):
        super().__init__(parent)
        self._fetcher = fetcher
        self._fetch_kwargs = fetch_kwargs

    def run(self) -> None:
        try:
            page = self._fetcher(**self._fetch_kwargs)
            self.result.emit(page)
        except Exception:
            self.result.emit(None)


class _DeleteThread(QThread):
    result = Signal(bool)

    def __init__(self, deleter: Callable, image_ids: list, parent=None):
        super().__init__(parent)
        self._deleter = deleter
        self._image_ids = image_ids

    def run(self) -> None:
        try:
            ok = self._deleter(self._image_ids)
            self.result.emit(bool(ok))
        except Exception:
            self.result.emit(False)


class _RelocateImageThread(QThread):
    result = Signal(object)  # dict | None — updated image data from patch_path

    def __init__(self, patcher: Callable, image_id: str, new_path: str, parent=None):
        super().__init__(parent)
        self._patcher = patcher
        self._image_id = image_id
        self._new_path = new_path

    def run(self) -> None:
        try:
            self.result.emit(self._patcher(self._image_id, self._new_path))
        except Exception:
            self.result.emit(None)


class _RelocateByPrefixThread(QThread):
    result = Signal(object)  # dict | None — counts from relocate_by_prefix

    def __init__(self, relocator: Callable, old_prefix: str, new_prefix: str, parent=None):
        super().__init__(parent)
        self._relocator = relocator
        self._old_prefix = old_prefix
        self._new_prefix = new_prefix

    def run(self) -> None:
        try:
            self.result.emit(self._relocator(self._old_prefix, self._new_prefix))
        except Exception:
            self.result.emit(None)


class _RequestLocateThread(QThread):
    result = Signal(object)  # dict | None — full image record including path

    def __init__(self, fetcher: Callable, image_id: str, parent=None):
        super().__init__(parent)
        self._fetcher = fetcher
        self._image_id = image_id

    def run(self) -> None:
        try:
            self.result.emit(self._fetcher(self._image_id))
        except Exception:
            self.result.emit(None)


class _PreviewRelocationThread(QThread):
    result = Signal(object)  # dict | None — {affected_count, old_prefix, new_prefix}

    def __init__(self, relocator: Callable, old_path: str, new_path: str, parent=None):
        super().__init__(parent)
        self._relocator = relocator
        self._old_path = old_path
        self._new_path = new_path

    def run(self) -> None:
        try:
            self.result.emit(self._relocator(self._old_path, self._new_path))
        except Exception:
            self.result.emit(None)


class _VerifyThread(QThread):
    result = Signal(object)  # str | None — the new file_status, or None on failure

    def __init__(self, verifier: Callable, image_id: str, parent=None):
        super().__init__(parent)
        self._verifier = verifier
        self._image_id = image_id

    def run(self) -> None:
        try:
            status = self._verifier(self._image_id)
            self.result.emit(status)
        except Exception:
            self.result.emit(None)


class _BatchVerifyThread(QThread):
    result = Signal(object)  # list[dict] — [{"id": ..., "file_status": ...}, ...]

    def __init__(self, verifier: Callable, image_ids: list, parent=None):
        super().__init__(parent)
        self._verifier = verifier
        self._image_ids = image_ids

    def run(self) -> None:
        try:
            self.result.emit(self._verifier(self._image_ids))
        except Exception:
            self.result.emit([])


class _VerifyMissingThread(QThread):
    result = Signal(object)  # dict | None — page of currently-missing images

    def __init__(self, fetcher: Callable, parent=None):
        super().__init__(parent)
        self._fetcher = fetcher

    def run(self) -> None:
        try:
            self.result.emit(self._fetcher())
        except Exception:
            self.result.emit(None)
