import pytest
from PIL import Image as PILImage


def test_extract_metadata_jpeg(tmp_path):
    img_path = tmp_path / "sample.jpg"
    PILImage.new("RGB", (800, 600)).save(img_path, "JPEG")

    from app.services.metadata_service import extract_metadata

    meta = extract_metadata(str(img_path))

    assert meta.width == 800
    assert meta.height == 600
    assert meta.mime_type == "image/jpeg"
    assert meta.file_size > 0


def test_extract_metadata_png(tmp_path):
    img_path = tmp_path / "sample.png"
    PILImage.new("RGB", (400, 300)).save(img_path, "PNG")

    from app.services.metadata_service import extract_metadata

    meta = extract_metadata(str(img_path))

    assert meta.width == 400
    assert meta.height == 300
    assert meta.mime_type == "image/png"


def test_extract_metadata_webp(tmp_path):
    img_path = tmp_path / "sample.webp"
    PILImage.new("RGB", (640, 480)).save(img_path, "WEBP")

    from app.services.metadata_service import extract_metadata

    meta = extract_metadata(str(img_path))

    assert meta.width == 640
    assert meta.height == 480
    assert meta.mime_type == "image/webp"
    assert meta.file_size > 0


def test_extract_metadata_tiff(tmp_path):
    img_path = tmp_path / "sample.tiff"
    PILImage.new("RGB", (320, 240)).save(img_path, "TIFF")

    from app.services.metadata_service import extract_metadata

    meta = extract_metadata(str(img_path))

    assert meta.width == 320
    assert meta.height == 240
    assert meta.mime_type == "image/tiff"
    assert meta.file_size > 0


def test_unsupported_file_type_rejected(tmp_path):
    bad_path = tmp_path / "document.txt"
    bad_path.write_text("not an image")

    from app.services.metadata_service import UnsupportedFileTypeError, extract_metadata

    with pytest.raises(UnsupportedFileTypeError):
        extract_metadata(str(bad_path))


def test_missing_file_detection(client, make_image):
    image = make_image("/nonexistent/ghost.jpg")

    response = client.post(f"/api/v1/images/{image.id}/verify")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["file_status"] == "missing"


def test_available_file_detection(client, make_image, tmp_path):
    img_path = tmp_path / "real.jpg"
    PILImage.new("RGB", (100, 100)).save(img_path, "JPEG")

    image = make_image(str(img_path))

    response = client.post(f"/api/v1/images/{image.id}/verify")

    assert response.status_code == 200
    assert response.json()["data"]["file_status"] == "available"
