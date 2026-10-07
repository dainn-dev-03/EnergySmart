"""Application settings, loaded from environment variables and `backend/.env`."""

from functools import lru_cache
from typing import Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url

# RFC 7518 §3.2: an HS256 key must be at least 256 bits.
MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EnergySmart API"
    app_version: str = "0.1.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database: DATABASE_URL wins when set; otherwise the URL is built from POSTGRES_* parts.
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: SecretStr = SecretStr("")
    postgres_test_db: str = "energy_management_test"
    # Fail fast instead of hanging when PostgreSQL is unreachable.
    database_connect_timeout_seconds: int = 5

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    cors_origins: str = "http://localhost:3000"
    app_timezone: str = "Asia/Ho_Chi_Minh"

    # Abnormal consumption detection: daily kWh / average of the same day type (weekday or
    # weekend) over the previous `alert_baseline_days` days.
    alert_baseline_days: int = 14
    alert_min_reference_days: int = 3
    alert_ratio_info: float = 1.2
    alert_ratio_warning: float = 1.5
    alert_ratio_critical: float = 2.0

    @field_validator("jwt_secret_key")
    @classmethod
    def _jwt_secret_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least {MIN_JWT_SECRET_LENGTH} characters. "
                'Generate one: python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        return value

    @model_validator(mode="after")
    def _require_database_config(self) -> Self:
        if not self.database_url and not (self.postgres_db and self.postgres_user):
            raise ValueError(
                "Database is not configured: set DATABASE_URL or POSTGRES_DB + POSTGRES_USER "
                "(+ POSTGRES_PASSWORD) in backend/.env"
            )
        return self

    @property
    def database_uri(self) -> URL:
        if self.database_url:
            return make_url(self.database_url)
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value() or None,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def test_database_uri(self) -> URL:
        return self.database_uri.set(database=self.postgres_test_db)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
