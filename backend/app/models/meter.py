from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import MeterStatus, MeterType
from app.models.base import TimestampMixin, str_enum

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.electricity_usage import ElectricityUsage
    from app.models.room import Room


class Meter(TimestampMixin, Base):
    __tablename__ = "meters"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="RESTRICT"), index=True)
    meter_code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    meter_type: Mapped[MeterType] = mapped_column(str_enum(MeterType, "meter_type"))
    status: Mapped[MeterStatus] = mapped_column(
        str_enum(MeterStatus, "meter_status"),
        default=MeterStatus.ACTIVE,
        server_default=MeterStatus.ACTIVE.value,
    )
    installation_date: Mapped[date | None]

    room: Mapped["Room"] = relationship(back_populates="meters")
    # Large collections: never loaded implicitly; rows are removed by ON DELETE CASCADE.
    usages: WriteOnlyMapped["ElectricityUsage"] = relationship(
        back_populates="meter", cascade="all, delete-orphan", passive_deletes=True
    )
    alerts: WriteOnlyMapped["Alert"] = relationship(
        back_populates="meter", cascade="all, delete-orphan", passive_deletes=True
    )
