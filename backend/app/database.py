import os
import sqlite3
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "telemetry.db"
DEFAULT_CSV_PATH = BASE_DIR / "data" / "telemetry.csv"


def get_db_path(db_path: Optional[str] = None) -> Path:
    if db_path:
        return Path(db_path)
    return Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Optional[str] = None) -> None:
    connection = get_connection(db_path)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS telemetry_readings (
            id INTEGER PRIMARY KEY,
            asset_id TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_asset_id ON telemetry_readings(asset_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_asset_type ON telemetry_readings(asset_type)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_metric ON telemetry_readings(metric)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_status ON telemetry_readings(status)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_recorded_at ON telemetry_readings(recorded_at)")
    connection.commit()
    connection.close()
