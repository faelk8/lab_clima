"""Particionamento de intervalos batch inclusivos."""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True, slots=True)
class DateWindow:
    """Intervalo inclusivo de datas para uma única consulta."""

    start: date
    end: date

    @property
    def days(self) -> int:
        """Número de datas do intervalo."""
        return (self.end - self.start).days + 1


def plan_windows(
    start: date, end: date, *, max_days: int = 7, max_requests: int = 30
) -> list[DateWindow]:
    """Divide intervalo contíguo em janelas sem lacunas nem sobreposição."""
    if start > end:
        raise ValueError("start deve ser anterior ou igual a end")
    if max_days < 1 or max_requests < 1:
        raise ValueError("limites precisam ser positivos")
    result: list[DateWindow] = []
    cursor = start
    while cursor <= end:
        window_end = min(cursor + timedelta(days=max_days - 1), end)
        result.append(DateWindow(cursor, window_end))
        cursor = window_end + timedelta(days=1)
        if len(result) > max_requests:
            raise ValueError(f"período excede orçamento de {max_requests} requests")
    return result
