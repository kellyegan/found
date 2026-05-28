from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlmodel import Session, select

from app.models.category import Category, ImageCategory
from app.models.collection import CollectionImage
from app.models.image import FileStatus, Image
from app.models.tag import ImageTag, Tag
from app.utils.pagination import decode_cursor, encode_cursor


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
        cursor: Optional[str] = None,
        limit: int = 100,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        exclude_categories: Optional[List[str]] = None,
        collection_id: Optional[UUID] = None,
        import_job_id: Optional[UUID] = None,
        missing: Optional[bool] = None,
    ) -> Tuple[List[Image], Optional[str], bool]:
        """Return a page of images with cursor-based pagination.

        Returns (images, next_cursor, has_more).
        Sort order is (imported_date, id) for stability.
        Include filters use AND logic; exclude filters remove any match.
        Tags are matched case-insensitively; categories are case-sensitive.
        """
        query = select(Image)

        for tag_name in (tags or []):
            subq = (
                select(ImageTag.image_id)
                .join(Tag, Tag.id == ImageTag.tag_id)
                .where(Tag.name == tag_name.lower())
            )
            query = query.where(Image.id.in_(subq))

        for tag_name in (exclude_tags or []):
            subq = (
                select(ImageTag.image_id)
                .join(Tag, Tag.id == ImageTag.tag_id)
                .where(Tag.name == tag_name.lower())
            )
            query = query.where(~Image.id.in_(subq))

        for cat_name in (categories or []):
            subq = (
                select(ImageCategory.image_id)
                .join(Category, Category.id == ImageCategory.category_id)
                .where(Category.name == cat_name)
            )
            query = query.where(Image.id.in_(subq))

        for cat_name in (exclude_categories or []):
            subq = (
                select(ImageCategory.image_id)
                .join(Category, Category.id == ImageCategory.category_id)
                .where(Category.name == cat_name)
            )
            query = query.where(~Image.id.in_(subq))

        if collection_id:
            query = (
                query
                .join(CollectionImage, CollectionImage.image_id == Image.id)
                .where(CollectionImage.collection_id == collection_id)
            )

        if import_job_id:
            query = query.where(Image.import_job_id == import_job_id)

        if missing is True:
            query = query.where(Image.file_status == FileStatus.missing)
        elif missing is False:
            query = query.where(Image.file_status != FileStatus.missing)

        if cursor:
            decoded = decode_cursor(cursor)
            if decoded:
                cursor_date, cursor_id = decoded
                query = query.where(
                    (Image.imported_date > cursor_date)
                    | ((Image.imported_date == cursor_date) & (Image.id > cursor_id))
                )

        query = query.distinct().order_by(Image.imported_date, Image.id).limit(limit + 1)
        rows = list(self.session.exec(query).all())

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = encode_cursor(rows[-1].imported_date, rows[-1].id) if has_more else None
        return rows, next_cursor, has_more

    def update(self, image: Image) -> Image:
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def delete(self, image: Image) -> None:
        self.session.delete(image)
        self.session.commit()

    def bulk_delete(self, image_ids: List[UUID]) -> None:
        """Remove multiple image records in a single transaction. Ignores IDs not found."""
        for image_id in image_ids:
            image = self.session.get(Image, image_id)
            if image:
                self.session.delete(image)
        self.session.commit()
