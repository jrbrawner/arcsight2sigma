"""adding sigma table

Revision ID: 9cc1e8ff1a99
Revises: 3f5917d89dc6
Create Date: 2024-01-27 12:17:25.785342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9cc1e8ff1a99'
down_revision: Union[str, None] = '3f5917d89dc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'SigmaRule',
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('rule_id', sa.String()),
        sa.Column('status', sa.String()),
        sa.Column('description', sa.String()),
        sa.Column('author', sa.String()),
        sa.Column('logsource', sa.String()),
        sa.Column('detection', sa.String()),
        sa.Column('condition', sa.String()),
        sa.Column('id', sa.Integer()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('title'),
        sa.UniqueConstraint('rule_id')
    )


def downgrade() -> None:
    op.drop_table("SigmaRule")
