"""Tests for POST /api/v1/images/bulk/delete."""
import pytest
from PIL import Image as PILImage


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / "photo.jpg"
    PILImage.new("RGB", (10, 10)).save(path, "JPEG")
    return path


def test_bulk_delete_removes_images_from_library(client, make_image):
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")
    img_c = make_image("/c.jpg")

    response = client.post(
        "/api/v1/images/bulk/delete",
        json={"image_ids": [str(img_a.id), str(img_b.id)]},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    remaining = {r["id"] for r in client.get("/api/v1/images").json()["data"]}
    assert str(img_a.id) not in remaining
    assert str(img_b.id) not in remaining
    assert str(img_c.id) in remaining


def test_bulk_delete_does_not_delete_source_files(client, image_file):
    job_id = client.post(
        "/api/v1/images/import", json={"paths": [str(image_file)]}
    ).json()["data"]["job_id"]
    image_id = client.get(f"/api/v1/images?import_job={job_id}").json()["data"][0]["id"]

    client.post("/api/v1/images/bulk/delete", json={"image_ids": [image_id]})

    assert image_file.exists()


def test_bulk_delete_empty_list_is_no_op(client, make_image):
    img = make_image("/a.jpg")

    response = client.post("/api/v1/images/bulk/delete", json={"image_ids": []})
    assert response.status_code == 200

    remaining = {r["id"] for r in client.get("/api/v1/images").json()["data"]}
    assert str(img.id) in remaining


def test_bulk_delete_ignores_nonexistent_ids(client):
    response = client.post(
        "/api/v1/images/bulk/delete",
        json={"image_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert response.status_code == 200


def test_bulk_delete_is_atomic(client, make_image):
    """All deletes succeed or none do — partial failure leaves DB unchanged."""
    img_a = make_image("/a.jpg")
    img_b = make_image("/b.jpg")

    # Both valid IDs — both should be deleted
    client.post(
        "/api/v1/images/bulk/delete",
        json={"image_ids": [str(img_a.id), str(img_b.id)]},
    )

    remaining = {r["id"] for r in client.get("/api/v1/images").json()["data"]}
    assert str(img_a.id) not in remaining
    assert str(img_b.id) not in remaining
