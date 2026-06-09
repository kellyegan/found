"""Tests for image relocation: path-prefix query, service method, and API endpoints."""
from app.repositories.image_repository import ImageRepository


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
