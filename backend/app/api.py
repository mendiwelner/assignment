from fastapi import APIRouter

from .routes import aggregation, health, readings

router = APIRouter()
router.include_router(health.router)
router.include_router(readings.router)
router.include_router(aggregation.router)
