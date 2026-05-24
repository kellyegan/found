import pytest
from PIL import Image as PILImage


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

def test_list_images_stable_ordering(client, make_image):
    for i in range(5):
        make_image(f"/photos/img{i}.jpg")

    first  = [img["id"] for img in client.get("/api/v1/images").json()["data"]]
    second = [img["id"] for img in client.get("/api/v1/images").json()["data"]]
    assert first == second


def test_pagination_is_consistent_with_ordering(client, make_image):
    for i in range(6):
        make_image(f"/photos/p{i}.jpg")

    all_ids   = [img["id"] for img in client.get("/api/v1/images?limit=10").json()["data"]]
    page_1    = [img["id"] for img in client.get("/api/v1/images?offset=0&limit=3").json()["data"]]
    page_2    = [img["id"] for img in client.get("/api/v1/images?offset=3&limit=3").json()["data"]]

    assert page_1 + page_2 == all_ids


# ── Filtering ─────────────────────────────────────────────────────────────────

def test_filter_by_tag(client, make_image):
    img_a = str(make_image("/filter/a.jpg").id)
    img_b = str(make_image("/filter/b.jpg").id)

    tag_id = client.post("/api/v1/tags", json={"name": "nature"}).json()["data"]["id"]
    client.post(f"/api/v1/images/{img_a}/tags", json={"tag_ids": [tag_id]})

    result = client.get("/api/v1/images?tag=nature").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_filter_by_tag_is_case_insensitive(client, make_image):
    img_a = str(make_image("/filter/c.jpg").id)
    tag_id = client.post("/api/v1/tags", json={"name": "urban"}).json()["data"]["id"]
    client.post(f"/api/v1/images/{img_a}/tags", json={"tag_ids": [tag_id]})

    result = client.get("/api/v1/images?tag=URBAN").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_filter_by_category(client, make_image):
    img_a = str(make_image("/filter/d.jpg").id)
    make_image("/filter/e.jpg")

    cat_id = client.post(
        "/api/v1/categories", json={"name": "Architecture", "description": ""}
    ).json()["data"]["id"]
    client.post(f"/api/v1/images/{img_a}/categories", json={"category_ids": [cat_id]})

    result = client.get("/api/v1/images?category=Architecture").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_filter_by_collection(client, make_image):
    img_a = str(make_image("/filter/f.jpg").id)
    make_image("/filter/g.jpg")

    col_id = client.post(
        "/api/v1/collections", json={"name": "Picks", "description": ""}
    ).json()["data"]["id"]
    client.post(f"/api/v1/collections/{col_id}/images", json={"image_ids": [img_a]})

    result = client.get(f"/api/v1/images?collection={col_id}").json()["data"]
    assert len(result) == 1
    assert result[0]["id"] == img_a


def test_no_filter_returns_all(client, make_image):
    for i in range(4):
        make_image(f"/filter/h{i}.jpg")

    result = client.get("/api/v1/images").json()["data"]
    assert len(result) == 4
