from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import ActorMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.building import Building
    from app.models.room import Room


class Floor(ActorMixin, TimestampMixin, Base):
    __tablename__ = "floors"
    # Also serves as the index on building_id (leading column).
    __table_args__ = (UniqueConstraint("building_id", "floor_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(100))
    floor_number: Mapped[int]
    description: Mapped[str | None] = mapped_column(Text)

    building: Mapped["Building"] = relationship(back_populates="floors")
    rooms: Mapped[list["Room"]] = relationship(
        back_populates="floor", passive_deletes="all", order_by="Room.code"
    )
