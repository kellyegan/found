from pathlib import Path

from PIL import Image as PILImage

THUMBNAIL_SIZE = (512, 512)


def get_thumbnail_path(sha256_hash: str, thumbnail_dir: str) -> Path:
    """Return the expected cache path for a hash: <thumbnail_dir>/<hash[:2]>/<hash>.jpg"""
    return Path(thumbnail_dir) / sha256_hash[:2] / f"{sha256_hash}.jpg"


def generate_thumbnail(source_path: str, sha256_hash: str, thumbnail_dir: str) -> str:
    """Resize the source image to fit within 512x512 and save as JPEG. Returns the thumbnail path."""
    thumb_path = get_thumbnail_path(sha256_hash, thumbnail_dir)
    thumb_path.parent.mkdir(parents=True, exist_ok=True)

    with PILImage.open(source_path) as img:
        img.thumbnail(THUMBNAIL_SIZE)
        img.convert("RGB").save(thumb_path, "JPEG", quality=85)

    return str(thumb_path)


def get_or_generate_thumbnail(source_path: str, sha256_hash: str, thumbnail_dir: str) -> str:
    """Return the thumbnail path, generating the file first if it doesn't exist."""
    thumb_path = get_thumbnail_path(sha256_hash, thumbnail_dir)
    if not thumb_path.exists():
        generate_thumbnail(source_path, sha256_hash, thumbnail_dir)
    return str(thumb_path)
