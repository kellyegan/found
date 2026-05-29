from enum import Enum, auto
from typing import Callable

from PySide6.QtCore import QObject, QThread, Property, Signal


class LibraryLoadingState(Enum):
    Loading = auto()
    Empty = auto()
    Ready = auto()
    Error = auto()


class LibraryViewModel(QObject):
    loadingStateChanged = Signal(str)

    def __init__(self, image_fetcher: Callable[[], int | None], parent=None):
        super().__init__(parent)
        self._image_fetcher = image_fetcher
        self._loading_state = LibraryLoadingState.Loading
        self._thread: _LoadThread | None = None

    @Property(str, notify=loadingStateChanged)
    def loadingState(self) -> str:
        return self._loading_state.name

    def load(self) -> None:
        self._thread = _LoadThread(self._image_fetcher)
        self._thread.result.connect(self._on_result)
        self._thread.start()

    def _on_result(self, count: int) -> None:
        if count < 0:
            new_state = LibraryLoadingState.Error
        elif count == 0:
            new_state = LibraryLoadingState.Empty
        else:
            new_state = LibraryLoadingState.Ready
        self._loading_state = new_state
        self.loadingStateChanged.emit(new_state.name)


class _LoadThread(QThread):
    result = Signal(int)  # -1 = error, 0 = empty, N = count

    def __init__(self, fetcher: Callable[[], int | None], parent=None):
        super().__init__(parent)
        self._fetcher = fetcher

    def run(self) -> None:
        try:
            count = self._fetcher()
            self.result.emit(-1 if count is None else count)
        except Exception:
            self.result.emit(-1)
