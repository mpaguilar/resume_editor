"""Seed initial roles

Revision ID: e0c1a2b3d4f5
Revises: d204a83ef0df
Create Date: 2025-08-28 15:55:21.164392

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e0c1a2b3d4f5"
down_revision: Union[str, Sequence[str], None] = "d204a83ef0df"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define a simple table structure for the data migration.
roles_table = sa.table("roles", sa.column("name", sa.String))


def upgrade() -> None:
    """Seed initial roles."""
    op.bulk_insert(
        roles_table,
        [
            {"name": "admin"},
            {"name": "user"},
        ],
    )


def downgrade() -> None:
    """Remove initial roles."""
    op.execute(roles_table.delete().where(roles_table.c.name.in_(["admin", "user"])))
