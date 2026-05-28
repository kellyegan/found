import os

import pytest
from PIL import Image as PILImage


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / "photo.jpg"
    PILImage.new("RGB", (800, 600)).save(path, "JPEG")
    return path


@pytest.fixture
def imported_image_id(client, image_file):
    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(image_file)]}
    ).json()["data"]["job_id"]
    return client.get(f"/api/v1/images?import_job={job_id}").json()["data"][0]["id"]


def test_file_returns_200_with_image_content(client, imported_image_id):
    response = client.get(f"/api/v1/images/{imported_image_id}/file")
    assert response.status_code == 200
    assert len(response.content) > 0


def test_file_returns_correct_mime_type(client, imported_image_id):
    response = client.get(f"/api/v1/images/{imported_image_id}/file")
    assert response.headers["content-type"].startswith("image/jpeg")


def test_file_unknown_image_id_returns_404(client):
    response = client.get("/api/v1/images/00000000-0000-0000-0000-000000000000/file")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_file_missing_on_disk_returns_404(client, make_image):
    image = make_image("/nonexistent/path/photo.jpg", mime_type="image/jpeg")
    response = client.get(f"/api/v1/images/{image.id}/file")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "file_not_found"


def test_file_unsupported_format_returns_415(client, make_image, tmp_path):
    image = make_image(str(tmp_path / "file.xyz"), mime_type=None)
    response = client.get(f"/api/v1/images/{image.id}/file")
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_format"


def test_file_read_failure_returns_500(client, make_image, tmp_path):
    path = tmp_path / "locked.jpg"
    PILImage.new("RGB", (10, 10)).save(path, "JPEG")
    image = make_image(str(path), mime_type="image/jpeg")
    os.chmod(path, 0o000)
    try:
        response = client.get(f"/api/v1/images/{image.id}/file")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "read_failure"
    finally:
        os.chmod(path, 0o644)
