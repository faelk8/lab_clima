"""Caso de uso de coleta histórica com validação antes da rede."""

from datetime import date
from pathlib import Path
from typing import Any

from climatewatch.domain.weather import Location
from climatewatch.infrastructure.raw_store import RawStore
from climatewatch.infrastructure.weather_http import WeatherHttpClient

ALLOWED_VARIABLES = {"temperature_2m", "precipitation", "relative_humidity_2m", "wind_speed_10m"}


def download_weather(
    location: Location,
    start: str,
    end: str,
    variables: list[str],
    output: Path,
    client: WeatherHttpClient | None = None,
) -> dict[str, Any]:
    """Valida período/variáveis, coleta e grava payload bruto com provenance."""
    start_day, end_day = date.fromisoformat(start), date.fromisoformat(end)
    if start_day > end_day:
        raise ValueError("start deve ser anterior ou igual a end")
    if not variables or set(variables) - ALLOWED_VARIABLES:
        raise ValueError("variáveis vazias ou não suportadas")
    body, response = (client or WeatherHttpClient()).fetch(
        latitude=location.latitude,
        longitude=location.longitude,
        start=start,
        end=end,
        variables=variables,
        timezone_name=location.timezone_name,
    )
    return RawStore(output).save(
        body,
        {
            "source": "open-meteo",
            "location_id": location.location_id,
            "start": start,
            "end": end,
            "variables": variables,
            **response,
        },
    )
