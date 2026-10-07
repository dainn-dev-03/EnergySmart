"""Aggregates every versioned route module under `settings.api_v1_prefix`."""

from fastapi import APIRouter

from app.api.routes import (
    alerts,
    audit_logs,
    analytics,
    auth,
    buildings,
    dashboard,
    electricity_prices,
    electricity_usages,
    floors,
    meters,
    reports,
    rooms,
)

api_router = APIRouter()
for module in (
    auth,
    buildings,
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
):
    api_router.include_router(module.router)
