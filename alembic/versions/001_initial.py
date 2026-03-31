"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-22

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attack_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attack_type", sa.String(), nullable=False),
        sa.Column("original_prompt", sa.Text(), nullable=False),
        sa.Column("adversarial_prompt", sa.Text(), nullable=True),
        sa.Column("model_response", sa.Text(), nullable=True),
        sa.Column("result", sa.String(), nullable=False),
        sa.Column("success_score", sa.Float(), nullable=False),
        sa.Column("iterations", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "defense_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("defense_type", sa.String(), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("is_malicious", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("detected_patterns", sa.JSON(), nullable=True),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_type", sa.String(), nullable=False),
        sa.Column("target_model", sa.String(), nullable=False),
        sa.Column("attack_type", sa.String(), nullable=True),
        sa.Column("defense_type", sa.String(), nullable=True),
        sa.Column("success_rate", sa.Float(), nullable=False),
        sa.Column("avg_score", sa.Float(), nullable=True),
        sa.Column("total_tests", sa.Integer(), nullable=False),
        sa.Column("passed_tests", sa.Integer(), nullable=False),
        sa.Column("failed_tests", sa.Integer(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("report", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.drop_table("evaluation_results")
    op.drop_table("defense_records")
    op.drop_table("attack_records")
