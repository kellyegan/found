"""Grid view mode tests for GET /images?view=grid.

TDD: these tests are written first and should FAIL until the feature is implemented.
"""

FULL_ONLY_FIELDS = {"path", "sha256_hash", "file_size", "mime_type",
                    "created_date", "modified_date", "imported_date", "import_job_id"}
GRID_FIELDS = {"id", "filename", "width", "height", "thumbnail_path", "file_status"}


# ── Grid response shape ────────────────────────────────────────────────────────

def test_grid_view_returns_minimal_fields(client, make_image):
    make_image("/grid/a.jpg")
    resp = client.get("/api/v1/images?view=grid").json()
    assert resp["success"] is True
    item = resp["data"][0]
    for field in GRID_FIELDS:
        assert field in item, f"expected field '{field}' in grid response"


def test_grid_view_excludes_full_metadata_fields(client, make_image):
    make_image("/grid/b.jpg")
    item = client.get("/api/v1/images?view=grid").json()["data"][0]
    for field in FULL_ONLY_FIELDS:
        assert field not in item, f"unexpected field '{field}' in grid response"


def test_default_view_returns_full_metadata(client, make_image):
    make_image("/grid/c.jpg")
    item = client.get("/api/v1/images").json()["data"][0]
    for field in FULL_ONLY_FIELDS | GRID_FIELDS:
        assert field in item, f"expected field '{field}' in full response"


def test_grid_view_explicit_full_returns_full_metadata(client, make_image):
    make_image("/grid/d.jpg")
    item = client.get("/api/v1/images?view=full").json()["data"][0]
    for field in FULL_ONLY_FIELDS | GRID_FIELDS:
        assert field in item, f"expected field '{field}' in full response"


# ── Grid composes with pagination and filters ──────────────────────────────────

def test_grid_view_composes_with_cursor(client, make_image):
    from datetime import datetime, timezone, timedelta
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(4):
        make_image(f"/grid/pag{i}.jpg", imported_date=base + timedelta(seconds=i))

    resp1 = client.get("/api/v1/images?view=grid&limit=2").json()
    assert resp1["has_more"] is True
    assert len(resp1["data"]) == 2
    assert "id" in resp1["data"][0]
    assert "path" not in resp1["data"][0]

    resp2 = client.get(f"/api/v1/images?view=grid&limit=2&cursor={resp1['next_cursor']}").json()
    assert resp2["has_more"] is False
    assert len(resp2["data"]) == 2


def test_grid_view_composes_with_tag_filter(client, make_image):
    img = make_image("/grid/tagged.jpg")
    make_image("/grid/untagged.jpg")
    tag_id = client.post("/api/v1/tags", json={"name": "portrait"}).json()["data"]["id"]
    client.post(f"/api/v1/images/{img.id}/tags", json={"tag_ids": [tag_id]})

    result = client.get("/api/v1/images?view=grid&tags=portrait").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == str(img.id)
    assert "path" not in result[0]
