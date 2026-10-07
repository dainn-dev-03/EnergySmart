from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import ActorMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.floor import Floor
    from app.models.meter import Meter


class Room(ActorMixin, TimestampMixin, Base):
    __tablename__ = "rooms"
    __table_args__ = (CheckConstraint("area > 0", name="area_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    area: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    description: Mapped[str | None] = mapped_column(Text)

    floor: Mapped["Floor"] = relationship(back_populates="rooms")
    meters: Mapped[list["Meter"]] = relationship(
        back_populates="room", passive_deletes="all", order_by="Meter.meter_code"
    )
