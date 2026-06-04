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

from found_app.core.api_client import ApiClient, ApiError, NetworkError, NotFoundError


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


# ---------------------------------------------------------------------------
# scan_paths
# ---------------------------------------------------------------------------


def test_scan_paths_returns_preview_data():
    client, mock_http = make_sync_client()
    preview = {"paths": ["/img/a.jpg"], "duplicates": []}
    mock_http.post.return_value = mock_response(
        200, {"success": True, "data": preview}
    )
    assert client.scan_paths(["/img/a.jpg"]) == preview


def test_scan_paths_posts_to_import_preview_endpoint():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": True, "data": {}}
    )
    client.scan_paths(["/img/a.jpg"])
    url = mock_http.post.call_args.args[0]
    assert url == "/api/v1/images/import/preview"


def test_scan_paths_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.scan_paths(["/img/a.jpg"]) is None


def test_scan_paths_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.scan_paths(["/img/a.jpg"]) is None


# ---------------------------------------------------------------------------
# import_paths
# ---------------------------------------------------------------------------


def test_import_paths_returns_job_id():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": True, "data": {"job_id": "job-123"}}
    )
    assert client.import_paths(["/img/a.jpg"]) == "job-123"


def test_import_paths_posts_to_import_endpoint():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": True, "data": {"job_id": "job-123"}}
    )
    client.import_paths(["/img/a.jpg"])
    url = mock_http.post.call_args.args[0]
    assert url == "/api/v1/images/import"


def test_import_paths_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.import_paths(["/img/a.jpg"]) is None


def test_import_paths_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.import_paths(["/img/a.jpg"]) is None


# ---------------------------------------------------------------------------
# fetch_job
# ---------------------------------------------------------------------------


def test_fetch_job_returns_job_data():
    client, mock_http = make_sync_client()
    job = {"job_id": "job-123", "status": "complete"}
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": job}
    )
    assert client.fetch_job("job-123") == job


def test_fetch_job_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "not_found", "message": "missing"}}
    )
    assert client.fetch_job("job-123") is None


def test_fetch_job_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.fetch_job("job-123") is None


# ---------------------------------------------------------------------------
# resolve_conflict
# ---------------------------------------------------------------------------


def test_resolve_conflict_returns_true_on_success():
    client, mock_http = make_sync_client()
    mock_http.patch.return_value = mock_response(
        200, {"success": True, "data": {}}
    )
    assert client.resolve_conflict("img-1", "/new/path.jpg") is True


def test_resolve_conflict_patches_image_path():
    client, mock_http = make_sync_client()
    mock_http.patch.return_value = mock_response(
        200, {"success": True, "data": {}}
    )
    client.resolve_conflict("img-1", "/new/path.jpg")
    url = mock_http.patch.call_args.args[0]
    body = mock_http.patch.call_args.kwargs["json"]
    assert url == "/api/v1/images/img-1"
    assert body == {"path": "/new/path.jpg"}


def test_resolve_conflict_returns_false_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.patch.return_value = mock_response(
        200, {"success": False, "error": {"code": "not_found", "message": "missing"}}
    )
    assert client.resolve_conflict("img-1", "/new/path.jpg") is False


def test_resolve_conflict_returns_false_on_exception():
    client, mock_http = make_sync_client()
    mock_http.patch.side_effect = Exception("timeout")
    assert client.resolve_conflict("img-1", "/new/path.jpg") is False


# ---------------------------------------------------------------------------
# create_tag
# ---------------------------------------------------------------------------


def test_create_tag_returns_tag_data_on_success():
    client, mock_http = make_sync_client()
    tag = {"id": "tag-1", "name": "nature"}
    mock_http.post.return_value = mock_response(200, {"success": True, "data": tag})
    assert client.create_tag("nature") == tag


def test_create_tag_returns_existing_tag_on_409():
    client, mock_http = make_sync_client()
    existing = {"id": "tag-1", "name": "Nature"}
    mock_http.post.return_value = mock_response(
        409, {"success": False, "error": {"code": "conflict", "message": "exists"}}
    )
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [existing]}
    )
    assert client.create_tag("nature") == existing


