from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.collection import Collection, CollectionImage
from app.models.image import Image


class CollectionRepository:
    """DB access for Collection records and CollectionImage join rows."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, collection: Collection) -> Collection:
        self.session.add(collection)
        self.session.commit()
        self.session.refresh(collection)
        return collection

    def get_by_id(self, collection_id: UUID) -> Optional[Collection]:
        return self.session.get(Collection, collection_id)

    def list(self) -> List[Collection]:
        return list(self.session.exec(select(Collection)).all())

    def update(self, collection: Collection) -> Collection:
        self.session.add(collection)
        self.session.commit()
        self.session.refresh(collection)
        return collection

    def delete(self, collection: Collection) -> None:
        self.session.delete(collection)
        self.session.commit()

    def get_images(self, collection_id: UUID) -> List[Image]:
        """Return images in a collection ordered by sort_order."""
        rows = self.session.exec(
            select(CollectionImage)
            .where(CollectionImage.collection_id == collection_id)
            .order_by(CollectionImage.sort_order)
        ).all()
        return [self.session.get(Image, r.image_id) for r in rows]

    def add_images(self, collection_id: UUID, image_ids: List[UUID]) -> None:
        """Append images to a collection, assigning sort_order after existing entries."""
        existing = self.session.exec(
            select(CollectionImage).where(CollectionImage.collection_id == collection_id)
        ).all()
        existing_ids = {r.image_id for r in existing}
        next_order = max((r.sort_order for r in existing), default=-1) + 1

        for image_id in image_ids:
            if image_id not in existing_ids:
                self.session.add(
                    CollectionImage(
                        collection_id=collection_id,
                        image_id=image_id,
                        sort_order=next_order,
                    )
                )
                next_order += 1
        self.session.commit()

    def remove_image(self, collection_id: UUID, image_id: UUID) -> None:
        row = self.session.get(CollectionImage, (collection_id, image_id))
        if row:
            self.session.delete(row)
            self.session.commit()

    def reorder(self, collection_id: UUID, image_ids: List[UUID]) -> None:
        """Set sort_order for each image according to its position in image_ids."""
        for order, image_id in enumerate(image_ids):
            row = self.session.get(CollectionImage, (collection_id, image_id))
            if row:
                row.sort_order = order
                self.session.add(row)
        self.session.commit()
