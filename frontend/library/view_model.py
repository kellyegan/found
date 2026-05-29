from enum import Enum, auto
from typing import Callable

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot

from frontend.library.thumbnail_grid_model import ThumbnailGridModel


class LibraryLoadingState(Enum):
    Loading = auto()
    Empty = auto()
    Ready = auto()
    Error = auto()


class LibraryViewModel(QObject):
    loadingStateChanged = Signal(str)

    def __init__(
        self,
        page_fetcher: Callable[..., dict | None],
        parent=None,
    ):
        super().__init__(parent)
        self._page_fetcher = page_fetcher
        self._loading_state = LibraryLoadingState.Loading
        self._grid_model = ThumbnailGridModel(parent=self)
        self._thread: _PageThread | None = None
        self._is_fetching = False

    @Property(str, notify=loadingStateChanged)
    def loadingState(self) -> str:
        return self._loading_state.name

    @Property(QObject, constant=True)
    def gridModel(self) -> ThumbnailGridModel:
        return self._grid_model

    def load(self) -> None:
        self._grid_model.clear()
        self._start_fetch(cursor=None, is_initial=True)

    @Slot()
    def load_more(self) -> None:
        if not self._grid_model.hasMore or self._is_fetching:
            return
        self._start_fetch(cursor=self._grid_model.cursor or None, is_initial=False)

    def _start_fetch(self, cursor: str | None, is_initial: bool) -> None:
        self._is_fetching = True
        self._thread = _PageThread(self._page_fetcher, cursor)
        self._thread.result.connect(lambda page: self._on_result(page, is_initial))
        self._thread.start()

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

    def _set_state(self, state: LibraryLoadingState) -> None:
        self._loading_state = state
        self.loadingStateChanged.emit(state.name)


class _PageThread(QThread):
    result = Signal(object)  # dict | None

    def __init__(self, fetcher: Callable, cursor: str | None, parent=None):
        super().__init__(parent)
        self._fetcher = fetcher
        self._cursor = cursor

    def run(self) -> None:
        try:
            page = self._fetcher(cursor=self._cursor, limit=100)
            self.result.emit(page)
        except Exception:
            self.result.emit(None)
