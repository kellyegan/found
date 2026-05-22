import hashlib


def sha256(path: str) -> str:
    """Return the SHA-256 hex digest of the file at path, reading in 8 KB chunks to keep memory use flat for large files."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
