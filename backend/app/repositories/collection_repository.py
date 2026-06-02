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
        """Append images to a collection, assigning sort_order after existing entries.
        Auto-sets cover_image_id to the first image if the collection has no cover."""
        existing = self.session.exec(
            select(CollectionImage).where(CollectionImage.collection_id == collection_id)
        ).all()
        existing_ids = {r.image_id for r in existing}
        next_order = max((r.sort_order for r in existing), default=-1) + 1

        first_new: Optional[UUID] = None
        for image_id in image_ids:
            if image_id not in existing_ids:
                self.session.add(
                    CollectionImage(
                        collection_id=collection_id,
                        image_id=image_id,
                        sort_order=next_order,
                    )
                )
                if first_new is None:
                    first_new = image_id
                next_order += 1
        self.session.commit()

        if first_new is not None:
            collection = self.session.get(Collection, collection_id)
            if collection and collection.cover_image_id is None:
                collection.cover_image_id = first_new
                self.session.add(collection)
                self.session.commit()

    def remove_image(self, collection_id: UUID, image_id: UUID) -> None:
        """Remove an image from a collection. If it was the cover, promote the next image."""
        row = self.session.get(CollectionImage, (collection_id, image_id))
        if row:
            self.session.delete(row)
            self.session.commit()

        collection = self.session.get(Collection, collection_id)
        if collection and collection.cover_image_id == image_id:
            remaining = self.session.exec(
                select(CollectionImage)
                .where(CollectionImage.collection_id == collection_id)
                .order_by(CollectionImage.sort_order)
            ).all()
            collection.cover_image_id = remaining[0].image_id if remaining else None
            self.session.add(collection)
            self.session.commit()

    def get_image_collections(self, image_id: UUID) -> List[Collection]:
        """Return all collections that contain the given image."""
        rows = self.session.exec(
            select(CollectionImage).where(CollectionImage.image_id == image_id)
        ).all()
        return [c for r in rows if (c := self.session.get(Collection, r.collection_id)) is not None]

    def reorder(self, collection_id: UUID, image_ids: List[UUID]) -> None:
        """Set sort_order for each image according to its position in image_ids."""
        for order, image_id in enumerate(image_ids):
            row = self.session.get(CollectionImage, (collection_id, image_id))
            if row:
                row.sort_order = order
                self.session.add(row)
        self.session.commit()
