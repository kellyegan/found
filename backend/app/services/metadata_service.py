import mimetypes
from dataclasses import dataclass
from pathlib import Path

from PIL import Image as PILImage, UnidentifiedImageError

# This is a local desktop app that processes the user's own files.
# The decompression-bomb guard is designed for servers handling untrusted uploads
# and is not applicable here.
PILImage.MAX_IMAGE_PIXELS = None

_SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
}

_PILLOW_FORMAT_TO_MIME = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "tiff": "image/tiff",
}


class UnsupportedFileTypeError(Exception):
    pass


@dataclass
class ImageMetadata:
    width: int
    height: int
    mime_type: str
    file_size: int


def extract_metadata(path: str) -> ImageMetadata:
    file_path = Path(path)

    try:
        PILImage.MAX_IMAGE_PIXELS = None  # belt-and-suspenders: ensures tests work too
        with PILImage.open(file_path) as img:
            pillow_mime = _PILLOW_FORMAT_TO_MIME.get((img.format or "").lower())
            width, height = img.size
    except UnidentifiedImageError:
        raise UnsupportedFileTypeError(f"Unsupported or unreadable file: {path}")

    # Pillow is authoritative; fall back to mimetypes guess if format unknown
    mime_type = pillow_mime or mimetypes.guess_type(str(file_path))[0]

    if mime_type not in _SUPPORTED_MIME_TYPES:
        raise UnsupportedFileTypeError(
            f"File type '{mime_type}' is not supported."
        )

    return ImageMetadata(
        width=width,
        height=height,
        mime_type=mime_type,
        file_size=file_path.stat().st_size,
    )
