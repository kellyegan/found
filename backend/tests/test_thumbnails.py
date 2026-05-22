from pathlib import Path

import pytest
from PIL import Image as PILImage


@pytest.fixture
def imported_image(client, tmp_path):
    """Import a real JPEG and return its image record."""
    img_path = tmp_path / "photo.jpg"
    PILImage.new("RGB", (800, 600)).save(img_path, "JPEG")
    client.post("/api/v1/images/import", json={"paths": [str(img_path)]})
    return client.get("/api/v1/images").json()["data"][0]


def test_thumbnail_created_on_import(imported_image):
    assert imported_image["thumbnail_path"] is not None
    assert Path(imported_image["thumbnail_path"]).exists()


def test_thumbnail_is_correct_size(imported_image):
    thumb_path = imported_image["thumbnail_path"]
    with PILImage.open(thumb_path) as img:
        assert img.width <= 512
        assert img.height <= 512


def test_thumbnail_retrieval(client, imported_image):
    image_id = imported_image["id"]
    response = client.get(f"/api/v1/images/{image_id}/thumbnail")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_thumbnail_not_regenerated_on_second_request(client, imported_image):
    image_id = imported_image["id"]
    thumb_path = Path(imported_image["thumbnail_path"])

    client.get(f"/api/v1/images/{image_id}/thumbnail")
    mtime_1 = thumb_path.stat().st_mtime

    client.get(f"/api/v1/images/{image_id}/thumbnail")
    mtime_2 = thumb_path.stat().st_mtime

    assert mtime_1 == mtime_2


def test_thumbnail_regenerated_when_file_missing(client, imported_image):
    image_id = imported_image["id"]
    thumb_path = Path(imported_image["thumbnail_path"])
    thumb_path.unlink()

    response = client.get(f"/api/v1/images/{image_id}/thumbnail")

    assert response.status_code == 200
    assert thumb_path.exists()
