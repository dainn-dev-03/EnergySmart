from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.floor import Floor


class Building(TimestampMixin, Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    address: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)

    # ON DELETE RESTRICT: the ORM must never null out children; the service returns 409 instead.
    floors: Mapped[list["Floor"]] = relationship(
        back_populates="building", passive_deletes="all", order_by="Floor.floor_number"
    )
