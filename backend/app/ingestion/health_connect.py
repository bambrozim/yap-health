import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.ingestion.base import ParsedMeasurement

SOURCE = "health_connect"

# (table, metric, value_col, time_col, transform, unit)
_SCALAR_MAP = [
    ("steps_record_table", "steps", "count", "start_time", lambda v: float(v), "count"),
    ("active_calories_burned_record_table", "active_calories", "energy", "start_time", lambda v: float(v) / 1000.0, "kcal"),
    ("total_calories_burned_record_table", "total_calories", "energy", "start_time", lambda v: float(v) / 1000.0, "kcal"),
    ("distance_record_table", "distance_km", "distance", "start_time", lambda v: float(v) / 1000.0, "km"),
    ("heart_rate_variability_rmssd_record_table", "hrv_rmssd", "heart_rate_variability_millis", "time", lambda v: float(v), "ms"),
    ("resting_heart_rate_record_table", "resting_heart_rate", "beats_per_minute", "time", lambda v: float(v), "bpm"),
    ("oxygen_saturation_record_table", "spo2", "percentage", "time", lambda v: float(v), "%"),
]


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    cur = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}


def _to_utc(millis: int) -> datetime:
    return datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)


_MILLIS_PER_HOUR = 3_600_000.0
# Health Connect sleep stage codes -> charted metric (only deep/rem are surfaced).
_STAGE_METRIC = {5: "sleep_deep", 6: "sleep_rem"}


class HealthConnectSqliteImporter:
    source = SOURCE

    def matches(self, path: Path) -> bool:
        return path.suffix == ".db"

    def parse(self, path: Path) -> Iterator[ParsedMeasurement]:
        con = sqlite3.connect(path)
        try:
            for table, metric, vcol, tcol, fn, unit in _SCALAR_MAP:
                if not _table_exists(con, table):
                    continue
                cols = _columns(con, table)
                if vcol not in cols or tcol not in cols:
                    continue
                for value, millis in con.execute(
                        f"SELECT {vcol}, {tcol} FROM {table} WHERE {vcol} IS NOT NULL"):
                    yield ParsedMeasurement(metric, _to_utc(millis), fn(value), unit)

            # Heart rate samples live in a series table keyed by epoch_millis.
            if _table_exists(con, "heart_rate_record_series_table"):
                hr_cols = _columns(con, "heart_rate_record_series_table")
                if {"beats_per_minute", "epoch_millis"} <= hr_cols:
                    for bpm, millis in con.execute(
                            "SELECT beats_per_minute, epoch_millis "
                            "FROM heart_rate_record_series_table"):
                        yield ParsedMeasurement("heart_rate", _to_utc(millis),
                                                float(bpm), "bpm")

            yield from self._parse_sleep(con)
        finally:
            con.close()

    def _parse_sleep(self, con: sqlite3.Connection) -> Iterator[ParsedMeasurement]:
        # Nightly sleep duration: one value per session (hours), timestamped at
        # wake time so daily aggregation buckets a night by its wake-up date and
        # sums any fragmented sessions.
        if _table_exists(con, "sleep_session_record_table"):
            cols = _columns(con, "sleep_session_record_table")
            if {"start_time", "end_time"} <= cols:
                for start, end in con.execute(
                        "SELECT start_time, end_time FROM sleep_session_record_table"):
                    hours = (end - start) / _MILLIS_PER_HOUR
                    yield ParsedMeasurement("sleep_duration", _to_utc(end), hours, "h")

        # Deep / REM minutes per night, derived from stage rows (charted only).
        if _table_exists(con, "sleep_stages_table"):
            cols = _columns(con, "sleep_stages_table")
            if {"stage_start_time", "stage_end_time", "stage_type"} <= cols:
                for s_start, s_end, s_type in con.execute(
                        "SELECT stage_start_time, stage_end_time, stage_type "
                        "FROM sleep_stages_table"):
                    metric = _STAGE_METRIC.get(s_type)
                    if metric is None:
                        continue
                    hours = (s_end - s_start) / _MILLIS_PER_HOUR
                    yield ParsedMeasurement(metric, _to_utc(s_end), hours, "h")
