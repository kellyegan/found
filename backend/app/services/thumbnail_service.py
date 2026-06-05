from pathlib import Path

from PIL import Image as PILImage

# This is a local desktop app that processes the user's own files.
# The decompression-bomb guard is designed for servers handling untrusted uploads
# and is not applicable here.
PILImage.MAX_IMAGE_PIXELS = None

THUMBNAIL_SIZE = (512, 512)


def get_thumbnail_path(sha256_hash: str, thumbnail_dir: str) -> Path:
    """Return the expected cache path for a hash: <thumbnail_dir>/<hash[:2]>/<hash>.jpg"""
    return Path(thumbnail_dir) / sha256_hash[:2] / f"{sha256_hash}.jpg"


def generate_thumbnail(source_path: str, sha256_hash: str, thumbnail_dir: str) -> str:
    """Resize the source image to fit within 512x512 and save as JPEG. Returns the thumbnail path."""
    thumb_path = get_thumbnail_path(sha256_hash, thumbnail_dir)
    thumb_path.parent.mkdir(parents=True, exist_ok=True)

    PILImage.MAX_IMAGE_PIXELS = None  # belt-and-suspenders: ensures tests work too
    with PILImage.open(source_path) as img:
        # Raw packed modes like I;16 (16-bit grayscale TIFF from scanners/DSLRs)
        # have two problems:
        #   1. thumbnail() raises ValueError on large downscales (>~6x ratio)
        #   2. convert('RGB') clips values > 255 → all-white thumbnail
        # Fix: convert to I (32-bit int, preserves 16-bit values), thumbnail
        # that (mode I is fully supported), then scale 0-65535 → 0-255 before
        # saving. The mode name always contains ";" for packed/raw modes.
        if ";" in (img.mode or ""):
            img = img.convert("I")
            img.thumbnail(THUMBNAIL_SIZE)
            img = img.point(lambda x: x / 256).convert("L")
        else:
            img.thumbnail(THUMBNAIL_SIZE)
        img.convert("RGB").save(thumb_path, "JPEG", quality=85)

    return str(thumb_path)


def get_or_generate_thumbnail(source_path: str, sha256_hash: str, thumbnail_dir: str) -> str:
    """Return the thumbnail path, generating the file first if it doesn't exist."""
    thumb_path = get_thumbnail_path(sha256_hash, thumbnail_dir)
    if not thumb_path.exists():
        generate_thumbnail(source_path, sha256_hash, thumbnail_dir)
    return str(thumb_path)
