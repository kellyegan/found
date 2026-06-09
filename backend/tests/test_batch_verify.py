"""Tests for POST /api/v1/images/verify."""
import pytest
from PIL import Image as PILImage

from app.models.image import FileStatus


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / "photo.jpg"
    PILImage.new("RGB", (100, 100)).save(path, "JPEG")
    return path


@pytest.fixture
def imported_image(client, image_file):
    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(image_file)]}
    ).json()["data"]["job_id"]
    return client.get(f"/api/v1/images?import_job={job_id}").json()["data"][0]


def test_verify_marks_missing_file_as_missing(client, imported_image, image_file):
    image_file.unlink()

    response = client.post(
        "/api/v1/images/verify",
        json={"image_ids": [imported_image["id"]]},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    updated = client.get(f"/api/v1/images/{imported_image['id']}").json()["data"]
    assert updated["file_status"] == FileStatus.missing


def test_verify_marks_available_file_as_available(client, make_image, image_file):
    image = make_image(str(image_file), file_status=FileStatus.missing)

    client.post("/api/v1/images/verify", json={"image_ids": [str(image.id)]})

    updated = client.get(f"/api/v1/images/{image.id}").json()["data"]
    assert updated["file_status"] == FileStatus.available


def test_verify_refreshes_metadata_when_file_replaced(client, imported_image, image_file):
    assert imported_image["width"] == 100
    assert imported_image["height"] == 100

    # Replace with a differently-sized image at the same path
    PILImage.new("RGB", (800, 600)).save(image_file, "JPEG")

    client.post("/api/v1/images/verify", json={"image_ids": [imported_image["id"]]})

    updated = client.get(f"/api/v1/images/{imported_image['id']}").json()["data"]
    assert updated["width"] == 800
    assert updated["height"] == 600
    assert updated["file_size"] != imported_image["file_size"]


def test_verify_ignores_nonexistent_image_ids(client):
    response = client.post(
        "/api/v1/images/verify",
        json={"image_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert response.status_code == 200


def test_verify_empty_list_is_no_op(client, make_image):
    img = make_image("/a.jpg")

    response = client.post("/api/v1/images/verify", json={"image_ids": []})
    assert response.status_code == 200

    unchanged = client.get(f"/api/v1/images/{img.id}").json()["data"]
    assert unchanged["file_status"] == FileStatus.available


def test_verify_processes_multiple_images(client, make_image, tmp_path):
    existing = tmp_path / "exists.jpg"
    PILImage.new("RGB", (10, 10)).save(existing, "JPEG")

    img_present = make_image(str(existing), file_status=FileStatus.missing)
    img_gone    = make_image("/nonexistent/gone.jpg", file_status=FileStatus.available)

    client.post(
        "/api/v1/images/verify",
        json={"image_ids": [str(img_present.id), str(img_gone.id)]},
    )

    assert client.get(f"/api/v1/images/{img_present.id}").json()["data"]["file_status"] == FileStatus.available
    assert client.get(f"/api/v1/images/{img_gone.id}").json()["data"]["file_status"] == FileStatus.missing


def test_verify_response_includes_results(client, make_image, tmp_path):
    existing = tmp_path / "exists.jpg"
    PILImage.new("RGB", (10, 10)).save(existing, "JPEG")

    img_present = make_image(str(existing), file_status=FileStatus.missing)
    img_gone    = make_image("/nonexistent/gone.jpg", file_status=FileStatus.available)

    response = client.post(
        "/api/v1/images/verify",
        json={"image_ids": [str(img_present.id), str(img_gone.id)]},
    )
    data = response.json()
    assert data["success"] is True
    results = {r["id"]: r["file_status"] for r in data["data"]["results"]}
    assert results[str(img_present.id)] == FileStatus.available
    assert results[str(img_gone.id)] == FileStatus.missing


def test_verify_response_results_empty_for_empty_input(client):
    response = client.post("/api/v1/images/verify", json={"image_ids": []})
    data = response.json()
    assert data["success"] is True
    assert data["data"]["results"] == []
