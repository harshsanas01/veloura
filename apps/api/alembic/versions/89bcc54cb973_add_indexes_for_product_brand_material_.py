"""add indexes for product brand material and tag filters

Revision ID: 89bcc54cb973
Revises: 28995c8e7dc4
Create Date: 2026-07-15 03:59:46.765495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '89bcc54cb973'
down_revision: Union[str, None] = '28995c8e7dc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_products_brand", "products", ["brand"])
    op.create_index("ix_products_material", "products", ["material"])
    op.create_index(
        "ix_products_occasion_tags_gin", "products", ["occasion_tags"], postgresql_using="gin"
    )
    op.create_index(
        "ix_products_season_tags_gin", "products", ["season_tags"], postgresql_using="gin"
    )
    op.create_index(
        "ix_products_style_tags_gin", "products", ["style_tags"], postgresql_using="gin"
    )


def downgrade() -> None:
    op.drop_index("ix_products_style_tags_gin", table_name="products")
    op.drop_index("ix_products_season_tags_gin", table_name="products")
    op.drop_index("ix_products_occasion_tags_gin", table_name="products")
    op.drop_index("ix_products_material", table_name="products")
    op.drop_index("ix_products_brand", table_name="products")
