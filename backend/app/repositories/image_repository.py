from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.image import Image


class ImageRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, image: Image) -> Image:
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def get_by_id(self, image_id: UUID) -> Optional[Image]:
        return self.session.get(Image, image_id)

    def get_by_path(self, path: str) -> Optional[Image]:
        """Return the image with this exact filesystem path, or None."""
        return self.session.exec(select(Image).where(Image.path == path)).first()

    def get_by_hash(self, sha256_hash: str) -> Optional[Image]:
        """Return an image with this SHA-256 hash, or None. Used for duplicate detection."""
        return self.session.exec(select(Image).where(Image.sha256_hash == sha256_hash)).first()

    def list(self, offset: int = 0, limit: int = 100) -> List[Image]:
        return list(self.session.exec(select(Image).offset(offset).limit(limit)).all())

    def update(self, image: Image) -> Image:
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def delete(self, image: Image) -> None:
        self.session.delete(image)
        self.session.commit()
