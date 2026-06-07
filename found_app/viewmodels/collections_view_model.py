from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Property, Signal, Slot
from PySide6.QtQml import QJSValue

from found_app.models.thumbnail_grid_model import ThumbnailGridModel


class CollectionsViewModel(QObject):
    collectionsChanged = Signal()
    loadingStateChanged = Signal(str)
    imagesRemovedFromLibrary = Signal()

    def __init__(
        self,
        collections_fetcher: Callable,
        collection_creator: Callable,
        images_adder: Callable,
        collection_images_fetcher: Callable,
        collection_remover: Callable | None = None,
        bulk_deleter: Callable | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._collections_fetcher = collections_fetcher
        self._collection_creator = collection_creator
        self._images_adder = images_adder
        self._collection_images_fetcher = collection_images_fetcher
        self._collection_remover = collection_remover
        self._bulk_deleter = bulk_deleter

        self._collections: list = []
        self._loading_state = "Idle"
        self._collection_grid_model = ThumbnailGridModel(parent=self)
        self._current_collection_id: str = ""
        self._fetch_thread: Optional[_FetchThread] = None
        self._images_thread: Optional[_ImagesThread] = None
        self._remove_thread: Optional[_RemoveImagesThread] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(str, notify=loadingStateChanged)
    def loadingState(self) -> str:
        return self._loading_state

    @Property(list, notify=collectionsChanged)
    def collections(self) -> list:
        return self._collections

    @Property(QObject, constant=True)
    def collectionGridModel(self) -> ThumbnailGridModel:
        return self._collection_grid_model

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot()
    def load(self) -> None:
        self._set_state("Loading")
        thread = _FetchThread(self._collections_fetcher)
        thread.result.connect(self._on_collections_result)
        self._fetch_thread = thread
        thread.start()

    @Slot(str)
    def createCollection(self, name: str) -> None:
        result = self._collection_creator(name)
        if result is None:
            return
        self._collections = sorted(
            self._collections + [result],
            key=lambda c: c["name"].lower(),
        )
        self.collectionsChanged.emit()

    @Slot(str, "QVariant")
    def addImagesToCollection(self, collection_id: str, image_ids) -> None:
        if isinstance(image_ids, QJSValue):
            image_ids = image_ids.toVariant() or []
        if not image_ids:
            return
        self._images_adder(collection_id, list(image_ids))

    @Slot(str)
    def loadCollectionImages(self, collection_id: str) -> None:
        self._current_collection_id = collection_id
        self._collection_grid_model.clear()
        thread = _ImagesThread(self._collection_images_fetcher, collection_id)
        thread.result.connect(self._on_images_result)
        self._images_thread = thread
        thread.start()

    @Slot()
    def reloadCollectionImages(self) -> None:
        if self._current_collection_id:
            self.loadCollectionImages(self._current_collection_id)

    @Slot(str, "QVariant", bool)
    def removeImagesFromCollection(self, collection_id: str, image_ids, also_from_library: bool) -> None:
        if isinstance(image_ids, QJSValue):
            image_ids = image_ids.toVariant() or []
        image_ids = list(image_ids)
        if not image_ids or self._collection_remover is None:
            return
        thread = _RemoveImagesThread(
            self._collection_remover, self._bulk_deleter, collection_id, image_ids, also_from_library
        )
        thread.result.connect(
            lambda ok: self._on_remove_images_result(ok, collection_id, also_from_library)
        )
        self._remove_thread = thread
        thread.start()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _on_remove_images_result(self, ok: bool, collection_id: str, also_from_library: bool) -> None:
        if not ok:
            return
        self.loadCollectionImages(collection_id)
        if also_from_library:
            self.imagesRemovedFromLibrary.emit()

    def _on_collections_result(self, data: list | None) -> None:
        if data is None:
            self._set_state("Error")
            return
        self._collections = sorted(data, key=lambda c: c["name"].lower())
        self.collectionsChanged.emit()
        self._set_state("Empty" if not data else "Ready")

    def _on_images_result(self, images: list | None) -> None:
        self._collection_grid_model.clear()
        if images:
            self._collection_grid_model.appendPage(images, None, False)

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
            data = self._fetcher()
            self.result.emit(data)
        except Exception:
            self.result.emit(None)


class _ImagesThread(QThread):
    result = Signal(object)

    def __init__(self, fetcher: Callable, collection_id: str, parent=None):
        super().__init__(parent)
        self._fetcher = fetcher
        self._collection_id = collection_id

    def run(self) -> None:
        try:
            images = self._fetcher(self._collection_id)
            self.result.emit(images if images is not None else [])
        except Exception:
            self.result.emit([])


class _RemoveImagesThread(QThread):
    result = Signal(bool)

    def __init__(
        self,
        remover: Callable,
        bulk_deleter: Callable | None,
        collection_id: str,
        image_ids: list,
        also_from_library: bool,
        parent=None,
    ):
        super().__init__(parent)
        self._remover = remover
        self._bulk_deleter = bulk_deleter
        self._collection_id = collection_id
        self._image_ids = image_ids
        self._also_from_library = also_from_library

    def run(self) -> None:
        try:
            ok = True
            for image_id in self._image_ids:
                if not self._remover(self._collection_id, image_id):
                    ok = False
            if self._also_from_library and self._bulk_deleter is not None:
                if not self._bulk_deleter(self._image_ids):
                    ok = False
            self.result.emit(ok)
        except Exception:
            self.result.emit(False)
