from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDef:
    key: str
    domain: str
    agg: str   # "sum" | "mean" | "min"
    unit: str


METRICS = {m.key: m for m in [
    MetricDef("steps", "activity", "sum", "count"),
    MetricDef("active_calories", "activity", "sum", "kcal"),
    MetricDef("total_calories", "activity", "sum", "kcal"),
    MetricDef("distance_km", "activity", "sum", "km"),
    MetricDef("heart_rate", "cardio", "mean", "bpm"),
    MetricDef("hrv_rmssd", "cardio", "mean", "ms"),
    MetricDef("resting_heart_rate", "cardio", "min", "bpm"),
    MetricDef("spo2", "cardio", "mean", "%"),
]}


def metrics_for_domain(domain: str) -> list[str]:
    return [k for k, m in METRICS.items() if m.domain == domain]