def test_create_tag_409_match_is_case_insensitive():
    client, mock_http = make_sync_client()
    existing = {"id": "tag-1", "name": "NATURE"}
    mock_http.post.return_value = mock_response(
        409, {"success": False, "error": {"code": "conflict", "message": "exists"}}
    )
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [existing]}
    )
    assert client.create_tag("nature") == existing


def test_create_tag_returns_none_when_409_search_finds_no_match():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        409, {"success": False, "error": {"code": "conflict", "message": "exists"}}
    )
    mock_http.get.return_value = mock_response(
        200, {"success": True, "data": [{"id": "tag-2", "name": "different"}]}
    )
    assert client.create_tag("nature") is None


def test_create_tag_returns_none_on_other_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        400, {"success": False, "error": {"code": "invalid", "message": "bad"}}
    )
    assert client.create_tag("nature") is None


def test_create_tag_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.create_tag("nature") is None


# ---------------------------------------------------------------------------
# search_tags
# ---------------------------------------------------------------------------


def test_search_tags_returns_list():
    client, mock_http = make_sync_client()
    tags = [{"id": "tag-1", "name": "nature"}, {"id": "tag-2", "name": "natural"}]
    mock_http.get.return_value = mock_response(200, {"success": True, "data": tags})
    assert client.search_tags("natur") == tags


def test_search_tags_returns_empty_list_when_no_results():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(200, {"success": True, "data": []})
    assert client.search_tags("xyz") == []


def test_search_tags_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.search_tags("natur") is None


def test_search_tags_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.search_tags("natur") is None


# ---------------------------------------------------------------------------
# fetch_image_tags
# ---------------------------------------------------------------------------


def test_fetch_image_tags_returns_list():
    client, mock_http = make_sync_client()
    tags = [{"id": "tag-1", "name": "nature"}]
    mock_http.get.return_value = mock_response(200, {"success": True, "data": tags})
    assert client.fetch_image_tags("img-1") == tags


def test_fetch_image_tags_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "not_found", "message": "missing"}}
    )
    assert client.fetch_image_tags("img-1") is None


def test_fetch_image_tags_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.fetch_image_tags("img-1") is None


# ---------------------------------------------------------------------------
# bulk_modify_tags
# ---------------------------------------------------------------------------


def test_bulk_modify_tags_returns_true_on_success():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    assert client.bulk_modify_tags(["img-1"], ["tag-1"], []) is True


def test_bulk_modify_tags_posts_correct_body():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    client.bulk_modify_tags(["img-1", "img-2"], ["tag-a"], ["tag-b"])
    body = mock_http.post.call_args.kwargs["json"]
    assert body == {
        "image_ids": ["img-1", "img-2"],
        "add_tag_ids": ["tag-a"],
        "remove_tag_ids": ["tag-b"],
    }


def test_bulk_modify_tags_returns_false_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.bulk_modify_tags(["img-1"], ["tag-1"], []) is False


def test_bulk_modify_tags_returns_false_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.bulk_modify_tags(["img-1"], ["tag-1"], []) is False


# ---------------------------------------------------------------------------
# list_categories
# ---------------------------------------------------------------------------


def test_list_categories_returns_list():
    client, mock_http = make_sync_client()
    cats = [{"id": "cat-1", "name": "Architecture"}]
    mock_http.get.return_value = mock_response(200, {"success": True, "data": cats})
    assert client.list_categories() == cats


def test_list_categories_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.list_categories() is None


def test_list_categories_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.list_categories() is None


# ---------------------------------------------------------------------------
# create_category
# ---------------------------------------------------------------------------


def test_create_category_returns_category_data():
    client, mock_http = make_sync_client()
    cat = {"id": "cat-1", "name": "Architecture"}
    mock_http.post.return_value = mock_response(200, {"success": True, "data": cat})
    assert client.create_category("Architecture") == cat


def test_create_category_posts_name_and_empty_description():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    client.create_category("Architecture")
    body = mock_http.post.call_args.kwargs["json"]
    assert body == {"name": "Architecture", "description": ""}


