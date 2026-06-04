"""
Tests for ApiClient.

Covers:
- health_check() returns True on 200, False on non-200 or network error
- request() parses the {"success", "data", "error"} envelope
- request() raises ApiError when success=false
- request() raises NotFoundError on 404
- request() raises NetworkError on connection failure
- ApiError carries code and message attributes
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

from found_app.api.client import ApiClient, ApiError, NetworkError, NotFoundError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def mock_response(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


def make_client() -> tuple[ApiClient, AsyncMock]:
    """Return an ApiClient backed by a fresh AsyncMock http client."""
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    return ApiClient(client=mock_http), mock_http


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------


async def test_health_check_returns_true_on_200():
    client, mock_http = make_client()
    mock_http.get.return_value = mock_response(200)
    assert await client.health_check() is True


async def test_health_check_returns_false_on_non_200():
    client, mock_http = make_client()
    mock_http.get.return_value = mock_response(503)
    assert await client.health_check() is False


async def test_health_check_returns_false_on_network_error():
    client, mock_http = make_client()
    mock_http.get.side_effect = httpx.NetworkError("Connection refused")
    assert await client.health_check() is False


# ---------------------------------------------------------------------------
# request() — success path
# ---------------------------------------------------------------------------


async def test_request_returns_data_on_success():
    payload = {"images": [{"id": 1}]}
    client, mock_http = make_client()
    mock_http.request.return_value = mock_response(
        200, {"success": True, "data": payload}
    )
    result = await client.request("GET", "/api/v1/images")
    assert result == payload


async def test_request_passes_method_and_path():
    client, mock_http = make_client()
    mock_http.request.return_value = mock_response(
        200, {"success": True, "data": {}}
    )
    await client.request("POST", "/api/v1/images")
    mock_http.request.assert_called_once_with("POST", "/api/v1/images")


# ---------------------------------------------------------------------------
# request() — envelope errors
# ---------------------------------------------------------------------------


async def test_request_raises_api_error_on_failed_envelope():
    client, mock_http = make_client()
    mock_http.request.return_value = mock_response(
        400,
        {"success": False, "error": {"code": "invalid_input", "message": "Bad value"}},
    )
    with pytest.raises(ApiError) as exc_info:
        await client.request("GET", "/api/v1/images")
    assert exc_info.value.code == "invalid_input"
    assert "Bad value" in exc_info.value.message


async def test_request_raises_not_found_error_on_404():
    client, mock_http = make_client()
    mock_http.request.return_value = mock_response(
        404,
        {"success": False, "error": {"code": "not_found", "message": "Image not found"}},
    )
    with pytest.raises(NotFoundError):
        await client.request("GET", "/api/v1/images/999")


async def test_not_found_error_is_subclass_of_api_error():
    with pytest.raises(ApiError):
        raise NotFoundError("missing")


# ---------------------------------------------------------------------------
# request() — network errors
# ---------------------------------------------------------------------------


async def test_request_raises_network_error_on_connection_failure():
    client, mock_http = make_client()
    mock_http.request.side_effect = httpx.NetworkError("Connection refused")
    with pytest.raises(NetworkError):
        await client.request("GET", "/api/v1/images")


async def test_request_raises_network_error_on_timeout():
    client, mock_http = make_client()
    mock_http.request.side_effect = httpx.TimeoutException("Timed out")
    with pytest.raises(NetworkError):
        await client.request("GET", "/api/v1/images")


# ---------------------------------------------------------------------------
# ApiError attributes
# ---------------------------------------------------------------------------


def test_api_error_exposes_code_and_message():
    err = ApiError("some_code", "Some message")
    assert err.code == "some_code"
    assert err.message == "Some message"


def test_api_error_str_includes_code_and_message():
    err = ApiError("some_code", "Some message")
    assert "some_code" in str(err)
    assert "Some message" in str(err)


# ---------------------------------------------------------------------------
# list_images
# ---------------------------------------------------------------------------


async def test_list_images_returns_items_cursor_and_has_more():
    """list_images() returns (items, next_cursor, has_more) from a paged response."""
    client, mock_http = make_client()
    items = [{"id": "abc", "filename": "a.jpg", "file_status": "available"}]
    mock_http.get.return_value = mock_response(
        200,
        {"success": True, "data": items, "next_cursor": "tok123", "has_more": True},
    )
    result_items, next_cursor, has_more = await client.list_images()
    assert result_items == items
    assert next_cursor == "tok123"
    assert has_more is True


async def test_list_images_passes_grid_view_by_default():
    client, mock_http = make_client()
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [], "next_cursor": None, "has_more": False}
    )
    await client.list_images()
    call_kwargs = mock_http.get.call_args
    params = call_kwargs.kwargs.get("params", call_kwargs.args[1] if len(call_kwargs.args) > 1 else {})
    assert params.get("view") == "grid"


async def test_list_images_passes_cursor_when_provided():
    client, mock_http = make_client()
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [], "next_cursor": None, "has_more": False}
    )
    await client.list_images(cursor="tok456")
    call_kwargs = mock_http.get.call_args
    params = call_kwargs.kwargs.get("params", {})
    assert params.get("cursor") == "tok456"


async def test_list_images_omits_cursor_when_none():
    client, mock_http = make_client()
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [], "next_cursor": None, "has_more": False}
    )
    await client.list_images(cursor=None)
    call_kwargs = mock_http.get.call_args
    params = call_kwargs.kwargs.get("params", {})
    assert "cursor" not in params


async def test_list_images_raises_network_error_on_connection_failure():
    client, mock_http = make_client()
    mock_http.get.side_effect = httpx.NetworkError("Connection refused")
    with pytest.raises(NetworkError):
        await client.list_images()


async def test_list_images_returns_empty_list_when_no_images():
    client, mock_http = make_client()
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [], "next_cursor": None, "has_more": False}
    )
    items, next_cursor, has_more = await client.list_images()
    assert items == []
    assert next_cursor is None
    assert has_more is False


# ---------------------------------------------------------------------------
# Sync client helpers
# ---------------------------------------------------------------------------


def make_sync_client() -> tuple[ApiClient, MagicMock]:
    mock_http = MagicMock(spec=httpx.Client)
    return ApiClient(sync_client=mock_http), mock_http


# ---------------------------------------------------------------------------
# fetch_images_page
# ---------------------------------------------------------------------------


def test_fetch_images_page_returns_items_cursor_and_has_more():
    client, mock_http = make_sync_client()
    items = [{"id": "abc", "thumbnail_url": "image://thumbnails/abc"}]
    mock_http.get.return_value = mock_response(
        200,
        {"success": True, "data": items, "next_cursor": "tok1", "has_more": True},
    )
    result = client.fetch_images_page()
    assert result["items"] == items
    assert result["next_cursor"] == "tok1"
    assert result["has_more"] is True


def test_fetch_images_page_passes_cursor():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [], "next_cursor": None, "has_more": False}
    )
    client.fetch_images_page(cursor="tok2")
    params = mock_http.get.call_args.kwargs["params"]
    assert params["cursor"] == "tok2"


def test_fetch_images_page_omits_cursor_when_none():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [], "next_cursor": None, "has_more": False}
    )
    client.fetch_images_page(cursor=None)
    params = mock_http.get.call_args.kwargs["params"]
    assert "cursor" not in params


def test_fetch_images_page_passes_category_filter():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [], "next_cursor": None, "has_more": False}
    )
    client.fetch_images_page(category="cat-1")
    params = mock_http.get.call_args.kwargs["params"]
    assert params["categories"] == "cat-1"


def test_fetch_images_page_passes_tag_filter():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [], "next_cursor": None, "has_more": False}
    )
    client.fetch_images_page(tag="nature")
    params = mock_http.get.call_args.kwargs["params"]
    assert params["tags"] == "nature"


def test_fetch_images_page_maps_missing_file_status_to_bool_param():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [], "next_cursor": None, "has_more": False}
    )
    client.fetch_images_page(file_status="missing")
    params = mock_http.get.call_args.kwargs["params"]
    assert params["missing"] is True
    assert "file_status" not in params


def test_fetch_images_page_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("network failure")
    assert client.fetch_images_page() is None


def test_fetch_images_page_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.fetch_images_page() is None


# ---------------------------------------------------------------------------
# fetch_image
# ---------------------------------------------------------------------------


def test_fetch_image_returns_image_data():
    client, mock_http = make_sync_client()
    image = {"id": "abc", "filename": "photo.jpg"}
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": image}
    )
    assert client.fetch_image("abc") == image


def test_fetch_image_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "not_found", "message": "missing"}}
    )
    assert client.fetch_image("abc") is None


def test_fetch_image_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.fetch_image("abc") is None


# ---------------------------------------------------------------------------
# verify_image
# ---------------------------------------------------------------------------


def test_verify_image_returns_file_status_string():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": True, "data": {"file_status": "available"}}
    )
    assert client.verify_image("abc") == "available"


def test_verify_image_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": False, "error": {"code": "not_found", "message": "missing"}}
    )
    assert client.verify_image("abc") is None


def test_verify_image_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.verify_image("abc") is None
