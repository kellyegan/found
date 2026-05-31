from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot
from PySide6.QtQml import QJSValue

_CYCLE = {"off": "include", "include": "exclude", "exclude": "off"}


class CategoriesViewModel(QObject):
    categoriesChanged = Signal()
    loadingStateChanged = Signal(str)
    filterChanged = Signal()

    def __init__(
        self,
        categories_fetcher: Callable,
        category_creator: Optional[Callable] = None,
        images_adder: Optional[Callable] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._categories_fetcher = categories_fetcher
        self._category_creator = category_creator
        self._images_adder = images_adder
        self._categories: list = []
        self._filter_states: dict[str, str] = {}
        self._loading_state = "Idle"
        self._fetch_thread: Optional[_FetchThread] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(str, notify=loadingStateChanged)
    def loadingState(self) -> str:
        return self._loading_state

    @Property(list, notify=categoriesChanged)
    def categories(self) -> list:
        return [
            {**cat, "filterState": self._filter_states.get(cat["id"], "off")}
            for cat in self._categories
        ]

    @Property("QVariant", notify=filterChanged)
    def activeFilters(self) -> dict:
        return {
            cat_id: state
            for cat_id, state in self._filter_states.items()
            if state != "off"
        }

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot()
    def load(self) -> None:
        self._set_state("Loading")
        thread = _FetchThread(self._categories_fetcher)
        thread.result.connect(self._on_result)
        thread.finished.connect(thread.deleteLater)
        self._fetch_thread = thread
        thread.start()

    @Slot(str)
    def cycleFilter(self, category_id: str) -> None:
        current = self._filter_states.get(category_id, "off")
        self._filter_states[category_id] = _CYCLE[current]
        self.categoriesChanged.emit()
        self.filterChanged.emit()

    @Slot(str)
    def createCategory(self, name: str) -> None:
        name = name.strip()
        if not name or self._category_creator is None:
            return
        result = self._category_creator(name)
        if result is None:
            return
        self._categories = sorted(
            self._categories + [result],
            key=lambda c: c["name"].lower(),
        )
        self.categoriesChanged.emit()

    @Slot(str, "QVariant")
    def addImagesToCategory(self, category_id: str, image_ids) -> None:
        if isinstance(image_ids, QJSValue):
            image_ids = image_ids.toVariant() or []
        if not image_ids or self._images_adder is None:
            return
        self._images_adder(category_id, list(image_ids))

    @Slot()
    def clearFilters(self) -> None:
        self._filter_states.clear()
        self.categoriesChanged.emit()
        self.filterChanged.emit()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _on_result(self, data: list | None) -> None:
        if data is None:
            self._set_state("Error")
            return
        self._categories = sorted(data, key=lambda c: c["name"].lower())
        self._filter_states.clear()
        self.categoriesChanged.emit()
        self._set_state("Ready")

    def _set_state(self, state: str) -> None:
        self._loading_state = state
        self.loadingStateChanged.emit(state)


class _FetchThread(QThread):
    result = Signal(object)

    def __init__(self, fetcher: Callable, parent=None):
        super().__init__(parent)
        self._fetcher = fetcher

    def run(self) -> None:
        try:
            self.result.emit(self._fetcher())
        except Exception:
            self.result.emit(None)
