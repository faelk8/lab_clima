"""Teste de retomada e quarentena sem chamada de rede."""

import json
from pathlib import Path

import pytest

from climatewatch.application.download import download_weather
from climatewatch.domain.weather import ContractError, Location
from climatewatch.infrastructure.batch_manifest import BatchManifest


class InvalidClient:
    """Devolve payload válido como JSON, mas incompleto no contrato."""

    def fetch(self, **params):
        """Retorna payload incompleto para exercitar quarentena."""
        return b'{"hourly":{"time":["2024-01-01T00:00"]}}', {"status": 200}


def test_bad_payload_preserved_quarantined_and_manifest_failed(tmp_path: Path) -> None:
    """Mantém raw, quarentena com referência e estado failed após contrato inválido."""
    location = Location("x", "X", 0, 0, "UTC")
    store = BatchManifest(tmp_path / "state" / "batches.json")
    with pytest.raises(ContractError, match="quarentena"):
        download_weather(
            location,
            "2024-01-01",
            "2024-01-01",
            ["precipitation"],
            tmp_path / "raw",
            InvalidClient(),
            manifest=store,
        )
    entry = store.entries()[0]
    assert entry["status"] == "failed"
    assert Path(entry["raw_path"]).exists()
    quarantine = json.loads(Path(entry["quarantine_path"]).read_text())
    assert quarantine["raw_path"] == entry["raw_path"]


def test_invalid_json_body_is_kept_and_quarantined(tmp_path: Path) -> None:
    """Preserva bytes de JSON malformado e registra quarentena referenciável."""

    class BrokenJsonClient:
        """Simula corpo inválido recebido com HTTP 200."""

        def fetch(self, **params):
            """Lança erro de origem com bytes recebidos anexados."""
            from climatewatch.infrastructure.weather_http import WeatherSourceError

            raise WeatherSourceError("resposta JSON inválida", 200, body=b"{")

    location = Location("x", "X", 0, 0, "UTC")
    store = BatchManifest(tmp_path / "state" / "batches.json")
    with pytest.raises(Exception, match="resposta JSON inválida"):
        download_weather(
            location,
            "2024-01-01",
            "2024-01-01",
            ["precipitation"],
            tmp_path / "raw",
            BrokenJsonClient(),
            manifest=store,
        )
    entry = store.entries()[0]
    assert Path(entry["raw_path"]).read_bytes() == b"{"
    assert Path(entry["quarantine_path"]).exists()
