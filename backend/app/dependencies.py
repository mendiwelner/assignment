from dataclasses import dataclass

from fastapi import Request


@dataclass
class ReadingFilters:
    asset_id: str | None = None
    asset_type: str | None = None
    metric: str | None = None
    status: str | None = None
    start_time: str | None = None
    end_time: str | None = None


def resolve_db_path(request: Request, db_path: str | None = None) -> str | None:
    return db_path or getattr(request.app.state, "db_path", None)


def get_reading_filters(
    asset_id: str | None = None,
    asset_type: str | None = None,
    metric: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> ReadingFilters:
    return ReadingFilters(
        asset_id=asset_id,
        asset_type=asset_type,
        metric=metric,
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
