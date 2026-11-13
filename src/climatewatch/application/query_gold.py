"""Casos de uso para leitura de agregados Gold."""

from datetime import date
from typing import Any

from climatewatch.infrastructure.gold_reader import GoldReader


class QueryGold:
    """Valida parâmetros e expõe leitura limitada das tabelas Gold."""

    def __init__(self, reader: GoldReader) -> None:
        self._reader = reader

    def daily(self, location_id: str, start: date, end: date) -> list[dict[str, Any]]:
        return self._reader.daily(location_id, start, end)

    def indicators(
        self, location_id: str, start: date, end: date
    ) -> list[dict[str, Any]]:
        return self._reader.indicators(location_id, start, end)
