from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    metric: str
    kind: str            # "daily_min" | "daily_range"
    green: tuple         # range considered green
    yellow: tuple        # wider tolerance band (outside -> red)
    unit: str
    source: str


TARGETS = {
    "steps": Target(
        "steps", "daily_min", green=(8000, float("inf")), yellow=(5000, 8000),
        unit="count",
        source="WHO physical-activity rationale / step-count literature (~8k+/day)"),
    "spo2": Target(
        "spo2", "daily_min", green=(95, 100), yellow=(92, 95), unit="%",
        source="Clinical norm (Mayo Clinic / AHA): normal SpO2 95-100%"),
    "resting_heart_rate": Target(
        "resting_heart_rate", "daily_range", green=(60, 100), yellow=(50, 110),
        unit="bpm",
        source="American Heart Association: normal resting heart rate 60-100 bpm"),
    "sleep_duration": Target(
        "sleep_duration", "daily_range", green=(7, 9), yellow=(6, 10), unit="h",
        source="National Sleep Foundation: adults (18-64) need 7-9 h/night"),
}
