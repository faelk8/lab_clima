"""Consulta externa opt-in; a suíte padrão funciona sem rede."""

import os

import pytest

from climatewatch.infrastructure.weather_http import WeatherHttpClient


@pytest.mark.skipif(os.getenv("CLIMATEWATCH_ONLINE") != "1", reason="consulta externa opt-in")
def test_open_meteo_short_request() -> None:
    """Confirma formato da fonte com uma data histórica curta."""
    import json

    body, meta = WeatherHttpClient(timeout_seconds=15).fetch(
        latitude=-23.5475,
        longitude=-46.63611,
        start="2024-01-01",
        end="2024-01-01",
        variables=["temperature_2m", "precipitation"],
        timezone_name="America/Sao_Paulo",
    )
    payload = json.loads(body)
    assert meta["status"] == 200
    assert len(payload["hourly"]["time"]) > 0
