"""split user full_name into first_name and last_name

Revision ID: fe61f4c8cdef
Revises: 27821d503949
Create Date: 2026-07-14 18:47:41.028788

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fe61f4c8cdef'
down_revision: Union[str, None] = '27821d503949'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('first_name', sa.String(length=120), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(length=120), nullable=True))
    op.execute(
        """
        UPDATE users SET
            first_name = COALESCE(NULLIF(split_part(full_name, ' ', 1), ''), 'Member'),
            last_name = NULLIF(trim(substring(full_name from length(split_part(full_name, ' ', 1)) + 1)), '')
        """
    )
    op.alter_column('users', 'first_name', nullable=False)
    op.alter_column('users', 'last_name', nullable=False, server_default='')
    op.drop_column('users', 'full_name')


def downgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.execute("UPDATE users SET full_name = trim(first_name || ' ' || last_name)")
    op.alter_column('users', 'full_name', nullable=False)
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
