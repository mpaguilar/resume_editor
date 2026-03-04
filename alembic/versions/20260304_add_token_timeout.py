"""Add access_token_expire_minutes to user_settings.

Revision ID: 20260304_add_token_timeout
Revises: 20260226_merge_heads
Create Date: 2026-03-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260304_add_token_timeout"
down_revision: Union[str, Sequence[str], None] = "20260226_merge_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add access_token_expire_minutes column to user_settings table.

    This column stores the user's preferred session timeout in minutes.
    If NULL, the global default (600 minutes) is used.

    """
    op.add_column(
        "user_settings",
        sa.Column("access_token_expire_minutes", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Remove access_token_expire_minutes column from user_settings table."""
    op.drop_column("user_settings", "access_token_expire_minutes")