def test_create_category_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.create_category("Architecture") is None


def test_create_category_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.create_category("Architecture") is None


# ---------------------------------------------------------------------------
# search_categories
# ---------------------------------------------------------------------------


def test_search_categories_returns_list():
    client, mock_http = make_sync_client()
    cats = [{"id": "cat-1", "name": "Architecture"}]
    mock_http.get.return_value = mock_response(200, {"success": True, "data": cats})
    assert client.search_categories("arch") == cats


def test_search_categories_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.search_categories("arch") is None


def test_search_categories_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.search_categories("arch") is None


# ---------------------------------------------------------------------------
# add_images_to_category
# ---------------------------------------------------------------------------


def test_add_images_to_category_returns_true_on_success():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    assert client.add_images_to_category("cat-1", ["img-1", "img-2"]) is True


def test_add_images_to_category_wraps_category_id_in_list():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    client.add_images_to_category("cat-1", ["img-1"])
    body = mock_http.post.call_args.kwargs["json"]
    assert body["add_category_ids"] == ["cat-1"]
    assert body["image_ids"] == ["img-1"]


def test_add_images_to_category_returns_false_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.add_images_to_category("cat-1", ["img-1"]) is False


def test_add_images_to_category_returns_false_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.add_images_to_category("cat-1", ["img-1"]) is False


# ---------------------------------------------------------------------------
# fetch_image_categories
# ---------------------------------------------------------------------------


def test_fetch_image_categories_returns_list():
    client, mock_http = make_sync_client()
    cats = [{"id": "cat-1", "name": "Architecture"}]
    mock_http.get.return_value = mock_response(200, {"success": True, "data": cats})
    assert client.fetch_image_categories("img-1") == cats


def test_fetch_image_categories_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "not_found", "message": "missing"}}
    )
    assert client.fetch_image_categories("img-1") is None


def test_fetch_image_categories_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.fetch_image_categories("img-1") is None


# ---------------------------------------------------------------------------
# bulk_modify_categories
# ---------------------------------------------------------------------------


def test_bulk_modify_categories_returns_true_on_success():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    assert client.bulk_modify_categories(["img-1"], ["cat-1"], []) is True


def test_bulk_modify_categories_posts_correct_body():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    client.bulk_modify_categories(["img-1"], ["cat-a"], ["cat-b"])
    body = mock_http.post.call_args.kwargs["json"]
    assert body == {
        "image_ids": ["img-1"],
        "add_category_ids": ["cat-a"],
        "remove_category_ids": ["cat-b"],
    }


def test_bulk_modify_categories_returns_false_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.bulk_modify_categories(["img-1"], ["cat-1"], []) is False


def test_bulk_modify_categories_returns_false_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.bulk_modify_categories(["img-1"], ["cat-1"], []) is False


# ---------------------------------------------------------------------------
# list_collections
# ---------------------------------------------------------------------------


def test_list_collections_returns_list():
    client, mock_http = make_sync_client()
    cols = [{"id": "col-1", "name": "Mood Board"}]
    mock_http.get.return_value = mock_response(200, {"success": True, "data": cols})
    assert client.list_collections() == cols


def test_list_collections_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.list_collections() is None


def test_list_collections_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.list_collections() is None


# ---------------------------------------------------------------------------
# create_collection
# ---------------------------------------------------------------------------


def test_create_collection_returns_collection_data():
    client, mock_http = make_sync_client()
    col = {"id": "col-1", "name": "Mood Board"}
    mock_http.post.return_value = mock_response(200, {"success": True, "data": col})
    assert client.create_collection("Mood Board") == col


def test_create_collection_posts_name():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    client.create_collection("Mood Board")
    body = mock_http.post.call_args.kwargs["json"]
    assert body == {"name": "Mood Board"}


def test_create_collection_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.create_collection("Mood Board") is None


def test_create_collection_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.create_collection("Mood Board") is None


# ---------------------------------------------------------------------------
# add_images_to_collection
# ---------------------------------------------------------------------------


