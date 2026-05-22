from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.category import Category, ImageCategory
from app.models.collection import CollectionImage
from app.models.image import Image
from app.models.tag import ImageTag, Tag


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

    def list(
        self,
        offset: int = 0,
        limit: int = 100,
        tag: Optional[str] = None,
        category: Optional[str] = None,
        collection_id: Optional[UUID] = None,
    ) -> List[Image]:
        """Return images with optional filtering by tag name, category name, or collection ID. Results are ordered by imported_date."""
        query = select(Image)

        if tag:
            query = (
                query
                .join(ImageTag, ImageTag.image_id == Image.id)
                .join(Tag, Tag.id == ImageTag.tag_id)
                .where(Tag.name == tag.lower())
            )

        if category:
            query = (
                query
                .join(ImageCategory, ImageCategory.image_id == Image.id)
                .join(Category, Category.id == ImageCategory.category_id)
                .where(Category.name == category)
            )

        if collection_id:
            query = (
                query
                .join(CollectionImage, CollectionImage.image_id == Image.id)
                .where(CollectionImage.collection_id == collection_id)
            )

        query = query.distinct().order_by(Image.imported_date).offset(offset).limit(limit)
        return list(self.session.exec(query).all())

    def update(self, image: Image) -> Image:
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def delete(self, image: Image) -> None:
        self.session.delete(image)
        self.session.commit()
