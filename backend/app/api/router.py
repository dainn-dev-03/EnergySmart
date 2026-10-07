"""Aggregates every versioned route module under `settings.api_v1_prefix`."""

from fastapi import APIRouter

from app.api.routes import (
    auth,
    buildings,
    electricity_prices,
    electricity_usages,
    floors,
    meters,
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
):
    api_router.include_router(module.router)