def test_add_images_to_collection_returns_true_on_success():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    assert client.add_images_to_collection("col-1", ["img-1", "img-2"]) is True


def test_add_images_to_collection_posts_correct_body():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    client.add_images_to_collection("col-1", ["img-1", "img-2"])
    body = mock_http.post.call_args.kwargs["json"]
    assert body == {"image_ids": ["img-1", "img-2"]}


def test_add_images_to_collection_uses_correct_url():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(200, {"success": True, "data": {}})
    client.add_images_to_collection("col-1", ["img-1"])
    url = mock_http.post.call_args.args[0]
    assert url == "/api/v1/collections/col-1/images"


def test_add_images_to_collection_returns_false_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.post.return_value = mock_response(
        200, {"success": False, "error": {"code": "server_error", "message": "oops"}}
    )
    assert client.add_images_to_collection("col-1", ["img-1"]) is False


def test_add_images_to_collection_returns_false_on_exception():
    client, mock_http = make_sync_client()
    mock_http.post.side_effect = Exception("timeout")
    assert client.add_images_to_collection("col-1", ["img-1"]) is False


# ---------------------------------------------------------------------------
# fetch_collection_images
# ---------------------------------------------------------------------------


def test_fetch_collection_images_returns_list():
    client, mock_http = make_sync_client()
    images = [{"id": "img-1", "filename": "photo.jpg"}]
    mock_http.get.return_value = mock_response(200, {"success": True, "data": images})
    assert client.fetch_collection_images("col-1") == images


def test_fetch_collection_images_passes_grid_view_param():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(200, {"success": True, "data": []})
    client.fetch_collection_images("col-1")
    params = mock_http.get.call_args.kwargs["params"]
    assert params.get("view") == "grid"


def test_fetch_collection_images_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "not_found", "message": "missing"}}
    )
    assert client.fetch_collection_images("col-1") is None


def test_fetch_collection_images_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.fetch_collection_images("col-1") is None


# ---------------------------------------------------------------------------
# fetch_image_collections
# ---------------------------------------------------------------------------


def test_fetch_image_collections_returns_list():
    client, mock_http = make_sync_client()
    cols = [{"id": "col-1", "name": "Mood Board"}]
    mock_http.get.return_value = mock_response(200, {"success": True, "data": cols})
    assert client.fetch_image_collections("img-1") == cols


def test_fetch_image_collections_returns_none_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.get.return_value = mock_response(
        200, {"success": False, "error": {"code": "not_found", "message": "missing"}}
    )
    assert client.fetch_image_collections("img-1") is None


def test_fetch_image_collections_returns_none_on_exception():
    client, mock_http = make_sync_client()
    mock_http.get.side_effect = Exception("timeout")
    assert client.fetch_image_collections("img-1") is None


# ---------------------------------------------------------------------------
# remove_image_from_collection
# ---------------------------------------------------------------------------


def test_remove_image_from_collection_returns_true_on_success():
    client, mock_http = make_sync_client()
    mock_http.delete.return_value = mock_response(200, {"success": True, "data": {}})
    assert client.remove_image_from_collection("col-1", "img-1") is True


def test_remove_image_from_collection_uses_correct_url():
    client, mock_http = make_sync_client()
    mock_http.delete.return_value = mock_response(200, {"success": True, "data": {}})
    client.remove_image_from_collection("col-1", "img-1")
    url = mock_http.delete.call_args.args[0]
    assert url == "/api/v1/collections/col-1/images/img-1"


def test_remove_image_from_collection_returns_false_on_api_failure():
    client, mock_http = make_sync_client()
    mock_http.delete.return_value = mock_response(
        200, {"success": False, "error": {"code": "not_found", "message": "missing"}}
    )
    assert client.remove_image_from_collection("col-1", "img-1") is False


def test_remove_image_from_collection_returns_false_on_exception():
    client, mock_http = make_sync_client()
    mock_http.delete.side_effect = Exception("timeout")
    assert client.remove_image_from_collection("col-1", "img-1") is False
