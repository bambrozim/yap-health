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
    MetricDef("sleep_duration", "sleep", "sum", "h"),
    MetricDef("sleep_deep", "sleep", "sum", "h"),
    MetricDef("sleep_rem", "sleep", "sum", "h"),
    MetricDef("energy_kcal", "nutrition", "sum", "kcal"),
    MetricDef("protein_g", "nutrition", "sum", "g"),
    MetricDef("carbs_g", "nutrition", "sum", "g"),
    MetricDef("fat_g", "nutrition", "sum", "g"),
    MetricDef("fiber_g", "nutrition", "sum", "g"),
    MetricDef("sugar_g", "nutrition", "sum", "g"),
    MetricDef("sodium_mg", "nutrition", "sum", "mg"),
    MetricDef("weight_kg", "body", "mean", "kg"),
    MetricDef("bmi", "body", "mean", "kg/m2"),
    MetricDef("body_fat_pct", "body", "mean", "%"),
]}


def metrics_for_domain(domain: str) -> list[str]:
    return [k for k, m in METRICS.items() if m.domain == domain]
