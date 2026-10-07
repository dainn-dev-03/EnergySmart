"""Seed demo data into the database configured in backend/.env.

Usage (from backend/):
    python -m app.seed.seed_database            # first run: full history; later: top up to now
    python -m app.seed.seed_database --reset    # wipe demo data (users kept) and rebuild
    python -m app.seed.seed_database --days 30  # history length for a fresh seed
"""

import argparse
import logging
import time
from collections.abc import Sequence

from app.core.database import SessionLocal
from app.seed.demo_data import reset_demo_data, seed_demo_data
from app.seed.settings import SeedSettings
from app.seed.users import seed_users

logger = logging.getLogger("seed")


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dữ liệu demo cho EnergySmart")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Xóa dữ liệu demo (tòa nhà, công tơ, điện năng, cảnh báo, bảng giá) rồi tạo lại",
    )
    parser.add_argument(
        "--days", type=int, help="Số ngày dữ liệu lịch sử khi tạo mới (mặc định SEED_DAYS)"
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    args = _parse_args(argv)
    settings = SeedSettings()
    days = args.days or settings.days
    started = time.perf_counter()

    with SessionLocal() as db:
        created_users = seed_users(db, settings)
        if args.reset:
            logger.warning("Resetting demo data (users are kept)")
            reset_demo_data(db)
        report = seed_demo_data(db, days=days, random_seed=settings.random_seed)
        db.commit()

    if created_users:
        logger.info("Created users: %s", ", ".join(created_users))
    action = (
        f"Created demo building with {days} days of history"
        if report.created_master_data
        else "Topped up existing demo data"
    )
    logger.info(
        "%s: %d meters, %d hourly readings, %d new alerts (%d open), data up to %s (%.1fs)",
        action,
        report.meter_count,
        report.inserted_readings,
        report.created_alerts,
        report.open_alerts,
        report.last_reading_at.strftime("%Y-%m-%d %H:%M"),
        time.perf_counter() - started,
    )


if __name__ == "__main__":
    main()
