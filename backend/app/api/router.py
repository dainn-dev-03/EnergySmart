"""Aggregates every versioned route module under `settings.api_v1_prefix`."""

from fastapi import APIRouter

from app.api.routes import (
    alerts,
    analytics,
    audit_logs,
    auth,
    buildings,
    chat,
    dashboard,
    electricity_prices,
    electricity_usages,
    floors,
    meters,
    reports,
    rooms,
    users,
)

api_router = APIRouter()
for module in (
    auth,
    buildings,
    chat,
    floors,
    rooms,
    meters,
    electricity_usages,
    electricity_prices,
    dashboard,
    analytics,
    alerts,
    reports,
    audit_logs,
    users,
):
    api_router.include_router(module.router)
