"""Seed demo data into the database configured in backend/.env.

Usage (from backend/):
    python -m app.seed.seed_database
"""

import argparse
import logging
from collections.abc import Sequence

from app.core.database import SessionLocal
from app.seed.settings import SeedSettings
from app.seed.users import seed_users

logger = logging.getLogger("seed")


def main(argv: Sequence[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    parser = argparse.ArgumentParser(description="Tạo dữ liệu demo cho EnergySmart")
    parser.parse_args(argv)

    settings = SeedSettings()
    with SessionLocal() as db:
        created_users = seed_users(db, settings)
        db.commit()

    if created_users:
        logger.info("Created users: %s", ", ".join(created_users))
    else:
        logger.info("Users already exist, nothing to create")


if __name__ == "__main__":
    main()
