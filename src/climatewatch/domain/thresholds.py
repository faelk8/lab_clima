"""Regra demonstrativa de chuva em janela de 24 horas; não é alerta oficial."""

from dataclasses import dataclass
from enum import StrEnum


class ThresholdState(StrEnum):
    BELOW = "abaixo"
    AT = "no_limite"
    ABOVE = "acima"
    INCONCLUSIVE = "inconclusivo"


@dataclass(frozen=True, slots=True)
class ThresholdResult:
    state: ThresholdState
    precipitation_mm: float | None
    coverage_hours: int
    required_hours: int


def evaluate_precipitation_threshold(
    precipitation_mm: float | None,
    coverage_hours: int,
    threshold_mm: float = 50.0,
    required_hours: int = 24,
) -> ThresholdResult:
    """Classifica valor demonstrativo; cobertura baixa ou valor ausente é inconclusivo."""
    if threshold_mm < 0:
        raise ValueError("threshold_mm deve ser não negativo")
    if required_hours < 1 or required_hours > 24:
        raise ValueError("required_hours deve estar entre 1 e 24")
    if coverage_hours < 0 or coverage_hours > 24:
        raise ValueError("coverage_hours deve estar entre 0 e 24")
    if precipitation_mm is None or coverage_hours < required_hours:
        state = ThresholdState.INCONCLUSIVE
    elif precipitation_mm < threshold_mm:
        state = ThresholdState.BELOW
    elif precipitation_mm == threshold_mm:
        state = ThresholdState.AT
    else:
        state = ThresholdState.ABOVE
    return ThresholdResult(state, precipitation_mm, coverage_hours, required_hours)
