"""adding arcsight rule table

Revision ID: 8355a2fee819
Revises: 9cc1e8ff1a99
Create Date: 2024-02-20 18:21:40.194655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8355a2fee819'
down_revision: Union[str, None] = '9cc1e8ff1a99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ArcSightRuleXML',
        sa.Column('name', sa.String()),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('raw', sa.String()),
        sa.Column('logic', sa.String()),
        sa.Column('id', sa.Integer()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )


def downgrade() -> None:
    op.drop_table("ArcSightRuleXML")
