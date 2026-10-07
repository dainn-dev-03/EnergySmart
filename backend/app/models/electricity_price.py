from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import ActorMixin, CreatedAtMixin


class ElectricityPrice(ActorMixin, CreatedAtMixin, Base):
    """Flat VND/kWh price valid from `effective_from` to `effective_to` (NULL = still valid)."""

    __tablename__ = "electricity_prices"
    __table_args__ = (
        CheckConstraint("price_per_kwh > 0", name="price_positive"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from", name="effective_range"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price_per_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    effective_from: Mapped[date] = mapped_column(index=True)
    effective_to: Mapped[date | None]
