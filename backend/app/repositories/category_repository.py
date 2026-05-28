from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.category import Category, ImageCategory


class CategoryRepository:
    """DB access for Category records and ImageCategory join rows."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, category: Category) -> Category:
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category

    def get_by_id(self, category_id: UUID) -> Optional[Category]:
        return self.session.get(Category, category_id)

    def list(self) -> List[Category]:
        return list(self.session.exec(select(Category)).all())

    def update(self, category: Category) -> Category:
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.session.delete(category)
        self.session.commit()

    def get_image_categories(self, image_id: UUID) -> List[Category]:
        """Return all categories assigned to an image."""
        rows = self.session.exec(
            select(ImageCategory).where(ImageCategory.image_id == image_id)
        ).all()
        return [self.session.get(Category, r.category_id) for r in rows]

    def add_image_category(self, image_id: UUID, category_id: UUID) -> None:
        """Assign a category to an image, silently ignoring if already assigned."""
        existing = self.session.get(ImageCategory, (image_id, category_id))
        if not existing:
            self.session.add(ImageCategory(image_id=image_id, category_id=category_id))
            self.session.commit()

    def clear_image_categories(self, image_id: UUID) -> None:
        rows = self.session.exec(
            select(ImageCategory).where(ImageCategory.image_id == image_id)
        ).all()
        for row in rows:
            self.session.delete(row)
        self.session.commit()

    def remove_image_category(self, image_id: UUID, category_id: UUID) -> None:
        row = self.session.get(ImageCategory, (image_id, category_id))
        if row:
            self.session.delete(row)
            self.session.commit()

    def bulk_categorise_images(
        self,
        image_ids: List[UUID],
        add_category_ids: List[UUID],
        remove_category_ids: List[UUID],
    ) -> None:
        """Apply category additions and removals to multiple images in a single transaction."""
        for image_id in image_ids:
            for category_id in add_category_ids:
                if not self.session.get(ImageCategory, (image_id, category_id)):
                    self.session.add(ImageCategory(image_id=image_id, category_id=category_id))
            for category_id in remove_category_ids:
                row = self.session.get(ImageCategory, (image_id, category_id))
                if row:
                    self.session.delete(row)
        self.session.commit()
