"""
Tests for ThumbnailProvider and _ThumbnailLRU — Commit 3.

Covers:
- _ThumbnailLRU.get() returns None for unknown key
- _ThumbnailLRU stores and retrieves by key
- _ThumbnailLRU evicts the oldest entry when capacity is exceeded
- _ThumbnailLRU moves a recently accessed entry to the end (so it survives eviction)
- _ThumbnailLRU put() updates existing key without eviction
- ThumbnailProvider.requestImageResponse() returns a QQuickImageResponse
"""

import pytest
from PySide6.QtGui import QImage

from found_app.providers.thumbnail_provider import ThumbnailProvider, _ThumbnailLRU


def _make_image(w=10, h=10) -> QImage:
    img = QImage(w, h, QImage.Format.Format_RGB32)
    img.fill(0x111111)
    return img


# ---------------------------------------------------------------------------
# _ThumbnailLRU
# ---------------------------------------------------------------------------


def test_lru_get_returns_none_for_missing_key(qapp):
    cache = _ThumbnailLRU(5)
    assert cache.get("missing") is None


def test_lru_stores_and_retrieves(qapp):
    cache = _ThumbnailLRU(5)
    img = _make_image()
    cache.put("k1", img)
    assert cache.get("k1") is img


def test_lru_evicts_oldest_on_overflow(qapp):
    cache = _ThumbnailLRU(2)
    img1, img2, img3 = _make_image(), _make_image(), _make_image()
    cache.put("k1", img1)
    cache.put("k2", img2)
    cache.put("k3", img3)  # k1 should be evicted
    assert cache.get("k1") is None
    assert cache.get("k2") is img2
    assert cache.get("k3") is img3


def test_lru_access_promotes_to_end(qapp):
    """Accessing k1 makes k2 the oldest; k2 is evicted when k3 is inserted."""
    cache = _ThumbnailLRU(2)
    img1, img2, img3 = _make_image(), _make_image(), _make_image()
    cache.put("k1", img1)
    cache.put("k2", img2)
    cache.get("k1")         # k1 now most-recently-used
    cache.put("k3", img3)   # k2 (oldest) evicted, not k1
    assert cache.get("k1") is img1
    assert cache.get("k2") is None
    assert cache.get("k3") is img3


def test_lru_put_update_does_not_evict(qapp):
    cache = _ThumbnailLRU(2)
    img1, img2, img_updated = _make_image(), _make_image(), _make_image()
    cache.put("k1", img1)
    cache.put("k2", img2)
    cache.put("k1", img_updated)  # update existing; capacity still 2, no eviction
    assert cache.get("k1") is img_updated
    assert cache.get("k2") is img2


# ---------------------------------------------------------------------------
# ThumbnailProvider
# ---------------------------------------------------------------------------


def test_thumbnail_provider_request_returns_image_response(qapp):
    from PySide6.QtCore import QSize
    from PySide6.QtQuick import QQuickImageResponse

    provider = ThumbnailProvider(base_url="http://127.0.0.1:9999")
    response = provider.requestImageResponse("some-uuid", QSize(60, 60))
    assert isinstance(response, QQuickImageResponse)


# ---------------------------------------------------------------------------
# Fetch caching behaviour
# ---------------------------------------------------------------------------


def _make_jpeg_bytes() -> bytes:
    """Return bytes of a minimal valid JPEG so QImage.loadFromData succeeds."""
    import io
    from PIL import Image as PILImage
    buf = io.BytesIO()
    PILImage.new("RGB", (10, 10), (17, 34, 51)).save(buf, "JPEG")
    return buf.getvalue()


def test_failed_fetch_is_not_cached(qapp, monkeypatch):
    """A timeout or non-200 response must not populate the LRU so the next
    request can retry rather than serving a stale placeholder forever."""
    import httpx
    from found_app.providers.thumbnail_provider import _FetchRunnable, _ThumbnailResponse

    monkeypatch.setattr(httpx, "get", lambda *a, **kw: (_ for _ in ()).throw(httpx.TimeoutException("timed out")))

    provider = ThumbnailProvider(base_url="http://127.0.0.1:9999")
    response = _ThumbnailResponse()
    runnable = _FetchRunnable(response, "http://x/thumbnail", provider._cache, "img-1")
    runnable.run()

    assert provider._cache.get("img-1") is None


def test_successful_fetch_is_cached(qapp, monkeypatch):
    """A 200 response with a valid image should be stored in the LRU."""
    import httpx
    from found_app.providers.thumbnail_provider import _FetchRunnable, _ThumbnailResponse

    jpeg_bytes = _make_jpeg_bytes()

    class _FakeResp:
        status_code = 200
        content = jpeg_bytes

    monkeypatch.setattr(httpx, "get", lambda *a, **kw: _FakeResp())

    provider = ThumbnailProvider(base_url="http://127.0.0.1:9999")
    response = _ThumbnailResponse()
    runnable = _FetchRunnable(response, "http://x/thumbnail", provider._cache, "img-2")
    runnable.run()

    assert provider._cache.get("img-2") is not None
