"""drop organization.default_funding_goal

Revision ID: bba60300e351
Revises: 1ba48f659a29
Create Date: 2023-08-08 10:41:01.062766

"""
from alembic import op
import sqlalchemy as sa


# Polar Custom Imports
from polar.kit.extensions.sqlalchemy import PostgresUUID

# revision identifiers, used by Alembic.
revision = 'bba60300e351'
down_revision = '1ba48f659a29'
branch_labels: tuple[str] | None = None
depends_on: tuple[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('organizations', 'default_funding_goal')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('organizations', sa.Column('default_funding_goal', sa.BIGINT(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###