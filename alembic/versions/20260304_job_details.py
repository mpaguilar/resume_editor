"""Add extracted job details columns to resumes table.

Revision ID: 20260304_job_details
Revises: 20260304_add_token_timeout
Create Date: 2026-03-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260304_job_details"
down_revision: Union[str, None] = "20260304_add_token_timeout"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add extracted job details columns to resumes table."""
    op.add_column(
        "resumes",
        sa.Column("extracted_company_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column("extracted_job_title", sa.String(255), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column("extracted_pay_rate", sa.String(100), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column("extracted_contact_info", sa.String(500), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column("extracted_work_arrangement", sa.String(50), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column("extracted_location", sa.String(255), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column("extracted_special_instructions", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove extracted job details columns from resumes table."""
    op.drop_column("resumes", "extracted_company_name")
    op.drop_column("resumes", "extracted_job_title")
    op.drop_column("resumes", "extracted_pay_rate")
    op.drop_column("resumes", "extracted_contact_info")
    op.drop_column("resumes", "extracted_work_arrangement")
    op.drop_column("resumes", "extracted_location")
    op.drop_column("resumes", "extracted_special_instructions")
