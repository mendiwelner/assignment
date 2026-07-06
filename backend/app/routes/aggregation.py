from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from ..dependencies import get_reading_filters, resolve_db_path
from ..schemas import ReadingFilters
from ..services import telemetry_service

router = APIRouter()


@router.get("/aggregation")
def aggregation(
    request: Request,
    filters: Annotated[ReadingFilters, Depends(get_reading_filters)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db_path: str | None = None,
) -> dict[str, object]:
    return telemetry_service.aggregate_readings(
        db_path=resolve_db_path(request, db_path),
        filters=filters,
        page=page,
        page_size=page_size,
    )
