from dataclasses import dataclass

from app.rules.targets import TARGETS, Target


@dataclass
class Evaluation:
    metric: str
    value: float
    status: str      # green | yellow | red
    message: str
    source: str


def _in(value: float, rng: tuple) -> bool:
    return rng[0] <= value <= rng[1]


def evaluate_value(metric: str, value: float) -> Evaluation | None:
    target: Target | None = TARGETS.get(metric)
    if target is None:
        return None
    if _in(value, target.green):
        status, msg = "green", f"{metric} dentro da meta"
    elif _in(value, target.yellow):
        status, msg = "yellow", f"{metric} em atenção"
    else:
        status, msg = "red", f"{metric} fora da faixa recomendada"
    return Evaluation(metric, value, status, msg, target.source)
