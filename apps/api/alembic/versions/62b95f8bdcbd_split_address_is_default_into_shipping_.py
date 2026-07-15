"""split address is_default into shipping and billing defaults

Revision ID: 62b95f8bdcbd
Revises: fe61f4c8cdef
Create Date: 2026-07-14 19:23:02.572064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '62b95f8bdcbd'
down_revision: Union[str, None] = 'fe61f4c8cdef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'addresses',
        sa.Column('is_default_shipping', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'addresses',
        sa.Column('is_default_billing', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        "UPDATE addresses SET is_default_shipping = is_default, is_default_billing = is_default"
    )
    op.drop_column('addresses', 'is_default')


def downgrade() -> None:
    op.add_column(
        'addresses',
        sa.Column('is_default', sa.BOOLEAN(), autoincrement=False, nullable=False, server_default=sa.false()),
    )
    op.execute("UPDATE addresses SET is_default = is_default_shipping")
    op.drop_column('addresses', 'is_default_billing')
    op.drop_column('addresses', 'is_default_shipping')
