from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot


class TagSearchViewModel(QObject):
    suggestionsChanged = Signal()
    loadingStateChanged = Signal(str)
    tagNamesChanged = Signal()

    def __init__(
        self,
        tags_fetcher: Callable,
        filter_state=None,
        parent=None,
    ):
        super().__init__(parent)
        self._tags_fetcher = tags_fetcher
        self._filter_state = filter_state
        self._raw_suggestions: list = []
        self._loading_state = "Idle"
        self._tag_names: dict[str, str] = {}
        self._active_fetch_threads: list = []

        if filter_state is not None:
            filter_state.filtersChanged.connect(self._on_filters_changed)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(list, notify=suggestionsChanged)
    def suggestions(self) -> list:
        if not self._raw_suggestions:
            return []
        if self._filter_state is None:
            return list(self._raw_suggestions)
        active_ids = set(self._filter_state.tagFilters.keys())
        return [t for t in self._raw_suggestions if t["id"] not in active_ids]

    @Property(str, notify=loadingStateChanged)
    def loadingState(self) -> str:
        return self._loading_state

    @Property("QVariant", notify=tagNamesChanged)
    def tagNames(self) -> dict:
        return dict(self._tag_names)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(str)
    def search(self, term: str) -> None:
        term = term.strip()
        if not term:
            return
        self._set_state("Loading")
        for t in list(self._active_fetch_threads):
            try:
                t.result.disconnect(self._on_result)
            except RuntimeError:
                pass
        thread = _FetchThread(self._tags_fetcher, term)
        thread.result.connect(self._on_result)
        self._active_fetch_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._active_fetch_threads.remove(t) if t in self._active_fetch_threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @Slot()
    def clear(self) -> None:
        self._raw_suggestions = []
        self.suggestionsChanged.emit()
        self._set_state("Idle")

    @Slot(str, str)
    def selectTag(self, tag_id: str, tag_name: str) -> None:
        self._tag_names[tag_id] = tag_name
        self.tagNamesChanged.emit()
        if self._filter_state is not None:
            self._filter_state.setTagFilter(tag_id, "include")
        self.clear()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _on_filters_changed(self) -> None:
        if self._filter_state is not None:
            active_ids = set(self._filter_state.tagFilters.keys())
            cleaned = {k: v for k, v in self._tag_names.items() if k in active_ids}
            if cleaned != self._tag_names:
                self._tag_names = cleaned
                self.tagNamesChanged.emit()
        self.suggestionsChanged.emit()

    def _on_result(self, data: list | None) -> None:
        if data is None:
            self._raw_suggestions = []
            self.suggestionsChanged.emit()
            self._set_state("Error")
            return
        self._raw_suggestions = data
        self.suggestionsChanged.emit()
        self._set_state("Ready" if self.suggestions else "Empty")

    def _set_state(self, state: str) -> None:
        self._loading_state = state
        self.loadingStateChanged.emit(state)


class _FetchThread(QThread):
    result = Signal(object)

    def __init__(self, fetcher: Callable, term: str, parent=None):
        super().__init__(parent)
        self._fetcher = fetcher
        self._term = term

    def run(self) -> None:
        try:
            self.result.emit(self._fetcher(self._term))
        except Exception:
            self.result.emit(None)
