"""create rewards

Revision ID: 2a27c6b389ff
Revises: 8fb1fcc039a1
Create Date: 2023-03-01 11:07:03.485155

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from polar.ext.sqlalchemy import GUID

# revision identifiers, used by Alembic.
revision = "2a27c6b389ff"
down_revision = "8fb1fcc039a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "rewards",
        sa.Column("issue_id", GUID(), nullable=False),
        sa.Column("repository_id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=25, scale=10), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("modified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.drop_table("test_model")
    op.drop_table("demo")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "demo",
        sa.Column(
            "testing", sa.VARCHAR(length=255), autoincrement=False, nullable=False
        ),
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name="demo_pkey"),
    )
    op.create_table(
        "test_model",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("guid", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("int_column", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("str_column", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("status", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="test_model_pkey"),
    )
    op.drop_table("rewards")
    # ### end Alembic commands ###