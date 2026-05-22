import shutil

import pytest
from PIL import Image as PILImage


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / "photo.jpg"
    PILImage.new("RGB", (800, 600)).save(path, "JPEG")
    return path


def test_import_single_image(client, image_file):
    response = client.post("/api/v1/images/import", json={"paths": [str(image_file)]})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "job_id" in data["data"]

    images = client.get("/api/v1/images").json()["data"]
    assert len(images) == 1
    assert images[0]["filename"] == "photo.jpg"
    assert images[0]["width"] == 800
    assert images[0]["height"] == 600
    assert images[0]["mime_type"] == "image/jpeg"
    assert images[0]["sha256_hash"] is not None


def test_import_job_tracks_progress(client, image_file):
    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(image_file)]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]

    assert job["status"] == "completed"
    assert job["total_files"] == 1
    assert job["successful_imports"] == 1
    assert job["failed_imports"] == 0


def test_duplicate_path_rejected(client, image_file):
    path = str(image_file)
    client.post("/api/v1/images/import", json={"paths": [path]})

    job_id = client.post(
        "/api/v1/images/import", json={"paths": [path]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["duplicate_paths"] == 1
    assert job["successful_imports"] == 0
    assert len(client.get("/api/v1/images").json()["data"]) == 1


def test_duplicate_hash_detection(client, image_file, tmp_path):
    client.post("/api/v1/images/import", json={"paths": [str(image_file)]})

    copy_path = tmp_path / "copy.jpg"
    shutil.copy(image_file, copy_path)

    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(copy_path)]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["duplicate_hashes"] == 1
    assert job["successful_imports"] == 0
    assert len(client.get("/api/v1/images").json()["data"]) == 1


def test_bulk_import_partial_failure(client, image_file, tmp_path):
    bad_path = tmp_path / "broken.txt"
    bad_path.write_text("not an image")

    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(image_file), str(bad_path)]}
    ).json()["data"]["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}").json()["data"]
    assert job["status"] == "completed"
    assert job["total_files"] == 2
    assert job["successful_imports"] == 1
    assert job["failed_imports"] == 1


def test_list_jobs(client, image_file, tmp_path):
    img2 = tmp_path / "other.jpg"
    PILImage.new("RGB", (100, 100)).save(img2, "JPEG")

    client.post("/api/v1/images/import", json={"paths": [str(image_file)]})
    client.post("/api/v1/images/import", json={"paths": [str(img2)]})

    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 2
