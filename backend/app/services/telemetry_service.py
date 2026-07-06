from ..database import get_connection
from ..schemas import ReadingFilters


def _build_filters(filters: ReadingFilters) -> tuple[list[str], list[object]]:
    clauses = []
    values: list[object] = []
    if filters.asset_id:
        clauses.append("asset_id = ?")
        values.append(filters.asset_id)
    if filters.asset_type:
        clauses.append("asset_type = ?")
        values.append(filters.asset_type)
    if filters.metric:
        clauses.append("metric = ?")
        values.append(filters.metric)
    if filters.status:
        clauses.append("status = ?")
        values.append(filters.status)
    if filters.start_time:
        clauses.append("recorded_at >= ?")
        values.append(filters.start_time)
    if filters.end_time:
        clauses.append("recorded_at <= ?")
        values.append(filters.end_time)
    return clauses, values


def _where_clause(filters: ReadingFilters) -> tuple[str, list[object]]:
    clauses, values = _build_filters(filters)
    where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_clause, values


def _pagination(page: int, page_size: int, total: int) -> dict[str, int]:
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": max((total + page_size - 1) // page_size, 0),
    }


def _invalid_time_range(filters: ReadingFilters) -> bool:
    return bool(filters.start_time and filters.end_time and filters.start_time > filters.end_time)


def list_readings(
    db_path: str | None,
    filters: ReadingFilters,
    page: int,
    page_size: int,
) -> dict[str, object]:
    if _invalid_time_range(filters):
        return {"items": [], "pagination": _pagination(page, page_size, 0)}

    where_clause, values = _where_clause(filters)
    connection = get_connection(db_path)
    try:
        total = connection.execute(
            f"SELECT COUNT(*) AS total FROM telemetry_readings{where_clause}",
            values,
        ).fetchone()["total"]

        offset = (page - 1) * page_size
        rows = connection.execute(
            f"""
            SELECT id, asset_id, asset_type, metric, value, unit, recorded_at, status
            FROM telemetry_readings{where_clause}
            ORDER BY recorded_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            values + [page_size, offset],
        ).fetchall()
    finally:
        connection.close()

    return {
        "items": [
            {
                "id": row["id"],
                "asset_id": row["asset_id"],
                "asset_type": row["asset_type"],
                "metric": row["metric"],
                "value": row["value"],
                "unit": row["unit"],
                "recorded_at": row["recorded_at"],
                "status": row["status"],
            }
            for row in rows
        ],
        "pagination": _pagination(page, page_size, total),
    }


def aggregate_readings(
    db_path: str | None,
    filters: ReadingFilters,
    page: int,
    page_size: int,
) -> dict[str, object]:
    if _invalid_time_range(filters):
        return {"items": [], "count": 0, "pagination": _pagination(page, page_size, 0)}

    where_clause, values = _where_clause(filters)
    offset = (page - 1) * page_size
    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            f"""
            WITH grouped AS (
                SELECT asset_id, asset_type, metric,
                       AVG(value) AS average,
                       MIN(value) AS minimum,
                       MAX(value) AS maximum,
                       COUNT(*) AS reading_count
                FROM telemetry_readings{where_clause}
                GROUP BY asset_id, asset_type, metric
            )
            SELECT asset_id, asset_type, metric, average, minimum, maximum, reading_count,
                   (SELECT COUNT(*) FROM grouped) AS total
            FROM grouped
            ORDER BY asset_id, metric
            LIMIT ? OFFSET ?
            """,
            values + [page_size, offset],
        ).fetchall()
    finally:
        connection.close()

    total = rows[0]["total"] if rows else 0
    return {
        "items": [
            {
                "asset_id": row["asset_id"],
                "asset_type": row["asset_type"],
                "metric": row["metric"],
                "average": round(row["average"], 2),
                "minimum": round(row["minimum"], 2),
                "maximum": round(row["maximum"], 2),
                "count": row["reading_count"],
            }
            for row in rows
        ],
        "count": total,
        "pagination": _pagination(page, page_size, total),
    }
