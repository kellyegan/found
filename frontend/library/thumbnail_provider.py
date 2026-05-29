import threading
from collections import OrderedDict

import httpx
from PySide6.QtCore import QRunnable, QSize, QThreadPool
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickAsyncImageProvider, QQuickImageResponse, QQuickTextureFactory


class _ThumbnailLRU:
    """Thread-safe LRU cache mapping image IDs to QImage objects."""

    def __init__(self, maxsize: int = 500):
        self._cache: OrderedDict[str, QImage] = OrderedDict()
        self._maxsize = maxsize
        self._lock = threading.Lock()

    def get(self, key: str) -> QImage | None:
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key: str, image: QImage) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._maxsize:
                    self._cache.popitem(last=False)
            self._cache[key] = image


class _ThumbnailResponse(QQuickImageResponse):
    def __init__(self):
        super().__init__()
        self._image = QImage()
        self._runnable: QRunnable | None = None  # keeps runnable alive until finished

    def textureFactory(self) -> QQuickTextureFactory:
        return QQuickTextureFactory.textureFactoryForImage(self._image)


class _FetchRunnable(QRunnable):
    def __init__(
        self,
        response: _ThumbnailResponse,
        url: str,
        cache: _ThumbnailLRU,
        image_id: str,
    ):
        super().__init__()
        self.setAutoDelete(False)
        self._response = response
        self._url = url
        self._cache = cache
        self._image_id = image_id

    def run(self) -> None:
        image = self._fetch()
        self._cache.put(self._image_id, image)
        self._response._image = image
        self._response.finished.emit()

    def _fetch(self) -> QImage:
        try:
            resp = httpx.get(self._url, timeout=10.0)
            if resp.status_code == 200:
                img = QImage()
                if img.loadFromData(resp.content) and not img.isNull():
                    return img
        except Exception:
            pass
        return _placeholder()


def _placeholder() -> QImage:
    img = QImage(60, 60, QImage.Format.Format_RGB32)
    img.fill(0x2A2A2A)
    return img


class ThumbnailProvider(QQuickAsyncImageProvider):
    def __init__(self, base_url: str = "http://127.0.0.1:8000", cache_size: int = 500):
        super().__init__()
        self._base_url = base_url.rstrip("/")
        self._cache = _ThumbnailLRU(cache_size)
        self._pending: list[_ThumbnailResponse] = []

    def requestImageResponse(self, image_id: str, requested_size: QSize) -> _ThumbnailResponse:
        response = _ThumbnailResponse()
        self._pending.append(response)
        response.finished.connect(lambda: self._on_finished(response))

        cached = self._cache.get(image_id)
        if cached is not None:
            response._image = cached
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: response.finished.emit())
        else:
            url = f"{self._base_url}/api/v1/images/{image_id}/thumbnail"
            runnable = _FetchRunnable(response, url, self._cache, image_id)
            response._runnable = runnable
            QThreadPool.globalInstance().start(runnable)

        return response

    def _on_finished(self, response: _ThumbnailResponse) -> None:
        try:
            self._pending.remove(response)
        except ValueError:
            pass
