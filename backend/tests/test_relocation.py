"""Tests for image relocation: path-prefix query, service method, and API endpoints."""
import hashlib
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


def test_get_by_path_prefix_treats_underscore_as_literal_not_wildcard(session, make_image):
    make_image("/Volumes/My_Drive/photos/a.jpg")
    make_image("/Volumes/MyXDrive/photos/b.jpg")  # 'X' sits where '_' wildcard would match

    result = ImageRepository(session).get_by_path_prefix("/Volumes/My_Drive/")

    assert len(result) == 1
    assert result[0].path == "/Volumes/My_Drive/photos/a.jpg"


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


def test_relocate_by_prefix_preserves_subdirectory_structure(session, make_image, tmp_path):
    new_dir = tmp_path / "new"
    subdir = new_dir / "subdir"
    subdir.mkdir(parents=True)
    PILImage.new("RGB", (10, 10)).save(subdir / "a.jpg", "JPEG")

    make_image("/old/subdir/a.jpg")

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/old/", str(new_dir) + "/")

    assert len(result.updated) == 1
    assert result.updated[0].path == str(subdir / "a.jpg")


def test_relocate_by_prefix_no_match_returns_empty(session, make_image):
    make_image("/other/a.jpg")

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/nomatch/", "/new/")

    assert result.updated == []
    assert result.not_found == []


def test_relocate_by_prefix_skips_when_new_path_already_in_library(session, make_image, tmp_path):
    existing_file = tmp_path / "a.jpg"
    PILImage.new("RGB", (10, 10)).save(existing_file, "JPEG")

    make_image("/old/a.jpg", file_status=FileStatus.missing)
    make_image(str(existing_file))  # already imported at the target path

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/old/", str(tmp_path) + "/")

    assert result.updated == []
    assert str(existing_file) in result.conflicts


def test_relocate_by_prefix_updates_when_hash_matches(session, make_image, tmp_path):
    new_file = tmp_path / "a.jpg"
    PILImage.new("RGB", (10, 10)).save(new_file, "JPEG")
    file_hash = hashlib.sha256(new_file.read_bytes()).hexdigest()

    make_image("/old/a.jpg", sha256_hash=file_hash)

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/old/", str(tmp_path) + "/")

    assert len(result.updated) == 1
    assert result.mismatched == []


def test_relocate_by_prefix_mismatches_when_hash_differs(session, make_image, tmp_path):
    new_file = tmp_path / "a.jpg"
    PILImage.new("RGB", (10, 10)).save(new_file, "JPEG")

    make_image("/old/a.jpg", sha256_hash="deadbeef" * 8)  # wrong hash

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/old/", str(tmp_path) + "/")

    assert result.updated == []
    assert str(new_file) in result.mismatched


def test_relocate_by_prefix_falls_back_to_path_when_no_hash(session, make_image, tmp_path):
    new_file = tmp_path / "a.jpg"
    PILImage.new("RGB", (10, 10)).save(new_file, "JPEG")

    make_image("/old/a.jpg")  # sha256_hash defaults to None

    result = ImageService(ImageRepository(session)).relocate_by_prefix("/old/", str(tmp_path) + "/")

    assert len(result.updated) == 1
    assert result.mismatched == []


def test_relocate_by_prefix_sets_file_status_available(session, make_image, tmp_path):
    PILImage.new("RGB", (10, 10)).save(tmp_path / "a.jpg", "JPEG")
    img = make_image("/old/a.jpg", file_status=FileStatus.missing)

    ImageService(ImageRepository(session)).relocate_by_prefix("/old/", str(tmp_path) + "/")

    updated = ImageRepository(session).get_by_id(img.id)
    assert updated.file_status == FileStatus.available


# ---------------------------------------------------------------------------
# Commit 3 — API: POST /images/preview-relocation + POST /images/relocate-prefix
# ---------------------------------------------------------------------------

def test_preview_relocation_returns_derived_prefixes_and_count(client, make_image):
    make_image("/Volumes/OldDrive/photos/a.jpg")
    make_image("/Volumes/OldDrive/photos/b.jpg")
    make_image("/Volumes/Other/c.jpg")

    response = client.post("/api/v1/images/preview-relocation", json={
        "old_path": "/Volumes/OldDrive/photos/a.jpg",
        "new_path": "/Volumes/NewDrive/photos/a.jpg",
    })

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["old_prefix"] == "/Volumes/OldDrive/"
    assert data["new_prefix"] == "/Volumes/NewDrive/"
    assert data["affected_count"] == 2


def test_preview_relocation_count_is_zero_when_no_images_match(client):
    response = client.post("/api/v1/images/preview-relocation", json={
        "old_path": "/Volumes/OldDrive/photos/a.jpg",
        "new_path": "/Volumes/NewDrive/photos/a.jpg",
    })

    assert response.status_code == 200
    assert response.json()["data"]["affected_count"] == 0


def test_relocate_prefix_updates_images_and_reports_counts(client, make_image, tmp_path):
    new_dir = tmp_path / "new"
    new_dir.mkdir()
    for name in ["a.jpg", "b.jpg"]:
        PILImage.new("RGB", (10, 10)).save(new_dir / name, "JPEG")

    make_image("/old/a.jpg")
    make_image("/old/b.jpg")

    response = client.post("/api/v1/images/relocate-prefix", json={
        "old_prefix": "/old/",
        "new_prefix": str(new_dir) + "/",
    })

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["updated"] == 2
    assert data["not_found"] == 0


def test_relocate_prefix_reports_not_found_count(client, make_image):
    make_image("/old/a.jpg")

    response = client.post("/api/v1/images/relocate-prefix", json={
        "old_prefix": "/old/",
        "new_prefix": "/nonexistent/",
    })

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["updated"] == 0
    assert data["not_found"] == 1


def test_relocate_prefix_reports_mismatched_count(client, make_image, tmp_path):
    new_file = tmp_path / "a.jpg"
    PILImage.new("RGB", (10, 10)).save(new_file, "JPEG")

    make_image("/old/a.jpg", sha256_hash="deadbeef" * 8)

    response = client.post("/api/v1/images/relocate-prefix", json={
        "old_prefix": "/old/",
        "new_prefix": str(tmp_path) + "/",
    })

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["updated"] == 0
    assert data["not_found"] == 0
    assert data["mismatched"] == 1


def test_relocate_prefix_reports_conflict_when_new_path_already_in_library(client, make_image, tmp_path):
    existing_file = tmp_path / "a.jpg"
    PILImage.new("RGB", (10, 10)).save(existing_file, "JPEG")

    make_image("/old/a.jpg", file_status=FileStatus.missing)
    make_image(str(existing_file))  # already imported at the target path

    response = client.post("/api/v1/images/relocate-prefix", json={
        "old_prefix": "/old/",
        "new_prefix": str(tmp_path) + "/",
    })

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["updated"] == 0
    assert data["not_found"] == 0
    assert data["conflicts"] == 1


def test_relocate_prefix_no_match_is_no_op(client, make_image):
    img = make_image("/other/a.jpg")

    response = client.post("/api/v1/images/relocate-prefix", json={
        "old_prefix": "/nomatch/",
        "new_prefix": "/new/",
    })

    assert response.status_code == 200
    assert response.json()["data"]["updated"] == 0

    unchanged = client.get(f"/api/v1/images/{img.id}").json()["data"]
    assert unchanged["path"] == "/other/a.jpg"
