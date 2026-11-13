"""Testes do caso de uso sem serviço externo."""

import json
from pathlib import Path

import pytest

from climatewatch.application.download import download_weather
from climatewatch.domain.weather import Location
from climatewatch.infrastructure.http_policy import CachedWeatherClient


class Client:
    """Cliente falso para execução inteiramente offline."""

    def fetch(self, **kwargs):
        """Devolve payload e metadados determinísticos."""
        body = (
            '{"hourly":{"time":["' + kwargs["start"] + 'T00:00"],"precipitation":[0.0]}}'
        ).encode()
        return body, {"status": 200, "url": "fixture://weather"}


def test_download_offline_persists_raw(tmp_path: Path) -> None:
    """Confere integração do caso de uso com persistência raw."""
    location = Location("x", "X", 0, 0, "UTC")
    result = download_weather(
        location, "2024-01-01", "2024-01-01", ["precipitation"], tmp_path, Client()
    )
    assert result["source"] == "open-meteo"
    assert Path(result["raw_path"]).exists()


def test_download_rejects_bad_inputs_before_http(tmp_path: Path) -> None:
    """Rejeita parâmetros inválidos antes de chamar o adapter."""
    with pytest.raises(ValueError):
        download_weather(
            Location("x", "X", 0, 0, "UTC"),
            "2024-02-01",
            "2024-01-01",
            ["precipitation"],
            tmp_path,
            Client(),
        )


def test_repeated_batch_skips_http_and_returns_existing_raw(tmp_path: Path) -> None:
    """Lote concluído idêntico é reutilizado sem nova chamada HTTP."""

    class CountingClient(Client):
        calls = 0

        def fetch(self, **kwargs):
            self.calls += 1
            return super().fetch(**kwargs)

    client = CountingClient()
    location = Location("x", "X", 0, 0, "UTC")
    args = (location, "2024-01-01", "2024-01-01", ["precipitation"], tmp_path / "raw")
    first = download_weather(*args, client)
    second = download_weather(*args, client)
    assert first["raw_path"] == second["raw_path"]
    assert second["batch_replay"] == "hit"
    assert client.calls == 1


def test_force_refresh_preserves_new_content_version(tmp_path: Path) -> None:
    """Atualização explícita ignora cache e mantém ambos os hashes no manifesto."""

    class RevisionClient:
        def __init__(self):
            self.calls = 0

        def fetch(self, **kwargs):
            self.calls += 1
            value = float(self.calls)
            body = (
                '{"hourly":{"time":["2024-01-01T00:00"],' f'"precipitation":[{value}]}}}}'
            ).encode()
            return body, {"status": 200}

    client = RevisionClient()
    location = Location("x", "X", 0, 0, "UTC")
    args = (location, "2024-01-01", "2024-01-01", ["precipitation"], tmp_path / "raw")
    first = download_weather(*args, client)
    second = download_weather(*args, client, force_refresh=True)
    assert first["sha256"] != second["sha256"]
    assert client.calls == 2
    state = json.loads((tmp_path / "state" / "batches.json").read_text())
    versions = next(iter(state.values()))["versions"]
    assert [entry["sha256"] for entry in versions] == [first["sha256"], second["sha256"]]


def test_force_refresh_bypasses_injected_policy_cache(tmp_path: Path) -> None:
    """Refresh ignora o cache da política compartilhada pelo backfill."""

    class RevisionClient:
        def __init__(self) -> None:
            self.calls = 0

        def fetch(self, **kwargs):
            self.calls += 1
            body = json.dumps(
                {
                    "hourly": {
                        "time": ["2024-01-01T00:00"],
                        "precipitation": [float(self.calls)],
                    }
                }
            ).encode()
            return body, {"status": 200}

    transport = RevisionClient()
    policy = CachedWeatherClient(transport, tmp_path / "cache", sleeper=lambda _: None)
    location = Location("x", "X", 0, 0, "UTC")
    args = (location, "2024-01-01", "2024-01-01", ["precipitation"], tmp_path / "raw")
    first = download_weather(*args, policy)
    second = download_weather(*args, policy, force_refresh=True)
    assert first["sha256"] != second["sha256"]
    assert transport.calls == 2
    assert policy.requests_made == 2


def test_failed_force_refresh_remains_pending_until_resume_fetches_new_source(
    tmp_path: Path,
) -> None:
    """Retomada de refresh falho ignora cache antigo e preserva as duas versões."""

    class CorrectedSource:
        def __init__(self) -> None:
            self.calls = 0
            self.fail_refresh = False
            self.revision = 1

        def fetch(self, **kwargs):
            self.calls += 1
            if self.fail_refresh:
                from climatewatch.infrastructure.weather_http import WeatherSourceError

                if self.calls <= 4:
                    raise WeatherSourceError("refresh temporariamente indisponível", 503)
            body = json.dumps(
                {
                    "hourly": {
                        "time": ["2024-01-01T00:00"],
                        "precipitation": [float(self.revision)],
                    }
                }
            ).encode()
            return body, {"status": 200}

    from climatewatch.application.resume import resume_incomplete
    from climatewatch.infrastructure.batch_manifest import BatchManifest
    from climatewatch.infrastructure.weather_http import WeatherSourceError

    transport = CorrectedSource()
    policy = CachedWeatherClient(transport, tmp_path / "cache", sleeper=lambda _: None)
    manifest = BatchManifest(tmp_path / "state" / "batches.json")
    location = Location("x", "X", 0.0, 0.0, "UTC")
    args = (location, "2024-01-01", "2024-01-01", ["precipitation"], tmp_path / "raw")
    original = download_weather(*args, policy, manifest=manifest)
    transport.fail_refresh = True
    with pytest.raises(WeatherSourceError, match="temporariamente indisponível"):
        download_weather(*args, policy, manifest=manifest, force_refresh=True)
    assert manifest.entries()[0]["status"] == "failed"
    assert manifest.entries()[0]["force_refresh_pending"] is True

    transport.fail_refresh = False
    transport.revision = 2
    results = resume_incomplete(
        manifest, {"x": location}, tmp_path / "raw", download_weather, client=policy
    )

    state = manifest.entries()[0]
    assert len(results) == 1
    assert results[0]["sha256"] != original["sha256"]
    assert state["status"] == "succeeded"
    assert state["force_refresh_pending"] is False
    assert [version["sha256"] for version in state["versions"]] == [
        original["sha256"],
        results[0]["sha256"],
    ]
    assert transport.calls == 5
