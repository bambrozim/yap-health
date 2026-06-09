import csv
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from app.config import settings
from app.ingestion.base import ParsedMeasurement

SOURCE = "health_sync"
_DATE_FMT = "%Y.%m.%d %H:%M:%S"

# Single-value CSVs: header column -> (metric, unit). Checked in order; the
# resting-HR column must win over the plain "Heart rate" column.
_SCALAR_COLUMNS = [
    ("Steps", "steps", "count"),
    ("Resting heart rate", "resting_heart_rate", "bpm"),
    ("heart rate variability", "hrv_rmssd", "ms"),
    ("Oxygen saturation", "spo2", "%"),
    ("Heart rate", "heart_rate", "bpm"),
]

# Nutrition: CSV column -> (metric, unit). Values already in kcal / grams.
_NUTRIENT_COLUMNS = {
    "kCal": ("energy_kcal", "kcal"),
    "Carbohydrate (gram)": ("carbs_g", "g"),
    "Fat (gram)": ("fat_g", "g"),
    "Fiber (gram)": ("fiber_g", "g"),
    "Sugar (gram)": ("sugar_g", "g"),
    "Protein (gram)": ("protein_g", "g"),
}


def _parse_ts(date_str: str) -> datetime:
    return datetime.strptime(date_str, _DATE_FMT).replace(tzinfo=timezone.utc)


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class HealthSyncCsvImporter:
    """Imports Health Sync CSV exports, dispatching by header columns.

    These CSVs are the data source for the scored domains when the Health
    Connect ``.db`` export is unavailable. Units are already canonical
    (kcal, grams, kg) so no scaling is applied. Body height has no CSV column,
    so BMI is derived from a configured height (``settings.height_m``).
    """

    source = SOURCE

    def __init__(self, height_m: float | None = None):
        self.height_m = height_m if height_m is not None else settings.height_m

    def matches(self, path: Path) -> bool:
        return path.suffix == ".csv"

    def parse(self, path: Path) -> Iterator[ParsedMeasurement]:
        with path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            header = reader.fieldnames or []
            if "Sleep stage" in header:
                yield from self._parse_sleep(reader)
            elif "kCal" in header:
                yield from self._parse_nutrition(reader, header)
            elif "Weight" in header:
                yield from self._parse_weight(reader)
            elif "Active calories" in header:
                yield from self._parse_energy(reader)
            else:
                yield from self._parse_scalar(reader, header)

    def _parse_scalar(self, reader, header) -> Iterator[ParsedMeasurement]:
        match = next(((col, metric, unit) for col, metric, unit in _SCALAR_COLUMNS
                      if col in header), None)
        if match is None:
            return
        col, metric, unit = match
        for row in reader:
            value = _to_float(row.get(col))
            if value is None:
                continue
            yield ParsedMeasurement(metric, _parse_ts(row["Date"]), value, unit)

    def _parse_energy(self, reader) -> Iterator[ParsedMeasurement]:
        for row in reader:
            ts = _parse_ts(row["Date"])
            for col, metric in (("Active calories", "active_calories"),
                                ("Total calories", "total_calories")):
                value = _to_float(row.get(col))
                if value is not None:
                    yield ParsedMeasurement(metric, ts, value, "kcal")

    def _parse_sleep(self, reader) -> Iterator[ParsedMeasurement]:
        # Sleep is logged as stage segments. Aggregate per night so a night that
        # crosses midnight is not split: segments from 18:00 on belong to the
        # next day's wake date. One value per metric per night avoids both the
        # midnight split and dedup-key collisions between segments.
        totals: dict[tuple[str, object], float] = defaultdict(float)
        for row in reader:
            seconds = _to_float(row.get("Duration in seconds"))
            stage = (row.get("Sleep stage") or "").strip().lower()
            if seconds is None:
                continue
            ts = _parse_ts(row["Date"])
            wake = ts.date() + timedelta(days=1) if ts.hour >= 18 else ts.date()
            hours = seconds / 3600.0
            if stage != "awake":
                totals[("sleep_duration", wake)] += hours
            if stage == "deep":
                totals[("sleep_deep", wake)] += hours
            elif stage == "rem":
                totals[("sleep_rem", wake)] += hours
        for (metric, wake), hours in totals.items():
            ts = datetime(wake.year, wake.month, wake.day, 12, tzinfo=timezone.utc)
            yield ParsedMeasurement(metric, ts, round(hours, 4), "h")

    def _parse_nutrition(self, reader, header) -> Iterator[ParsedMeasurement]:
        present = [(col, metric, unit) for col, (metric, unit)
                   in _NUTRIENT_COLUMNS.items() if col in header]
        for row in reader:
            if (_to_float(row.get("kCal")) or 0) < 1:
                continue  # skip empty/placeholder entries
            ts = _parse_ts(row["Date"])
            for col, metric, unit in present:
                value = _to_float(row.get(col))
                if value is not None:
                    yield ParsedMeasurement(metric, ts, value, unit)

    def _parse_weight(self, reader) -> Iterator[ParsedMeasurement]:
        for row in reader:
            kg = _to_float(row.get("Weight"))
            ts = _parse_ts(row["Date"])
            if kg:
                yield ParsedMeasurement("weight_kg", ts, kg, "kg")
                if self.height_m:
                    yield ParsedMeasurement("bmi", ts, kg / (self.height_m ** 2),
                                            "kg/m2")
            fat = _to_float(row.get("Body fat percentage"))
            if fat:
                yield ParsedMeasurement("body_fat_pct", ts, fat, "%")
