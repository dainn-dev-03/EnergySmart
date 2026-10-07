from sqlalchemy import func, select

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_username(self, username: str) -> User | None:
        """Case-insensitive lookup, so `Admin` and `admin` are the same account."""
        return self.db.scalar(select(User).where(func.lower(User.username) == username.lower()))

    def admin_count(self) -> int:
        return self._count(User.role == "ADMIN", User.is_active.is_(True))
