from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Collection(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True)
    description: Optional[str] = None
    created_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    cover_image_id: Optional[UUID] = None


class CollectionImage(SQLModel, table=True):
    collection_id: UUID = Field(foreign_key="collection.id", primary_key=True)
    image_id: UUID = Field(foreign_key="image.id", primary_key=True)
    sort_order: int = 0
