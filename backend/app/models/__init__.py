"""Import every model so `Base.metadata` is complete (required by Alembic autogenerate)."""

from app.core.database import Base
from app.models.alert import Alert
from app.models.building import Building
from app.models.electricity_price import ElectricityPrice
from app.models.electricity_usage import ElectricityUsage
from app.models.floor import Floor
from app.models.meter import Meter
from app.models.room import Room
from app.models.user import User

__all__ = [
    "Alert",
    "Base",
    "Building",
    "ElectricityPrice",
    "ElectricityUsage",
    "Floor",
    "Meter",
    "Room",
    "User",
]
