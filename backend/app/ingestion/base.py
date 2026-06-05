import hashlib
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedMeasurement:
    metric: str
    ts: datetime
    value: float
    unit: str


@dataclass
class ParsedWorkout:
    type: str
    start_ts: datetime
    end_ts: datetime
    duration_s: int
    distance_km: float
    calories: float
    source_uuid: str | None = None


def make_dedup_key(metric: str, ts: datetime, value: float,
                   source: str, source_uuid: str | None) -> str:
    if source_uuid:
        return f"{source}:{source_uuid}"
    raw = f"{metric}|{ts.isoformat()}|{value}"
    digest = hashlib.sha1(raw.encode()).hexdigest()[:16]
    return f"{source}:{digest}"
