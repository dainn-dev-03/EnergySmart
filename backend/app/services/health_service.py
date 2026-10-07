import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceUnavailableError
from app.schemas.health import HealthRead

logger = logging.getLogger(__name__)


class HealthService:
    def __init__(self, db: Session, app_version: str) -> None:
        self.db = db
        self.app_version = app_version

    def check(self) -> HealthRead:
        try:
            self.db.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            logger.error("Database health check failed: %s", exc)
            raise ServiceUnavailableError(
                "Không kết nối được cơ sở dữ liệu", code="DATABASE_UNAVAILABLE"
            ) from exc
        return HealthRead(status="ok", database="ok", version=self.app_version)
