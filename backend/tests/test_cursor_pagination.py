"""Cursor pagination tests for GET /images.

TDD: these tests are written first and should FAIL until the feature is implemented.
"""
from datetime import datetime, timezone, timedelta


def _make_images_ordered(make_image, count):
    """Create `count` images with distinct imported_dates so ordering is deterministic."""
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    images = []
    for i in range(count):
        images.append(
            make_image(f"/pag/img{i}.jpg", imported_date=base + timedelta(seconds=i))
        )
    return images


# ── Stable ordering ───────────────────────────────────────────────────────────

def test_list_images_stable_ordering(client, make_image):
    for i in range(5):
        make_image(f"/photos/img{i}.jpg")

    first  = [img["id"] for img in client.get("/api/v1/images").json()["data"]]
    second = [img["id"] for img in client.get("/api/v1/images").json()["data"]]
    assert first == second


# ── Basic cursor structure ─────────────────────────────────────────────────────

def test_first_page_returns_has_more_and_next_cursor(client, make_image):
    _make_images_ordered(make_image, 5)

    resp = client.get("/api/v1/images?limit=3").json()
    assert resp["success"] is True
    assert len(resp["data"]) == 3
    assert resp["has_more"] is True
    assert resp["next_cursor"] is not None
    assert isinstance(resp["next_cursor"], str)


def test_last_page_has_no_next_cursor(client, make_image):
    _make_images_ordered(make_image, 3)

    resp = client.get("/api/v1/images?limit=10").json()
    assert resp["success"] is True
    assert len(resp["data"]) == 3
    assert resp["has_more"] is False
    assert resp["next_cursor"] is None


def test_cursor_is_opaque_string(client, make_image):
    """The cursor is a base64 string, not raw JSON or a plain ID."""
    import base64
    import json

    _make_images_ordered(make_image, 2)
    resp = client.get("/api/v1/images?limit=1").json()
    cursor = resp["next_cursor"]

    # Should be decodable as base64 JSON but not already be plain JSON
    assert "{" not in cursor  # not raw JSON
    decoded = json.loads(base64.urlsafe_b64decode(cursor + "=="))
    assert "d" in decoded  # date field
    assert "i" in decoded  # id field


# ── Traversal ─────────────────────────────────────────────────────────────────

def test_cursor_traversal_yields_all_images_without_duplicates(client, make_image):
    images = _make_images_ordered(make_image, 7)
    expected_ids = [str(img.id) for img in images]

    collected = []
    cursor = None
    while True:
        url = "/api/v1/images?limit=3"
        if cursor:
            url += f"&cursor={cursor}"
        resp = client.get(url).json()
        collected.extend(img["id"] for img in resp["data"])
        if not resp["has_more"]:
            break
        cursor = resp["next_cursor"]

    assert len(collected) == len(expected_ids)
    assert set(collected) == set(expected_ids)
    assert collected == expected_ids  # no duplicates, stable order


def test_cursor_traversal_consistent_with_full_list(client, make_image):
    _make_images_ordered(make_image, 6)

    all_ids = [img["id"] for img in client.get("/api/v1/images?limit=100").json()["data"]]

    page1_resp = client.get("/api/v1/images?limit=3").json()
    page1_ids = [img["id"] for img in page1_resp["data"]]
    cursor = page1_resp["next_cursor"]

    page2_resp = client.get(f"/api/v1/images?limit=3&cursor={cursor}").json()
    page2_ids = [img["id"] for img in page2_resp["data"]]

    assert page1_ids + page2_ids == all_ids


# ── Offset param removed ───────────────────────────────────────────────────────

def test_offset_param_is_ignored_or_absent(client, make_image):
    """offset is no longer a supported parameter — passing it should not paginate.
    The endpoint should behave as if no offset was given (i.e. return from the start)."""
    _make_images_ordered(make_image, 4)

    # offset should have no effect; result should equal first page without cursor
    with_offset = client.get("/api/v1/images?limit=4&offset=2").json()
    without_offset = client.get("/api/v1/images?limit=4").json()
    assert [i["id"] for i in with_offset["data"]] == [i["id"] for i in without_offset["data"]]


# ── Filters compose with cursor ────────────────────────────────────────────────

def test_tag_filter_composes_with_cursor(client, make_image):
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    tagged = []
    for i in range(6):
        img = make_image(f"/tag_pag/img{i}.jpg", imported_date=base + timedelta(seconds=i))
        if i % 2 == 0:
            tagged.append(img)

    tag_id = client.post("/api/v1/tags", json={"name": "even"}).json()["data"]["id"]
    for img in tagged:
        client.post(f"/api/v1/images/{img.id}/tags", json={"tag_ids": [tag_id]})

    resp1 = client.get("/api/v1/images?tags=even&limit=2").json()
    assert len(resp1["data"]) == 2
    assert resp1["has_more"] is True

    resp2 = client.get(f"/api/v1/images?tags=even&limit=2&cursor={resp1['next_cursor']}").json()
    assert len(resp2["data"]) == 1
    assert resp2["has_more"] is False

    all_ids = [str(img.id) for img in tagged]
    page_ids = [i["id"] for i in resp1["data"]] + [i["id"] for i in resp2["data"]]
    assert set(page_ids) == set(all_ids)


def test_category_filter_composes_with_cursor(client, make_image):
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    categorised = []
    for i in range(6):
        img = make_image(f"/cat_pag/img{i}.jpg", imported_date=base + timedelta(seconds=i))
        if i % 2 == 0:
            categorised.append(img)

    cat_id = client.post(
        "/api/v1/categories", json={"name": "Landscape", "description": ""}
    ).json()["data"]["id"]
    for img in categorised:
        client.post(f"/api/v1/images/{img.id}/categories", json={"category_ids": [cat_id]})

    resp1 = client.get(f"/api/v1/images?categories={cat_id}&limit=2").json()
    assert len(resp1["data"]) == 2
    assert resp1["has_more"] is True

    resp2 = client.get(
        f"/api/v1/images?categories={cat_id}&limit=2&cursor={resp1['next_cursor']}"
    ).json()
    assert len(resp2["data"]) == 1
    assert resp2["has_more"] is False

    all_ids = [str(img.id) for img in categorised]
    page_ids = [i["id"] for i in resp1["data"]] + [i["id"] for i in resp2["data"]]
    assert set(page_ids) == set(all_ids)


def test_missing_filter_composes_with_cursor(client, make_image):
    from app.models.image import FileStatus
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(4):
        status = FileStatus.missing if i < 3 else FileStatus.available
        make_image(f"/miss_pag/img{i}.jpg", imported_date=base + timedelta(seconds=i), file_status=status)

    resp1 = client.get("/api/v1/images?missing=true&limit=2").json()
    assert len(resp1["data"]) == 2
    assert resp1["has_more"] is True

    resp2 = client.get(f"/api/v1/images?missing=true&limit=2&cursor={resp1['next_cursor']}").json()
    assert len(resp2["data"]) == 1
    assert resp2["has_more"] is False
