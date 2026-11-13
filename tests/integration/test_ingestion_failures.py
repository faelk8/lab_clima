"""Falhas controladas do downloader e preservação de lotes."""

import json
import os
from pathlib import Path

import pytest

from climatewatch.application.download import download_weather
from climatewatch.domain.weather import Location
from climatewatch.infrastructure.batch_manifest import BatchManifest
from climatewatch.infrastructure.http_policy import CachedWeatherClient
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
        payload = {
            "hourly": {
                "time": [f"{params['start']}T00:00"],
                "precipitation": [1.0],
            }
        }
        return json.dumps(payload).encode(), {"status": 200}


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


@pytest.mark.parametrize("failure_point", ["raw", "sidecar", "manifest"])
def test_storage_failures_preserve_previous_raw_and_can_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_point: str
) -> None:
    """Falha em cada persistência não corrompe lotes prévios e permite replay."""
    location = Location("x", "X", 0, 0, "UTC")
    manifest_path = tmp_path / "state" / "batches.json"
    manifest = BatchManifest(manifest_path)
    raw_root = tmp_path / "raw"
    first = download_weather(
        location,
        "2024-01-01",
        "2024-01-01",
        ["precipitation"],
        raw_root,
        GoodClient(),
        manifest=manifest,
    )
    raw_path = Path(first["raw_path"])
    original = raw_path.read_bytes()
    second_params = {
        "location_id": "x",
        "latitude": 0,
        "longitude": 0,
        "start": "2024-01-02",
        "end": "2024-01-02",
        "variables": ["precipitation"],
        "timezone_name": "UTC",
    }
    second_batch_id = BatchManifest.batch_id(second_params)
    actual_replace = os.replace
    raised = False

    def fail_selected_replace(source, destination):
        nonlocal raised
        destination_path = Path(destination)
        should_fail = False
        if not raised and failure_point == "raw":
            in_raw = destination_path.is_relative_to(raw_root)
            is_sidecar = destination_path.name.endswith(".manifest.json")
            should_fail = in_raw and not is_sidecar
        elif not raised and failure_point == "sidecar":
            in_raw = destination_path.is_relative_to(raw_root)
            is_sidecar = destination_path.name.endswith(".manifest.json")
            should_fail = in_raw and is_sidecar
        elif not raised and failure_point == "manifest" and destination_path == manifest_path:
            pending = json.loads(Path(source).read_text(encoding="utf-8"))
            should_fail = pending[second_batch_id]["status"] == "succeeded"
        if should_fail:
            raised = True
            raise OSError(f"simulated {failure_point} write failure")
        actual_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_selected_replace)
    with pytest.raises(OSError, match="simulated"):
        download_weather(
            location,
            "2024-01-02",
            "2024-01-02",
            ["precipitation"],
            raw_root,
            GoodClient(),
            manifest=manifest,
        )
    assert raised
    failed = [
        entry for entry in manifest.entries({"failed"}) if entry["batch_id"] == second_batch_id
    ]
    assert len(failed) == 1
    assert failed[0]["status"] == "failed"
    assert raw_path.read_bytes() == original
    monkeypatch.undo()
    retried = download_weather(
        location,
        "2024-01-02",
        "2024-01-02",
        ["precipitation"],
        raw_root,
        GoodClient(),
        manifest=manifest,
    )
    assert retried["status"] == "succeeded"
    assert len(manifest.entries({"succeeded"})) == 2
    assert not manifest.entries({"failed", "running"})


def test_backfill_uses_one_retry_policy_per_execution(tmp_path: Path) -> None:
    """Erro 503 usa três tentativas, sem multiplicação por decorator aninhado."""

    class PersistentServerError:
        def __init__(self) -> None:
            self.calls = 0

        def fetch(self, **params):
            self.calls += 1
            raise WeatherSourceError("servidor indisponível", 503)

    transport = PersistentServerError()
    policy = CachedWeatherClient(transport, tmp_path / "cache", sleeper=lambda _: None)
    with pytest.raises(WeatherSourceError, match="servidor indisponível"):
        download_weather(
            Location("x", "X", 0, 0, "UTC"),
            "2024-01-01",
            "2024-01-01",
            ["precipitation"],
            tmp_path / "raw",
            policy,
            manifest=BatchManifest(tmp_path / "state" / "batches.json"),
        )
    assert transport.calls == 3
    assert policy.requests_made == 3
