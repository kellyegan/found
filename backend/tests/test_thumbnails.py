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


def test_generate_thumbnail_succeeds_for_16bit_tiff(tmp_path):
    """16-bit grayscale TIFFs (mode I;16) must produce a valid, non-white thumbnail.

    Two bugs affect I;16 images from scanners/DSLRs:
    1. thumbnail() raises ValueError for large downscales (>~6x) — 3000×3000
       → 512 reliably triggers this.
    2. convert('RGB') clips values > 255, turning real-data images all white.

    The fix converts I;16 → I (preserves values) → thumbnail → scale
    0-65535 to 0-255 → L → RGB → JPEG.
    """
    from app.services.thumbnail_service import generate_thumbnail

    img_path = tmp_path / "scan.tif"
    # Vertical gradient: top row all-black (value 0), bottom row all-white (65535).
    # This verifies both that the image generates and that values aren't clipped.
    size = 3000
    img = PILImage.new("I;16", (size, size))
    img.putdata([int(y / size * 65535) for y in range(size) for _ in range(size)])
    img.save(img_path)

    thumb_path = generate_thumbnail(str(img_path), "aabbccdd", str(tmp_path))

    assert Path(thumb_path).exists()
    with PILImage.open(thumb_path) as t:
        assert t.width <= 512
        assert t.height <= 512
        # The gradient must be preserved: top pixels dark, bottom pixels bright.
        # If values were clipped to 255 the whole image would be white.
        pixels = list(t.convert("L").tobytes())
        top_avg = sum(pixels[:t.width]) / t.width
        bot_avg = sum(pixels[-t.width:]) / t.width
        assert top_avg < 50, f"Top row should be dark (avg {top_avg:.1f})"
        assert bot_avg > 200, f"Bottom row should be bright (avg {bot_avg:.1f})"


def test_generate_thumbnail_succeeds_for_oversized_image(tmp_path, monkeypatch):
    """Must produce a thumbnail even when PIL's pixel limit is breached.

    Setting MAX_IMAGE_PIXELS=1 simulates a gigapixel file without needing one.
    """
    import PIL.Image as PILModule
    from app.services.thumbnail_service import generate_thumbnail

    img_path = tmp_path / "large.jpg"
    PILImage.new("RGB", (200, 200), color=(64, 128, 192)).save(img_path, "JPEG")

    monkeypatch.setattr(PILModule, "MAX_IMAGE_PIXELS", 1)

    thumb_path = generate_thumbnail(str(img_path), "deadbeef", str(tmp_path))

    assert Path(thumb_path).exists()
    with PILImage.open(thumb_path) as t:
        assert t.width <= 512
        assert t.height <= 512
