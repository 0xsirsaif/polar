"""issue.issue_has_in_progress_relationship

Revision ID: c228c42e2443
Revises: 4cc309887434
Create Date: 2023-05-12 11:18:38.939385

"""
from alembic import op
import sqlalchemy as sa


# Polar Custom Imports
from polar.kit.extensions.sqlalchemy import PostgresUUID

# revision identifiers, used by Alembic.
revision = "c228c42e2443"
down_revision = "4cc309887434"
branch_labels: tuple[str] | None = None
depends_on: tuple[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "issues",
        sa.Column(
            "issue_has_in_progress_relationship",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )
    op.add_column(
        "issues",
        sa.Column(
            "issue_has_pull_request_relationship",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )

    op.execute(
        """
update issues set
    issue_has_in_progress_relationship = 't'
where id in (
    select i.id from issues i join issue_references ON issue_references.issue_id = i.id join pull_requests ON pull_requests.id = issue_references.pull_request_id where pull_requests.is_draft = True
)
    """
    )

    op.execute(
        """
update issues set
    issue_has_in_progress_relationship = 't'
where id in (
    select i.id from issues i join issue_references ON issue_references.issue_id = i.id where issue_references.reference_type in ('external_github_pull_request', 'external_github_commit')
);
    """
    )

    op.execute(
        """
update issues set 
    issue_has_pull_request_relationship = 't'
where id in (
    select i.id from issues i join issue_references ON issue_references.issue_id = i.id join pull_requests ON pull_requests.id = issue_references.pull_request_id where pull_requests.is_draft = False
)
    """
    )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("issues", "issue_has_pull_request_relationship")
    op.drop_column("issues", "issue_has_in_progress_relationship")
    # ### end Alembic commands ###