from datetime import date, datetime, time, timezone
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Measurement
from app.domain.metrics import METRICS

_AGG = {"sum": sum, "mean": mean, "min": min}


def daily_series(session: Session, metric: str, start: date, end: date
                 ) -> list[tuple[date, float]]:
    agg = _AGG[METRICS[metric].agg]
    lo = datetime.combine(start, time.min, tzinfo=timezone.utc)
    hi = datetime.combine(end, time.max, tzinfo=timezone.utc)
    rows = session.scalars(
        select(Measurement).where(
            Measurement.metric == metric,
            Measurement.ts >= lo, Measurement.ts <= hi)).all()
    buckets: dict[date, list[float]] = {}
    for r in rows:
        day = r.ts.astimezone(timezone.utc).date()
        buckets.setdefault(day, []).append(r.value)
    return [(d, round(float(agg(vals)), 2)) for d, vals in sorted(buckets.items())]
