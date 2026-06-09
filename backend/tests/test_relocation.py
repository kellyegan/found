"""Tests for image relocation: path-prefix query, service method, and API endpoints."""
import pytest
from PIL import Image as PILImage

from app.models.image import FileStatus
from app.repositories.image_repository import ImageRepository
from app.services.image_service import ImageService, derive_relocation_prefixes


# ---------------------------------------------------------------------------
# Commit 1 — Repository: get_by_path_prefix
# ---------------------------------------------------------------------------

def test_get_by_path_prefix_returns_matching_images(session, make_image):
    make_image("/Volumes/Drive/photos/a.jpg")
    make_image("/Volumes/Drive/photos/b.jpg")
    make_image("/Volumes/Other/photos/c.jpg")

    result = ImageRepository(session).get_by_path_prefix("/Volumes/Drive/")

    assert {img.path for img in result} == {
        "/Volumes/Drive/photos/a.jpg",
        "/Volumes/Drive/photos/b.jpg",
    }


def test_get_by_path_prefix_empty_when_no_match(session, make_image):
    make_image("/Volumes/Drive/photos/a.jpg")

    result = ImageRepository(session).get_by_path_prefix("/Volumes/Other/")

    assert result == []


def test_get_by_path_prefix_does_not_match_partial_directory_name(session, make_image):
    make_image("/Volumes/Drive/photos/a.jpg")
    make_image("/Volumes/DriveExtra/photos/b.jpg")

    result = ImageRepository(session).get_by_path_prefix("/Volumes/Drive/")

    assert len(result) == 1
    assert result[0].path == "/Volumes/Drive/photos/a.jpg"


# ---------------------------------------------------------------------------
# Commit 2 — Service: derive_relocation_prefixes + relocate_by_prefix
# ---------------------------------------------------------------------------

def test_derive_prefixes_drive_rename():
    old, new = derive_relocation_prefixes(
        "/Volumes/OldDrive/photos/2024/img001.jpg",
        "/Volumes/NewDrive/photos/2024/img001.jpg",
    )
    assert old == "/Volumes/OldDrive/"
    assert new == "/Volumes/NewDrive/"


def test_derive_prefixes_directory_rename():
    old, new = derive_relocation_prefixes(
        "/Users/kelly/Projects/project_a/img001.jpg",
        "/Users/kelly/Projects/project_b/img001.jpg",
    )
    assert old == "/Users/kelly/Projects/project_a/"
    assert new == "/Users/kelly/Projects/project_b/"


def test_derive_prefixes_different_mount_point():
    # 'photos/img001.jpg' is the common suffix, so the prefix boundary falls at the drive root.
    # This preserves relative structure: other images under /Volumes/OldDrive/ will be
    # relocated to the equivalent path under /Users/kelly/Desktop/.
    old, new = derive_relocation_prefixes(
        "/Volumes/OldDrive/photos/img001.jpg",
        "/Users/kelly/Desktop/photos/img001.jpg",
    )
    assert old == "/Volumes/OldDrive/"
    assert new == "/Users/kelly/Desktop/"


def test_derive_prefixes_filename_changed():
    old, new = derive_relocation_prefixes(
        "/Volumes/Drive/photos/img001.jpg",
        "/Volumes/NewDrive/photos/renamed.jpg",
    )
    assert old == "/Volumes/Drive/photos/"
    assert new == "/Volumes/NewDrive/photos/"


def test_relocate_by_prefix_updates_images_whose_new_path_exists(session, make_image, tmp_path):
    new_dir = tmp_path / "new"
    new_dir.mkdir()
    PILImage.new("RGB", (10, 10)).save(new_dir / "a.jpg", "JPEG")

    make_image("/old/a.jpg")

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/old/", str(new_dir) + "/")

    assert len(result.updated) == 1
    assert result.updated[0].path == str(new_dir / "a.jpg")
    assert result.not_found == []


def test_relocate_by_prefix_skips_images_whose_new_path_is_absent(session, make_image):
    make_image("/old/a.jpg")

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/old/", "/nonexistent/")

    assert result.updated == []
    assert "/nonexistent/a.jpg" in result.not_found


def test_relocate_by_prefix_partial_results(session, make_image, tmp_path):
    PILImage.new("RGB", (10, 10)).save(tmp_path / "exists.jpg", "JPEG")
    make_image("/old/exists.jpg")
    make_image("/old/gone.jpg")

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/old/", str(tmp_path) + "/")

    assert len(result.updated) == 1
    assert len(result.not_found) == 1


def test_relocate_by_prefix_no_match_returns_empty(session, make_image):
    make_image("/other/a.jpg")

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/nomatch/", "/new/")

    assert result.updated == []
    assert result.not_found == []


def test_relocate_by_prefix_sets_file_status_available(session, make_image, tmp_path):
    PILImage.new("RGB", (10, 10)).save(tmp_path / "a.jpg", "JPEG")
    img = make_image("/old/a.jpg", file_status=FileStatus.missing)

    ImageService(ImageRepository(session)).relocate_by_prefix("/old/", str(tmp_path) + "/")

    updated = ImageRepository(session).get_by_id(img.id)
    assert updated.file_status == FileStatus.available
