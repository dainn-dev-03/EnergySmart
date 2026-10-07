"""audit trail and actor attribution

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ACTORED_TABLES = ("buildings", "floors", "rooms", "meters", "electricity_prices", "electricity_usages")


def upgrade() -> None:
    for table in _ACTORED_TABLES:
        op.add_column(table, sa.Column("created_by_id", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("updated_by_id", sa.Integer(), nullable=True))
        op.create_foreign_key(f"fk_{table}_created_by_id_users", table, "users", ["created_by_id"], ["id"], ondelete="SET NULL")
        op.create_foreign_key(f"fk_{table}_updated_by_id_users", table, "users", ["updated_by_id"], ["id"], ondelete="SET NULL")
    op.add_column("alerts", sa.Column("resolved_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_alerts_resolved_by_id_users", "alerts", "users", ["resolved_by_id"], ["id"], ondelete="SET NULL")
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("entity_label", sa.String(255), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_constraint("fk_alerts_resolved_by_id_users", "alerts", type_="foreignkey")
    op.drop_column("alerts", "resolved_by_id")
    for table in reversed(_ACTORED_TABLES):
        op.drop_constraint(f"fk_{table}_updated_by_id_users", table, type_="foreignkey")
        op.drop_constraint(f"fk_{table}_created_by_id_users", table, type_="foreignkey")
        op.drop_column(table, "updated_by_id")
        op.drop_column(table, "created_by_id")
