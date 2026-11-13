"""Testes do contrato v1 e das fixtures offline."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from climatewatch.domain.weather import ContractError, Location, WeatherRecord, parse_hourly_payload

FIXTURES = Path("data/fixtures")
LOCATION = Location("br-sp-sao-paulo", "São Paulo", -23.5, -46.6, "America/Sao_Paulo")


def test_fixture_regular_has_expected_rows() -> None:
    """Confere payload sintético regular sem rede."""
    payload = json.loads((FIXTURES / "hourly_regular.json").read_text())
    assert len(parse_hourly_payload(payload, LOCATION)) == 3


def test_misaligned_arrays_are_rejected() -> None:
    """Rejeita arrays divergentes para não truncar observações."""
    payload = json.loads((FIXTURES / "hourly_regular.json").read_text())
    payload["hourly"]["precipitation"].pop()
    with pytest.raises(ContractError, match="desalinhado"):
        parse_hourly_payload(payload, LOCATION)


def test_naive_time_and_invalid_values_are_rejected() -> None:
    """Exige timestamp com fuso e unidades dentro dos limites."""
    with pytest.raises(ContractError, match="timezone"):
        WeatherRecord("x", datetime(2024, 1, 1), None, 0, None, None)
    with pytest.raises(ContractError, match="humidity"):
        WeatherRecord("x", datetime.now(timezone.utc), None, 0, 101, None)


def test_local_timestamp_is_normalized_to_utc() -> None:
    """Interpreta hora sem offset no fuso configurado e normaliza para UTC."""
    payload = json.loads((FIXTURES / "hourly_nulls.json").read_text())
    record = parse_hourly_payload(payload, LOCATION)[0]
    assert record.measurement_time.isoformat() == "2024-01-01T03:00:00+00:00"
