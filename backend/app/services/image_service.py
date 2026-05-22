from typing import List, Optional
from uuid import UUID

from app.models.image import Image
from app.repositories.image_repository import ImageRepository
from app.schemas.image import ImageCreate


class ImageService:
    def __init__(self, repo: ImageRepository):
        self.repo = repo

    def create_image(self, data: ImageCreate) -> Image:
        image = Image(**data.model_dump())
        return self.repo.create(image)

    def get_image(self, image_id: UUID) -> Optional[Image]:
        return self.repo.get_by_id(image_id)

    def list_images(self, offset: int = 0, limit: int = 100) -> List[Image]:
        return self.repo.list(offset=offset, limit=limit)

    def delete_image(self, image_id: UUID) -> bool:
        image = self.repo.get_by_id(image_id)
        if not image:
            return False
        self.repo.delete(image)
        return True
