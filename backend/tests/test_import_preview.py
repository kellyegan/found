import shutil

import pytest
from PIL import Image as PILImage


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / "photo.jpg"
    PILImage.new("RGB", (800, 600)).save(path, "JPEG")
    return path


def test_preview_new_images_in_new_bucket(client, image_file):
    response = client.post("/api/v1/images/import/preview", json={"paths": [str(image_file)]})
    assert response.status_code == 200
    data = response.json()["data"]
    assert str(image_file) in data["new"]
    assert data["already_imported"] == []
    assert data["conflicts"] == []
    assert data["invalid"] == []


def test_preview_makes_no_db_writes(client, image_file):
    client.post("/api/v1/images/import/preview", json={"paths": [str(image_file)]})
    assert client.get("/api/v1/images").json()["data"] == []


def test_preview_detects_already_imported_path(client, image_file):
    client.post("/api/v1/images/import", json={"paths": [str(image_file)]})

    response = client.post("/api/v1/images/import/preview", json={"paths": [str(image_file)]})
    data = response.json()["data"]
    assert str(image_file) in data["already_imported"]
    assert data["new"] == []
    assert data["conflicts"] == []


def test_preview_detects_hash_conflict(client, image_file, tmp_path):
    client.post("/api/v1/images/import", json={"paths": [str(image_file)]})

    copy_path = tmp_path / "copy.jpg"
    shutil.copy(image_file, copy_path)

    response = client.post("/api/v1/images/import/preview", json={"paths": [str(copy_path)]})
    data = response.json()["data"]
    assert len(data["conflicts"]) == 1
    conflict = data["conflicts"][0]
    assert conflict["path"] == str(copy_path)
    assert conflict["existing_path"] == str(image_file)
    assert conflict["existing_filename"] == "photo.jpg"
    assert conflict["existing_image_id"] is not None
    assert data["new"] == []
    assert data["already_imported"] == []


def test_preview_detects_invalid_file(client, tmp_path):
    bad = tmp_path / "broken.txt"
    bad.write_text("not an image")

    response = client.post("/api/v1/images/import/preview", json={"paths": [str(bad)]})
    data = response.json()["data"]
    assert str(bad) in data["invalid"]
    assert data["new"] == []
    assert data["conflicts"] == []


def test_preview_mixed_buckets(client, image_file, tmp_path):
    client.post("/api/v1/images/import", json={"paths": [str(image_file)]})

    new_img = tmp_path / "new.jpg"
    PILImage.new("RGB", (100, 100)).save(new_img, "JPEG")

    conflict_img = tmp_path / "conflict.jpg"
    shutil.copy(image_file, conflict_img)

    bad = tmp_path / "bad.txt"
    bad.write_text("not an image")

    paths = [str(image_file), str(new_img), str(conflict_img), str(bad)]
    response = client.post("/api/v1/images/import/preview", json={"paths": paths})
    assert response.status_code == 200
    data = response.json()["data"]

    assert str(image_file) in data["already_imported"]
    assert str(new_img) in data["new"]
    assert any(c["path"] == str(conflict_img) for c in data["conflicts"])
    assert str(bad) in data["invalid"]
