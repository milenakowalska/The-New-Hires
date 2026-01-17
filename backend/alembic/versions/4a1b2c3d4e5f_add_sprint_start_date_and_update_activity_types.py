"""Add sprint_start_date and update activity types

Revision ID: 4a1b2c3d4e5f
Revises: 377100619abe
Create Date: 2026-01-17 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '377100619abe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sprint_start_date to users
    op.add_column('users', sa.Column('sprint_start_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    
    # Update ActivityType enum
    # We use commit_as_batch or op.execute for Postgres enum additions
    # Note: ADD VALUE cannot be executed in a transaction block in some PG versions, 
    # but Alembic usually handles this or we can use op.execute.
    op.execute("ALTER TYPE activitytype ADD VALUE 'RETROSPECTIVE_COMPLETED'")
    op.execute("ALTER TYPE activitytype ADD VALUE 'TICKET_STATUS_CHANGED'")
    op.execute("ALTER TYPE activitytype ADD VALUE 'PULL_REQUEST_OPENED'")


def downgrade() -> None:
    # Downgrade is trickier for enums in Postgres (can't easily remove)
    op.drop_column('users', 'sprint_start_date')
    # For activitytype we just leave the extra values as they don't hurt much in downgrade
    # or we'd have to recreate the whole type which is risky.
