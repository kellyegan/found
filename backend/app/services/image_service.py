from pathlib import Path
from typing import List, Optional
from uuid import UUID

from app.core.config import settings
from app.models.image import FileStatus, Image
from app.repositories.image_repository import ImageRepository
from app.services.thumbnail_service import get_or_generate_thumbnail


class ImageService:
    def __init__(self, repo: ImageRepository):
        self.repo = repo

    def get_image(self, image_id: UUID) -> Optional[Image]:
        return self.repo.get_by_id(image_id)

    def list_images(
        self,
        offset: int = 0,
        limit: int = 100,
        tag: Optional[str] = None,
        category: Optional[str] = None,
        collection_id: Optional[UUID] = None,
        import_job_id: Optional[UUID] = None,
    ) -> List[Image]:
        return self.repo.list(
            offset=offset, limit=limit,
            tag=tag, category=category, collection_id=collection_id,
            import_job_id=import_job_id,
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

    def verify_file(self, image_id: UUID) -> Optional[Image]:
        image = self.repo.get_by_id(image_id)
        if not image:
            return None
        image.file_status = (
            FileStatus.available if Path(image.path).exists() else FileStatus.missing
        )
        return self.repo.update(image)
