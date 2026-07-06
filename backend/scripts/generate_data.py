#!/usr/bin/env python3
"""
generate_data.py — Mock sensor-telemetry dataset generator
===========================================================

Produces a CSV of water-facility sensor readings for the "Sensor-Telemetry
Explorer" home assignment.

Schema (one row per reading):
    id           int        e.g. 8421301
    asset_id     str        e.g. "PS-042"
    asset_type   enum       pump_station | borehole | reservoir
    metric       enum       flow_rate | pressure | energy_kwh | water_level
    value        float      e.g. 37.4
    unit         str        m3/h | bar | kWh | m
    recorded_at  ISO ts     e.g. "2024-03-18T14:22:00Z"
    status       enum       ok | warning | fault

The data is a realistic-ish time series: each asset/metric pair is sampled at a
fixed interval, with daily seasonality, noise, and occasional spikes. Status is
derived from how far a reading sits outside its normal band.

A small fraction of rows are deliberately "dirty" (duplicates, out-of-range
values, blank fields, non-UTC timestamps) so the optional pandas cleaning step
has something real to do. Turn this off with --dirty-fraction 0.

Usage
-----
    python generate_data.py                        # ~1,000,000 rows -> telemetry.csv
    python generate_data.py --rows 200000          # smaller set
    python generate_data.py -o data/readings.csv   # custom path
    python generate_data.py --dirty-fraction 0     # perfectly clean data
    python generate_data.py --seed 7               # reproducible variation

No third-party dependencies — standard library only.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


# --------------------------------------------------------------------------- #
# Metric definitions: normal operating band + unit                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MetricSpec:
    name: str
    unit: str
    low: float          # bottom of normal range
    high: float         # top of normal range
    amplitude: float    # size of the daily swing
    noise: float        # gaussian noise stddev
    decimals: int


METRICS: dict[str, MetricSpec] = {
    "flow_rate":   MetricSpec("flow_rate",   "m3/h", 5.0,  60.0, 18.0, 2.5, 1),
    "pressure":    MetricSpec("pressure",    "bar",  1.5,  6.0,  1.2,  0.15, 2),
    "energy_kwh":  MetricSpec("energy_kwh",  "kWh",  0.5,  40.0, 12.0, 1.5, 2),
    "water_level": MetricSpec("water_level", "m",    0.5,  12.0, 3.0,  0.4, 2),
}

# Which metrics each asset type reports.
ASSET_TYPES: dict[str, list[str]] = {
    "pump_station": ["flow_rate", "pressure", "energy_kwh"],
    "borehole":     ["water_level", "flow_rate", "energy_kwh"],
    "reservoir":    ["water_level", "pressure"],
}

ASSET_PREFIX = {"pump_station": "PS", "borehole": "BH", "reservoir": "RS"}


@dataclass(frozen=True)
class Asset:
    asset_id: str
    asset_type: str


def build_assets(counts: dict[str, int]) -> list[Asset]:
    """Create a fleet, e.g. {'pump_station': 18, 'borehole': 14, 'reservoir': 8}."""
    assets: list[Asset] = []
    for atype, n in counts.items():
        prefix = ASSET_PREFIX[atype]
        for i in range(1, n + 1):
            assets.append(Asset(f"{prefix}-{i:03d}", atype))
    return assets


def reading_value(spec: MetricSpec, ts: datetime, rng: random.Random) -> float:
    """Base band midpoint + daily sine seasonality + noise, clamped to >= 0."""
    midpoint = (spec.low + spec.high) / 2.0
    # Daily cycle: peak mid-afternoon, trough pre-dawn.
    hour_angle = (ts.hour + ts.minute / 60.0) / 24.0 * 2 * math.pi
    seasonal = math.sin(hour_angle - math.pi / 2) * spec.amplitude / 2.0
    noise = rng.gauss(0, spec.noise)
    # Rare spike (equipment surge / demand event).
    spike = 0.0
    if rng.random() < 0.004:
        spike = rng.uniform(spec.amplitude, spec.amplitude * 2.5) * rng.choice([-1, 1])
    return max(0.0, midpoint + seasonal + noise + spike)


def derive_status(spec: MetricSpec, value: float) -> str:
    """ok inside band, warning just outside, fault far outside."""
    span = spec.high - spec.low
    if value < spec.low - 0.5 * span or value > spec.high + 0.5 * span:
        return "fault"
    if value < spec.low or value > spec.high:
        return "warning"
    return "ok"


def iso_utc(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def dirty_row(row: list, rng: random.Random) -> list:
    """
    Corrupt a copy of a row in one of several plausible ways, to exercise a
    cleaning/ETL step. Columns: [id, asset_id, asset_type, metric, value, unit,
    recorded_at, status].
    """
    row = list(row)
    kind = rng.choice(["negative", "blank_value", "local_tz", "outlier", "blank_status"])
    if kind == "negative":                     # impossible negative reading
        row[4] = round(-abs(float(row[4])) - rng.uniform(1, 5), 3)
    elif kind == "blank_value":                # missing value
        row[4] = ""
    elif kind == "local_tz":                   # non-UTC / offset timestamp
        # e.g. 2024-03-18T16:22:00+02:00 instead of ...Z
        base = datetime.strptime(row[6], "%Y-%m-%dT%H:%M:%SZ")
        row[6] = (base + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S+02:00")
    elif kind == "outlier":                    # absurd out-of-range spike
        row[4] = round(float(row[4]) * rng.uniform(50, 200), 3)
        row[7] = "fault"
    elif kind == "blank_status":               # missing status
        row[7] = ""
    return row


def generate(
    rows_target: int,
    output: str,
    seed: int,
    dirty_fraction: float,
    start: datetime,
    interval_minutes: int,
    duplicate_fraction: float,
) -> None:
    rng = random.Random(seed)

    # A fleet of 40 assets by default.
    assets = build_assets({"pump_station": 18, "borehole": 14, "reservoir": 8})
    # Flatten into (asset, metric, spec) series.
    series = [
        (a, m, METRICS[m])
        for a in assets
        for m in ASSET_TYPES[a.asset_type]
    ]

    next_id = 1
    written = 0
    step = timedelta(minutes=interval_minutes)

    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["id", "asset_id", "asset_type", "metric",
             "value", "unit", "recorded_at", "status"]
        )

        ts = start
        # Advance through time, emitting one row per series per timestep, until
        # we hit the target row count.
        while written < rows_target:
            for asset, metric, spec in series:
                if written >= rows_target:
                    break
                val = round(reading_value(spec, ts, rng), spec.decimals)
                status = derive_status(spec, val)
                row = [
                    next_id, asset.asset_id, asset.asset_type, metric,
                    val, spec.unit, iso_utc(ts), status,
                ]
                next_id += 1

                # Occasionally emit a corrupted variant instead of the clean row.
                if dirty_fraction and rng.random() < dirty_fraction:
                    row = dirty_row(row, rng)

                writer.writerow(row)
                written += 1

                # Occasionally duplicate the row (same id) to test dedupe.
                if duplicate_fraction and rng.random() < duplicate_fraction and written < rows_target:
                    writer.writerow(row)
                    written += 1

            ts += step

    print(f"Wrote {written:,} rows to {output}")
    print(f"  assets: {len(assets)}  series: {len(series)}")
    print(f"  time span: {iso_utc(start)} .. {iso_utc(ts)}  (every {interval_minutes} min)")
    if dirty_fraction:
        print(f"  ~{dirty_fraction:.1%} dirty rows + ~{duplicate_fraction:.1%} duplicates "
              f"(set --dirty-fraction 0 for clean data)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate mock water-facility telemetry CSV.")
    p.add_argument("--rows", type=int, default=1_000_000,
                   help="approximate number of rows (default: 1,000,000)")
    p.add_argument("-o", "--output", default="telemetry.csv",
                   help="output CSV path (default: telemetry.csv)")
    p.add_argument("--seed", type=int, default=42, help="random seed (default: 42)")
    p.add_argument("--dirty-fraction", type=float, default=0.01,
                   help="fraction of rows that are corrupted, 0 to disable (default: 0.01)")
    p.add_argument("--duplicate-fraction", type=float, default=0.003,
                   help="fraction of rows duplicated (default: 0.003)")
    p.add_argument("--start", default="2024-01-01T00:00:00Z",
                   help="first timestamp, ISO UTC (default: 2024-01-01T00:00:00Z)")
    p.add_argument("--interval-minutes", type=int, default=15,
                   help="sampling interval per series in minutes (default: 15)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    start = datetime.strptime(args.start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    generate(
        rows_target=args.rows,
        output=args.output,
        seed=args.seed,
        dirty_fraction=args.dirty_fraction,
        start=start.replace(tzinfo=None),  # we format UTC manually
        interval_minutes=args.interval_minutes,
        duplicate_fraction=args.duplicate_fraction,
    )


if __name__ == "__main__":
    main()
