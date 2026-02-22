"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-02-22 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

script_visibility = sa.Enum("private", "team", "public", name="script_visibility")
run_status = sa.Enum("pending", "running", "succeeded", "failed", name="run_status")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "scripts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("visibility", script_visibility, nullable=False, server_default="private"),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scripts_owner_id_updated_at", "scripts", ["owner_id", "updated_at"])
    op.create_index("ix_scripts_visibility", "scripts", ["visibility"])

    op.create_table(
        "script_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("triggered_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", run_status, nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["triggered_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_script_runs_script_id_started_at",
        "script_runs",
        ["script_id", "started_at"],
    )
    op.create_index("ix_script_runs_status", "script_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_script_runs_status", table_name="script_runs")
    op.drop_index("ix_script_runs_script_id_started_at", table_name="script_runs")
    op.drop_table("script_runs")

    op.drop_index("ix_scripts_visibility", table_name="scripts")
    op.drop_index("ix_scripts_owner_id_updated_at", table_name="scripts")
    op.drop_table("scripts")

    op.drop_table("users")

    bind = op.get_bind()
    run_status.drop(bind, checkfirst=False)
    script_visibility.drop(bind, checkfirst=False)
