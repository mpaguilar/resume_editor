"""Add company column to resumes table.

Revision ID: 20260225_add_company
Revises: 3e902acf0d1d
Create Date: 2026-02-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260225_add_company"
down_revision: Union[str, None] = "3e902acf0d1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add company column to resumes table."""
    op.add_column(
        "resumes",
        sa.Column("company", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    """Remove company column from resumes table."""
    op.drop_column("resumes", "company")
