from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, UniqueConstraint, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import AlertSeverity, AlertType
from app.models.base import str_enum

if TYPE_CHECKING:
    from app.models.meter import Meter


class Alert(Base):
    __tablename__ = "alerts"
    # One alert per meter, type and evaluated day: re-running detection never duplicates.
    __table_args__ = (UniqueConstraint("meter_id", "alert_type", "usage_date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    meter_id: Mapped[int] = mapped_column(ForeignKey("meters.id", ondelete="CASCADE"), index=True)
    alert_type: Mapped[AlertType] = mapped_column(str_enum(AlertType, "alert_type", length=30))
    severity: Mapped[AlertSeverity] = mapped_column(str_enum(AlertSeverity, "alert_severity"))
    message: Mapped[str] = mapped_column(String(500))
    threshold_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    actual_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    usage_date: Mapped[date]
    is_resolved: Mapped[bool] = mapped_column(default=False, server_default=false(), index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    resolved_at: Mapped[datetime | None]

    meter: Mapped["Meter"] = relationship(back_populates="alerts")
