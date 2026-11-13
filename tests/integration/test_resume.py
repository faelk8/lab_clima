"""Teste de retomada e quarentena sem chamada de rede."""

import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from climatewatch.application.download import download_weather
from climatewatch.application.resume import resume_incomplete
from climatewatch.domain.weather import ContractError, Location
from climatewatch.infrastructure.batch_manifest import BatchManifest
from climatewatch.infrastructure.weather_http import WeatherHttpClient, WeatherSourceError


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


def test_invalid_utf8_body_is_preserved_and_quarantined(tmp_path: Path) -> None:
    """Bytes UTF-8 inválidos recebidos da origem permanecem auditáveis."""

    class InvalidUtf8Response:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, size=-1):
            return b"\xff"

    manifest = BatchManifest(tmp_path / "state" / "batches.json")
    with patch("urllib.request.urlopen", return_value=InvalidUtf8Response()):
        with pytest.raises(WeatherSourceError, match="resposta JSON inválida"):
            download_weather(
                Location("x", "X", 0, 0, "UTC"),
                "2024-01-01",
                "2024-01-01",
                ["precipitation"],
                tmp_path / "raw",
                WeatherHttpClient(),
                manifest=manifest,
            )

    entry = manifest.entries()[0]
    assert entry["status"] == "failed"
    assert Path(entry["raw_path"]).read_bytes() == b"\xff"
    quarantine = json.loads(Path(entry["quarantine_path"]).read_text())
    assert quarantine["sha256"] == entry["sha256"]
    assert "JSON inválida" in quarantine["reason"]


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

    def offline_download(location, start, end, variables, output, *, client, manifest):
        resumed_locations.append(location)
        return download_weather(
            location,
            start,
            end,
            variables,
            output,
            client,
            manifest=manifest,
        )

    results = resume_incomplete(
        manifest,
        changed_catalog,
        tmp_path / "raw",
        offline_download,
        client=GoodClient(),
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

    def offline_download(location, start, end, variables, output, *, client, manifest):
        locations.append(location)
        return download_weather(location, start, end, variables, output, client, manifest=manifest)

    results = resume_incomplete(
        manifest, {}, tmp_path / "raw", offline_download, client=GoodClient()
    )

    assert results[0]["batch_id"] == batch_id
    assert locations[0].location_id == "removed-location"
    assert locations[0].latitude == 1.0
    assert manifest.entries()[0]["status"] == "succeeded"


def test_resume_shares_request_and_retry_budget_across_batches(tmp_path: Path) -> None:
    """Uma retomada de 31 lotes respeita um orçamento global de 30 tentativas."""

    class RetryOnceClient:
        def __init__(self) -> None:
            self.calls = 0
            self.failed_once = False

        def fetch(self, **params):
            self.calls += 1
            if not self.failed_once:
                self.failed_once = True
                raise WeatherSourceError("falha transitória", 503)
            payload = {
                "hourly": {
                    "time": [f"{params['start']}T00:00"],
                    "precipitation": [1.0],
                }
            }
            return json.dumps(payload).encode(), {"status": 200}

    manifest = BatchManifest(tmp_path / "state" / "batches.json")
    location = Location("x", "X", 0.0, 0.0, "UTC")
    for offset in range(31):
        day = (date(2024, 1, 1) + timedelta(days=offset)).isoformat()
        params = {
            "location_id": "x",
            "latitude": 0.0,
            "longitude": 0.0,
            "start": day,
            "end": day,
            "variables": ["precipitation"],
            "timezone_name": "UTC",
        }
        batch_id, _ = manifest.begin(params)
        manifest.fail(batch_id, "interrompido")

    transport = RetryOnceClient()
    results = resume_incomplete(
        manifest,
        {"x": location},
        tmp_path / "raw",
        download_weather,
        client=transport,
        cache_dir=tmp_path / "cache",
        max_requests=30,
    )

    assert transport.calls == 30
    assert len(results) == 29
    assert len(manifest.entries({"succeeded"})) == 29
    assert len(manifest.entries({"failed", "running"})) == 2
