from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

from app.core.config import settings
from app.models.image import FileStatus, Image
from app.repositories.image_repository import ImageRepository
from app.services.metadata_service import UnsupportedFileTypeError, extract_metadata
from app.services.thumbnail_service import get_or_generate_thumbnail


class ImageService:
    def __init__(self, repo: ImageRepository):
        self.repo = repo

    def get_image(self, image_id: UUID) -> Optional[Image]:
        return self.repo.get_by_id(image_id)

    def list_images(
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
        return self.repo.list(
            cursor=cursor, limit=limit,
            tags=tags, categories=categories,
            exclude_tags=exclude_tags, exclude_categories=exclude_categories,
            collection_id=collection_id, import_job_id=import_job_id,
            missing=missing,
        )

    def patch_path(self, image_id: UUID, new_path: str) -> Optional[Image]:
        """Update the file path (and derived filename) of an existing image record."""
        image = self.repo.get_by_id(image_id)
        if not image:
            return None
        image.path = new_path
        image.filename = Path(new_path).name
        image.file_status = FileStatus.available
        return self.repo.update(image)

    def delete_image(self, image_id: UUID) -> bool:
        image = self.repo.get_by_id(image_id)
        if not image:
            return False
        self.repo.delete(image)
        return True

    def get_or_create_thumbnail(self, image: Image) -> str:
        """Return the thumbnail path, generating and persisting it if the file is missing."""
        thumb_path = get_or_generate_thumbnail(
            image.path, image.sha256_hash, settings.thumbnail_dir
        )
        if image.thumbnail_path != thumb_path:
            image.thumbnail_path = thumb_path
            self.repo.update(image)
        return thumb_path

    def batch_verify(self, image_ids: List[UUID]) -> None:
        """Verify file existence and refresh metadata for multiple images."""
        for image_id in image_ids:
            image = self.repo.get_by_id(image_id)
            if not image:
                continue
            path = Path(image.path)
            if not path.exists():
                image.file_status = FileStatus.missing
            else:
                try:
                    meta = extract_metadata(image.path)
                    image.width = meta.width
                    image.height = meta.height
                    image.mime_type = meta.mime_type
                    image.file_size = meta.file_size
                    image.file_status = FileStatus.available
                except (UnsupportedFileTypeError, OSError):
                    image.file_status = FileStatus.inaccessible
            self.repo.update(image)

    def verify_file(self, image_id: UUID) -> Optional[Image]:
        image = self.repo.get_by_id(image_id)
        if not image:
            return None
        image.file_status = (
            FileStatus.available if Path(image.path).exists() else FileStatus.missing
        )
        return self.repo.update(image)
