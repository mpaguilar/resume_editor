"""Merge multiple heads into a single revision.

Revision ID: 20260226_merge_heads
Revises: 20260225_add_company, 27081f99702c
Create Date: 2026-02-26

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260226_merge_heads"
down_revision: Union[str, Sequence[str], None] = (
    "20260225_add_company",
    "27081f99702c",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge point - no actual schema changes needed.

    This migration serves as a merge point for two parallel branches:
    - Branch 1: 3e902acf0d1d → 20260225_add_company (adds company column)
    - Branch 2: 3e902acf0d1d → a1f4c822f86c → 27081f99702c (adds export settings)

    Both branches add independent columns, so no schema changes are required
    at the merge point.

    """
    # No schema changes needed - this is a merge point only
    pass


def downgrade() -> None:
    """Downgrade is a no-op for merge migration.

    Individual downgrades should be handled by downgrading the
    specific branch revisions.

    """
    # No schema changes to revert - this is a merge point only
    pass
