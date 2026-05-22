from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True)
    description: Optional[str] = None


class ImageCategory(SQLModel, table=True):
    image_id: UUID = Field(foreign_key="image.id", primary_key=True)
    category_id: UUID = Field(foreign_key="category.id", primary_key=True)
