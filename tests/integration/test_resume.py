"""Teste de retomada e quarentena sem chamada de rede."""

import json
from pathlib import Path

import pytest

from climatewatch.application.download import download_weather
from climatewatch.application.resume import resume_incomplete
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


def test_resume_uses_custom_manifest_and_persisted_location(tmp_path: Path) -> None:
    """Retoma no manifesto original e mantém coordenadas/fuso persistidos."""
    manifest = BatchManifest(tmp_path / "custom" / "batches.json")
    params = {
        "location_id": "x",
        "latitude": 0.0,
        "longitude": 2.0,
        "start": "2024-01-01",
        "end": "2024-01-01",
        "variables": ["precipitation"],
        "timezone_name": "UTC",
    }
    batch_id, _ = manifest.begin(params)
    manifest.fail(batch_id, "interrompido")
    changed_catalog = {"x": Location("x", "Atualizado", 10.0, 20.0, "Asia/Tokyo")}
    resumed_locations = []

    class GoodClient:
        def fetch(self, **kwargs):
            return b'{"hourly":{"time":["2024-01-01T00:00"],"precipitation":[1]}}', {"status": 200}

    def offline_download(location, start, end, variables, output, *, manifest):
        resumed_locations.append(location)
        return download_weather(
            location,
            start,
            end,
            variables,
            output,
            GoodClient(),
            manifest=manifest,
        )

    results = resume_incomplete(
        manifest,
        changed_catalog,
        tmp_path / "raw",
        offline_download,
    )

    entries = manifest.entries()
    assert len(results) == 1
    assert results[0]["batch_id"] == batch_id
    assert entries[0]["batch_id"] == batch_id
    assert entries[0]["status"] == "succeeded"
    assert entries[0]["params"] == params
    assert resumed_locations[0].latitude == 0.0
    assert resumed_locations[0].longitude == 2.0
    assert resumed_locations[0].timezone_name == "UTC"
    assert not (tmp_path / "state" / "batches.json").exists()


def test_resume_does_not_require_location_in_current_catalog(tmp_path: Path) -> None:
    """Coordenadas persistidas permitem retomar mesmo sem entrada no catálogo atual."""
    manifest = BatchManifest(tmp_path / "custom" / "batches.json")
    params = {
        "location_id": "removed-location",
        "latitude": 1.0,
        "longitude": 2.0,
        "start": "2024-01-01",
        "end": "2024-01-01",
        "variables": ["precipitation"],
        "timezone_name": "UTC",
    }
    batch_id, _ = manifest.begin(params)
    manifest.fail(batch_id, "interrompido")
    locations = []

    class GoodClient:
        def fetch(self, **kwargs):
            return b'{"hourly":{"time":["2024-01-01T00:00"],"precipitation":[1]}}', {"status": 200}

    def offline_download(location, start, end, variables, output, *, manifest):
        locations.append(location)
        return download_weather(
            location, start, end, variables, output, GoodClient(), manifest=manifest
        )

    results = resume_incomplete(manifest, {}, tmp_path / "raw", offline_download)

    assert results[0]["batch_id"] == batch_id
    assert locations[0].location_id == "removed-location"
    assert locations[0].latitude == 1.0
    assert manifest.entries()[0]["status"] == "succeeded"
