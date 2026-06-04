from enum import Enum, auto
from typing import Callable

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot

from found_app.library.thumbnail_grid_model import ThumbnailGridModel


class LibraryLoadingState(Enum):
    Loading = auto()
    Empty = auto()
    Ready = auto()
    Error = auto()


class LibraryViewModel(QObject):
    loadingStateChanged = Signal(str)
    missingCountChanged = Signal(int)

    def __init__(
        self,
        page_fetcher: Callable[..., dict | None],
        filter_state=None,
        image_verifier: Callable | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._page_fetcher = page_fetcher
        self._image_verifier = image_verifier
        self._loading_state = LibraryLoadingState.Loading
        self._grid_model = ThumbnailGridModel(parent=self)
        self._grid_model.missingCountChanged.connect(self.missingCountChanged)
        self._thread: _PageThread | None = None
        self._verify_threads: list = []
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
        thread = _VerifyThread(self._image_verifier, image_id)
        thread.result.connect(lambda status, iid=image_id: self._on_verify_result(iid, status))
        self._verify_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._verify_threads.remove(t) if t in self._verify_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

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
