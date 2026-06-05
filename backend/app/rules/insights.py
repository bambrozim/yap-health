from dataclasses import dataclass
from datetime import date
from statistics import mean


@dataclass
class Insight:
    metric: str
    text: str
    severity: str   # info | warning


# metric -> (delta threshold, label, source)
_TREND = {
    "resting_heart_rate": (5.0, "FC de repouso",
                           "AHA: a sustained rise in resting HR can reflect fatigue/stress"),
    "hrv_rmssd": (-10.0, "HRV",
                  "HRV trends track recovery and autonomic balance"),
}


def trend_insight(metric: str, baseline: list[tuple[date, float]],
                  recent: list[tuple[date, float]]) -> Insight | None:
    cfg = _TREND.get(metric)
    if cfg is None or not baseline or not recent:
        return None
    threshold, label, _src = cfg
    base = mean(v for _, v in baseline)
    cur = mean(v for _, v in recent)
    delta = cur - base
    if threshold > 0 and delta >= threshold:
        return Insight(metric,
                       f"Seu {label} subiu {delta:.0f} vs. a média das últimas 4 semanas",
                       "warning")
    if threshold < 0 and delta <= threshold:
        return Insight(metric,
                       f"Seu {label} caiu {abs(delta):.0f} vs. a média das últimas 4 semanas",
                       "warning")
    return None
