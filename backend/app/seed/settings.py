"""Demo-only settings (SEED_* variables). The API never reads these at runtime."""

from pydantic import EmailStr, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SeedSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="SEED_", extra="ignore"
    )

    admin_username: str
    admin_password: SecretStr
    admin_email: EmailStr
    admin_full_name: str = "Quản trị viên"
    # Password of the demo `manager` and `viewer` accounts; they are skipped when unset.
    demo_password: SecretStr | None = None
    # Days of hourly history created on the first run.
    days: int = Field(90, ge=1, le=366)
    # Fixed seed so the generated data is reproducible.
    random_seed: int = 42
