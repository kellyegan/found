"""add cover_image_id to collection

Revision ID: a1b2c3d4e5f6
Revises: fd6e447ad21a
Create Date: 2026-05-28 00:00:00.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fd6e447ad21a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('collection', sa.Column('cover_image_id', sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column('collection', 'cover_image_id')
