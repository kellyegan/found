from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlmodel import Session, select

from app.models.category import Category, ImageCategory
from app.models.collection import Collection, CollectionImage
from app.models.image import FileStatus, Image
from app.models.import_result import ImportResult
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

    def get_by_path_prefix(self, prefix: str) -> List[Image]:
        """Return all images whose path starts with prefix."""
        return list(self.session.exec(
            select(Image).where(Image.path.like(f"{prefix}%"))
        ).all())

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

        for cat_id in (categories or []):
            subq = (
                select(ImageCategory.image_id)
                .where(ImageCategory.category_id == UUID(cat_id))
            )
            query = query.where(Image.id.in_(subq))

        for cat_id in (exclude_categories or []):
            subq = (
                select(ImageCategory.image_id)
                .where(ImageCategory.category_id == UUID(cat_id))
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
        self._purge_references([image.id])
        self.session.delete(image)
        self.session.commit()

    def bulk_delete(self, image_ids: List[UUID]) -> None:
        """Remove multiple image records in a single transaction. Ignores IDs not found."""
        self._purge_references(image_ids)
        for image_id in image_ids:
            image = self.session.get(Image, image_id)
            if image:
                self.session.delete(image)
        self.session.commit()

    def _purge_references(self, image_ids: List[UUID]) -> None:
        """Remove rows in other tables that reference the given images.

        SQLite enforces no FK cascade for these association tables, so this
        cleanup must happen explicitly before the Image rows are deleted.
        """
        ids = set(image_ids)
        if not ids:
            return

        for row in self.session.exec(select(ImageTag).where(ImageTag.image_id.in_(ids))).all():
            self.session.delete(row)
        for row in self.session.exec(select(ImageCategory).where(ImageCategory.image_id.in_(ids))).all():
            self.session.delete(row)

        collection_links = self.session.exec(
            select(CollectionImage).where(CollectionImage.image_id.in_(ids))
        ).all()
        affected_collection_ids = {link.collection_id for link in collection_links}
        for link in collection_links:
            self.session.delete(link)

        for collection_id in affected_collection_ids:
            collection = self.session.get(Collection, collection_id)
            if collection and collection.cover_image_id in ids:
                remaining = self.session.exec(
                    select(CollectionImage)
                    .where(CollectionImage.collection_id == collection_id)
                    .order_by(CollectionImage.sort_order)
                ).all()
                collection.cover_image_id = remaining[0].image_id if remaining else None
                self.session.add(collection)

        for result in self.session.exec(
            select(ImportResult).where(ImportResult.existing_image_id.in_(ids))
        ).all():
            result.existing_image_id = None
            self.session.add(result)
