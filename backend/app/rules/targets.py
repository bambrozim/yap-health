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
    "sodium_mg": Target(
        "sodium_mg", "daily_max", green=(0, 2000), yellow=(2000, 2500), unit="mg",
        source="OMS: ingestão de sódio < 2 g/dia"),
    "sugar_g": Target(
        "sugar_g", "daily_max", green=(0, 50), yellow=(50, 65), unit="g",
        source="OMS: açúcares livres < 10% das calorias (~50 g/2000 kcal); "
               "açúcar total usado como proxy"),
    "fiber_g": Target(
        "fiber_g", "daily_min", green=(25, float("inf")), yellow=(15, 25), unit="g",
        source="OMS/DRI: fibra alimentar >= 25 g/dia"),
    "bmi": Target(
        "bmi", "daily_range", green=(18.5, 24.9), yellow=(17, 29.9), unit="kg/m2",
        source="OMS: IMC saudável 18,5-24,9 (sobrepeso 25-29,9; abaixo do peso < 18,5)"),
}
