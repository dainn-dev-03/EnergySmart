from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.meter import Meter


class ElectricityUsage(CreatedAtMixin, Base):
    """Energy consumed by one meter during one interval (an hour) starting at `recorded_at`.

    `kwh` is the consumption of the interval, not a cumulative meter reading.
    """

    __tablename__ = "electricity_usages"
    __table_args__ = (
        # Leading column meter_id: this unique index is also the meter_id index.
        UniqueConstraint("meter_id", "recorded_at"),
        CheckConstraint("kwh >= 0", name="kwh_non_negative"),
        CheckConstraint("power_factor >= 0 AND power_factor <= 1", name="power_factor_range"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    meter_id: Mapped[int] = mapped_column(ForeignKey("meters.id", ondelete="CASCADE"))
    recorded_at: Mapped[datetime] = mapped_column(index=True)
    kwh: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    voltage: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    current: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    power_factor: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    cost: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    meter: Mapped["Meter"] = relationship(back_populates="usages")
