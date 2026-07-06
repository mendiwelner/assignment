import csv
from pathlib import Path

from .database import DEFAULT_CSV_PATH, get_connection, init_db


def load_csv(csv_path: str | Path | None = None, db_path: str | Path | None = None, chunk_size: int = 1000) -> int:
    init_db(db_path)
    target_csv = Path(csv_path or DEFAULT_CSV_PATH)
    if not target_csv.exists():
        raise FileNotFoundError(f"CSV file not found: {target_csv}")

    connection = get_connection(db_path)
    existing_count = connection.execute("SELECT COUNT(*) FROM telemetry_readings").fetchone()[0]
    if existing_count > 0:
        connection.close()
        return existing_count
    rows: list[tuple] = []
    inserted = 0
    skipped = 0
    with target_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            # Basic validation and type coercion for dirty rows
            try:
                rid = int(row.get("id", ""))
                asset_id = row.get("asset_id", "")
                asset_type = row.get("asset_type", "")
                metric = row.get("metric", "")
                raw_value = row.get("value", "")
                unit = row.get("unit", "")
                recorded_at = row.get("recorded_at", "")
                status = row.get("status", "")

                # Skip rows with missing essential fields
                if not (asset_id and asset_type and metric and raw_value and recorded_at and status):
                    skipped += 1
                    continue

                value = float(raw_value)
            except Exception:
                skipped += 1
                continue

            rows.append((rid, asset_id, asset_type, metric, value, unit, recorded_at, status))

            if len(rows) >= chunk_size:
                # Use INSERT OR IGNORE to tolerate duplicate PKs from dirty CSVs
                connection.executemany(
                    """
                    INSERT OR IGNORE INTO telemetry_readings (id, asset_id, asset_type, metric, value, unit, recorded_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                inserted += connection.total_changes
                rows.clear()

    if rows:
        connection.executemany(
            """
            INSERT OR IGNORE INTO telemetry_readings (id, asset_id, asset_type, metric, value, unit, recorded_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        inserted += connection.total_changes

    connection.commit()
    connection.close()

    # total_changes is cumulative for the connection lifecycle; return meaningful counts
    print(f"Inserted ~{inserted} rows (skipped {skipped} dirty rows).")
    return inserted


if __name__ == "__main__":
    load_csv()
