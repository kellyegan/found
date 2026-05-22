import pytest
from PIL import Image as PILImage


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_image(client, filename, path):
    return client.post(
        "/api/v1/images", json={"filename": filename, "path": path}
    ).json()["data"]["id"]


# ── Job lifecycle ─────────────────────────────────────────────────────────────

def test_job_lifecycle(client, tmp_path):
    img = tmp_path / "photo.jpg"
    PILImage.new("RGB", (100, 100)).save(img, "JPEG")

    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(img)]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["status"] == "completed"
    assert job["processed_files"] == job["total_files"]
    assert job["successful_imports"] + job["duplicate_paths"] + job["duplicate_hashes"] + job["failed_imports"] == job["total_files"]


def test_failed_files_do_not_affect_job_completion(client, tmp_path):
    good = tmp_path / "good.jpg"
    PILImage.new("RGB", (100, 100)).save(good, "JPEG")
    bad = tmp_path / "bad.txt"
    bad.write_text("not an image")

    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(good), str(bad)]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["status"] == "completed"
    assert job["successful_imports"] == 1
    assert job["failed_imports"] == 1


# ── Stable ordering ───────────────────────────────────────────────────────────

def test_list_images_stable_ordering(client):
    for i in range(5):
        _make_image(client, f"img{i}.jpg", f"/photos/img{i}.jpg")

    first  = [img["id"] for img in client.get("/api/v1/images").json()["data"]]
    second = [img["id"] for img in client.get("/api/v1/images").json()["data"]]
    assert first == second


def test_pagination_is_consistent_with_ordering(client):
    for i in range(6):
        _make_image(client, f"p{i}.jpg", f"/photos/p{i}.jpg")

    all_ids   = [img["id"] for img in client.get("/api/v1/images?limit=10").json()["data"]]
    page_1    = [img["id"] for img in client.get("/api/v1/images?offset=0&limit=3").json()["data"]]
    page_2    = [img["id"] for img in client.get("/api/v1/images?offset=3&limit=3").json()["data"]]

    assert page_1 + page_2 == all_ids


# ── Filtering ─────────────────────────────────────────────────────────────────

def test_filter_by_tag(client):
    img_a = _make_image(client, "a.jpg", "/filter/a.jpg")
    img_b = _make_image(client, "b.jpg", "/filter/b.jpg")

    tag_id = client.post("/api/v1/tags", json={"name": "nature"}).json()["data"]["id"]
    client.post(f"/api/v1/images/{img_a}/tags", json={"tag_ids": [tag_id]})

    result = client.get("/api/v1/images?tag=nature").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_filter_by_tag_is_case_insensitive(client):
    img_a = _make_image(client, "c.jpg", "/filter/c.jpg")
    tag_id = client.post("/api/v1/tags", json={"name": "urban"}).json()["data"]["id"]
    client.post(f"/api/v1/images/{img_a}/tags", json={"tag_ids": [tag_id]})

    result = client.get("/api/v1/images?tag=URBAN").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_filter_by_category(client):
    img_a = _make_image(client, "d.jpg", "/filter/d.jpg")
    _make_image(client, "e.jpg", "/filter/e.jpg")

    cat_id = client.post(
        "/api/v1/categories", json={"name": "Architecture", "description": ""}
    ).json()["data"]["id"]
    client.post(f"/api/v1/images/{img_a}/categories", json={"category_ids": [cat_id]})

    result = client.get("/api/v1/images?category=Architecture").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_filter_by_collection(client):
    img_a = _make_image(client, "f.jpg", "/filter/f.jpg")
    _make_image(client, "g.jpg", "/filter/g.jpg")

    col_id = client.post(
        "/api/v1/collections", json={"name": "Picks", "description": ""}
    ).json()["data"]["id"]
    client.post(f"/api/v1/collections/{col_id}/images", json={"image_ids": [img_a]})

    result = client.get(f"/api/v1/images?collection={col_id}").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_no_filter_returns_all(client):
    for i in range(4):
        _make_image(client, f"h{i}.jpg", f"/filter/h{i}.jpg")

    result = client.get("/api/v1/images").json()["data"]
    assert len(result) == 4
