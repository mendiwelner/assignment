from dataclasses import dataclass


@dataclass
class ReadingFilters:
    asset_id: str | None = None
    asset_type: str | None = None
    metric: str | None = None
    status: str | None = None
    start_time: str | None = None
    end_time: str | None = None
