from datetime import date

from sqlalchemy.orm import Session

from app.domain.aggregation import daily_series
from app.domain.metrics import METRICS
from app.rules.scoring import domain_score, overall_score

DOMAINS = ["cardio", "activity", "sleep"]


def latest_daily_values(session: Session, metrics: list[str],
                        start: date, end: date) -> dict[str, float]:
    out: dict[str, float] = {}
    for m in metrics:
        series = daily_series(session, m, start, end)
        if series:
            out[m] = series[-1][1]
    return out


def build_scoreboard(session: Session, start: date, end: date) -> dict:
    all_metrics = list(METRICS.keys())
    latest = latest_daily_values(session, all_metrics, start, end)
    domains = {d: domain_score(d, latest) for d in DOMAINS}
    return {"overall": overall_score(domains), "domains": domains,
            "as_of": end.isoformat()}
