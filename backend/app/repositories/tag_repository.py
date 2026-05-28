from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.tag import ImageTag, Tag


class TagRepository:
    """DB access for Tag records and ImageTag join rows."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, tag: Tag) -> Tag:
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        return tag

    def get_by_id(self, tag_id: UUID) -> Optional[Tag]:
        return self.session.get(Tag, tag_id)

    def get_by_name(self, name: str) -> Optional[Tag]:
        return self.session.exec(select(Tag).where(Tag.name == name)).first()

    def list(self) -> List[Tag]:
        return list(self.session.exec(select(Tag)).all())

    def update(self, tag: Tag) -> Tag:
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        return tag

    def delete(self, tag: Tag) -> None:
        self.session.delete(tag)
        self.session.commit()

    def get_image_tags(self, image_id: UUID) -> List[Tag]:
        """Return all tags assigned to an image."""
        rows = self.session.exec(
            select(ImageTag).where(ImageTag.image_id == image_id)
        ).all()
        return [self.session.get(Tag, r.tag_id) for r in rows]

    def add_image_tag(self, image_id: UUID, tag_id: UUID) -> None:
        """Add a tag to an image, silently ignoring if already assigned."""
        existing = self.session.get(ImageTag, (image_id, tag_id))
        if not existing:
            self.session.add(ImageTag(image_id=image_id, tag_id=tag_id))
            self.session.commit()

    def clear_image_tags(self, image_id: UUID) -> None:
        """Remove all tag assignments for an image."""
        rows = self.session.exec(
            select(ImageTag).where(ImageTag.image_id == image_id)
        ).all()
        for row in rows:
            self.session.delete(row)
        self.session.commit()

    def remove_image_tag(self, image_id: UUID, tag_id: UUID) -> None:
        row = self.session.get(ImageTag, (image_id, tag_id))
        if row:
            self.session.delete(row)
            self.session.commit()

    def bulk_tag_images(
        self,
        image_ids: List[UUID],
        add_tag_ids: List[UUID],
        remove_tag_ids: List[UUID],
    ) -> None:
        """Apply tag additions and removals to multiple images in a single transaction."""
        for image_id in image_ids:
            for tag_id in add_tag_ids:
                if not self.session.get(ImageTag, (image_id, tag_id)):
                    self.session.add(ImageTag(image_id=image_id, tag_id=tag_id))
            for tag_id in remove_tag_ids:
                row = self.session.get(ImageTag, (image_id, tag_id))
                if row:
                    self.session.delete(row)
        self.session.commit()
