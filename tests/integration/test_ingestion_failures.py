"""Falhas controladas do downloader e preservação de lotes."""

from pathlib import Path

import pytest

from climatewatch.application.download import download_weather
from climatewatch.domain.weather import Location
from climatewatch.infrastructure.batch_manifest import BatchManifest
from climatewatch.infrastructure.weather_http import WeatherSourceError


class OutageClient:
    """Cliente que falha para representar uma interrupção externa."""

    def fetch(self, **params):
        """Dispara timeout de origem."""
        raise WeatherSourceError("timeout de teste")


class GoodClient:
    """Cliente de fixture que retorna resposta contratual válida."""

    def fetch(self, **params):
        """Devolve uma hora e metadata sintéticas."""
        return b'{"hourly":{"time":["2024-01-01T00:00"],"precipitation":[1.0]}}', {"status": 200}


def test_failed_request_is_recorded_then_resumed(tmp_path: Path) -> None:
    """Falha fica no manifesto e o mesmo lote pode ser retomado."""
    location = Location("x", "X", 0, 0, "UTC")
    manifest = BatchManifest(tmp_path / "state" / "batches.json")
    with pytest.raises(WeatherSourceError):
        download_weather(
            location,
            "2024-01-01",
            "2024-01-01",
            ["precipitation"],
            tmp_path / "raw",
            OutageClient(),
            manifest=manifest,
        )
    assert manifest.entries({"failed"})[0]["error"] == "timeout de teste"
    result = download_weather(
        location,
        "2024-01-01",
        "2024-01-01",
        ["precipitation"],
        tmp_path / "raw",
        GoodClient(),
        manifest=manifest,
    )
    assert result["status"] == "succeeded"
    assert manifest.entries()[0]["attempts"] == 2


def test_failure_in_new_batch_preserves_previous_raw(tmp_path: Path) -> None:
    """Erro de armazenamento em lote novo não remove arquivo já concluído."""
    location = Location("x", "X", 0, 0, "UTC")
    manifest = BatchManifest(tmp_path / "state" / "batches.json")
    first = download_weather(
        location,
        "2024-01-01",
        "2024-01-01",
        ["precipitation"],
        tmp_path / "raw",
        GoodClient(),
        manifest=manifest,
    )
    raw_path = Path(first["raw_path"])
    original = raw_path.read_bytes()
    with pytest.raises(WeatherSourceError):
        download_weather(
            location,
            "2024-01-02",
            "2024-01-02",
            ["precipitation"],
            tmp_path / "raw",
            OutageClient(),
            manifest=manifest,
        )
    assert raw_path.read_bytes() == original
    assert len(manifest.entries({"succeeded"})) == 1
    assert len(manifest.entries({"failed"})) == 1
