"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-07 12:27:34.627889

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_buildings")),
        sa.UniqueConstraint("code", name=op.f("uq_buildings_code")),
    )
    op.create_table(
        "electricity_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price_per_kwh", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name=op.f("ck_electricity_prices_effective_range"),
        ),
        sa.CheckConstraint("price_per_kwh > 0", name=op.f("ck_electricity_prices_price_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_electricity_prices")),
    )
    op.create_index(
        op.f("ix_electricity_prices_effective_from"),
        "electricity_prices",
        ["effective_from"],
        unique=False,
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.Enum(
                "ADMIN",
                "MANAGER",
                "VIEWER",
                name="user_role",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            server_default="VIEWER",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )
    op.create_table(
        "floors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("floor_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["building_id"],
            ["buildings.id"],
            name=op.f("fk_floors_building_id_buildings"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_floors")),
        sa.UniqueConstraint(
            "building_id", "floor_number", name=op.f("uq_floors_building_id_floor_number")
        ),
    )
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("floor_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("area", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("area > 0", name=op.f("ck_rooms_area_positive")),
        sa.ForeignKeyConstraint(
            ["floor_id"], ["floors.id"], name=op.f("fk_rooms_floor_id_floors"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rooms")),
        sa.UniqueConstraint("code", name=op.f("uq_rooms_code")),
    )
    op.create_index(op.f("ix_rooms_floor_id"), "rooms", ["floor_id"], unique=False)
    op.create_table(
        "meters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("meter_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "meter_type",
            sa.Enum(
                "SINGLE_PHASE",
                "THREE_PHASE",
                name="meter_type",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "INACTIVE",
                "MAINTENANCE",
                name="meter_status",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column("installation_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["room_id"], ["rooms.id"], name=op.f("fk_meters_room_id_rooms"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meters")),
        sa.UniqueConstraint("meter_code", name=op.f("uq_meters_meter_code")),
    )
    op.create_index(op.f("ix_meters_room_id"), "meters", ["room_id"], unique=False)
    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("meter_id", sa.Integer(), nullable=False),
        sa.Column(
            "alert_type",
            sa.Enum(
                "HIGH_CONSUMPTION",
                name="alert_type",
                native_enum=False,
                create_constraint=True,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "INFO",
                "WARNING",
                "CRITICAL",
                name="alert_severity",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("threshold_value", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("actual_value", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["meter_id"], ["meters.id"], name=op.f("fk_alerts_meter_id_meters"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
        sa.UniqueConstraint(
            "meter_id",
            "alert_type",
            "usage_date",
            name=op.f("uq_alerts_meter_id_alert_type_usage_date"),
        ),
    )
    op.create_index(op.f("ix_alerts_created_at"), "alerts", ["created_at"], unique=False)
    op.create_index(op.f("ix_alerts_is_resolved"), "alerts", ["is_resolved"], unique=False)
    op.create_index(op.f("ix_alerts_meter_id"), "alerts", ["meter_id"], unique=False)
    op.create_table(
        "electricity_usages",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("meter_id", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kwh", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("voltage", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("current", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("power_factor", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("cost", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("kwh >= 0", name=op.f("ck_electricity_usages_kwh_non_negative")),
        sa.CheckConstraint(
            "power_factor >= 0 AND power_factor <= 1",
            name=op.f("ck_electricity_usages_power_factor_range"),
        ),
        sa.ForeignKeyConstraint(
            ["meter_id"],
            ["meters.id"],
            name=op.f("fk_electricity_usages_meter_id_meters"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_electricity_usages")),
        sa.UniqueConstraint(
            "meter_id", "recorded_at", name=op.f("uq_electricity_usages_meter_id_recorded_at")
        ),
    )
    op.create_index(
        op.f("ix_electricity_usages_recorded_at"),
        "electricity_usages",
        ["recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_electricity_usages_recorded_at"), table_name="electricity_usages")
    op.drop_table("electricity_usages")
    op.drop_index(op.f("ix_alerts_meter_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_is_resolved"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_created_at"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_meters_room_id"), table_name="meters")
    op.drop_table("meters")
    op.drop_index(op.f("ix_rooms_floor_id"), table_name="rooms")
    op.drop_table("rooms")
    op.drop_table("floors")
    op.drop_table("users")
    op.drop_index(op.f("ix_electricity_prices_effective_from"), table_name="electricity_prices")
    op.drop_table("electricity_prices")
    op.drop_table("buildings")
