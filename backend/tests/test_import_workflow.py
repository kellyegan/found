import shutil

import pytest
from PIL import Image as PILImage


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / "photo.jpg"
    PILImage.new("RGB", (800, 600)).save(path, "JPEG")
    return path


# ── Job results ───────────────────────────────────────────────────────────────

def test_successful_import_sets_import_job_id(client, image_file):
    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(image_file)]}
    ).json()["data"]["job_id"]

    images = client.get(f"/api/v1/images?import_job={job_id}").json()["data"]
    assert len(images) == 1
    assert images[0]["import_job_id"] == job_id


def test_import_job_filter_isolates_by_job(client, tmp_path):
    img_a = tmp_path / "a.jpg"
    img_b = tmp_path / "b.jpg"
    PILImage.new("RGB", (10, 10)).save(img_a, "JPEG")
    PILImage.new("RGB", (20, 20)).save(img_b, "JPEG")

    job_a = client.post("/api/v1/images/import", json={"paths": [str(img_a)]}).json()["data"]["job_id"]
    job_b = client.post("/api/v1/images/import", json={"paths": [str(img_b)]}).json()["data"]["job_id"]

    assert len(client.get(f"/api/v1/images?import_job={job_a}").json()["data"]) == 1
    assert len(client.get(f"/api/v1/images?import_job={job_b}").json()["data"]) == 1


def test_duplicate_hash_creates_result_record(client, image_file, tmp_path):
    client.post("/api/v1/images/import", json={"paths": [str(image_file)]})

    copy_path = tmp_path / "copy.jpg"
    shutil.copy(image_file, copy_path)

    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(copy_path)]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["duplicate_hashes"] == 1
    assert len(job["results"]) == 1

    result = job["results"][0]
    assert result["outcome"] == "duplicate_hash"
    assert result["path"] == str(copy_path)
    assert result["existing_image_id"] is not None


def test_failed_import_creates_result_record(client, tmp_path):
    bad = tmp_path / "broken.txt"
    bad.write_text("not an image")

    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(bad)]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["failed_imports"] == 1
    assert len(job["results"]) == 1

    result = job["results"][0]
    assert result["outcome"] == "failed"
    assert result["path"] == str(bad)
    assert result["existing_image_id"] is None


def test_duplicate_path_has_no_result_record(client, image_file):
    client.post("/api/v1/images/import", json={"paths": [str(image_file)]})

    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(image_file)]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["duplicate_paths"] == 1
    assert job["results"] == []


def test_job_results_empty_for_all_successes(client, image_file):
    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(image_file)]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["successful_imports"] == 1
    assert job["results"] == []


def test_job_incremental_progress(client, tmp_path):
    """processed_files increments per file — job is live-pollable during import."""
    paths = []
    for i in range(3):
        p = tmp_path / f"img{i}.jpg"
        PILImage.new("RGB", (10, 10)).save(p, "JPEG")
        paths.append(str(p))

    job_id = client.post(
        "/api/v1/images/import", json={"paths": paths}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["processed_files"] == 3
    assert job["total_files"] == 3


# ── PATCH /images/{image_id} ──────────────────────────────────────────────────

def test_patch_image_path(client, image_file, make_image, tmp_path):
    image = make_image(str(image_file))
    new_path = str(tmp_path / "renamed.jpg")

    response = client.patch(f"/api/v1/images/{image.id}", json={"path": new_path})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["path"] == new_path
    assert data["filename"] == "renamed.jpg"


def test_patch_image_path_not_found(client):
    response = client.patch(
        "/api/v1/images/00000000-0000-0000-0000-000000000000",
        json={"path": "/some/path.jpg"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_patch_resolves_duplicate_hash(client, image_file, tmp_path):
    """Full workflow: import, detect duplicate hash, patch the existing record's path."""
    client.post("/api/v1/images/import", json={"paths": [str(image_file)]})

    copy_path = tmp_path / "moved.jpg"
    shutil.copy(image_file, copy_path)

    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(copy_path)]}
    ).json()["data"]["job_id"]

    result = client.get(f"/api/v1/jobs/{job_id}").json()["data"]["results"][0]
    existing_id = result["existing_image_id"]

    patch_response = client.patch(
        f"/api/v1/images/{existing_id}", json={"path": str(copy_path)}
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["path"] == str(copy_path)
