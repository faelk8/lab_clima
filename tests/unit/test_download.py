"""Testes do caso de uso sem serviço externo."""

import json
from pathlib import Path

import pytest

from climatewatch.application.download import download_weather
from climatewatch.domain.weather import Location


class Client:
    """Cliente falso para execução inteiramente offline."""

    def fetch(self, **kwargs):
        """Devolve payload e metadados determinísticos."""
        return b'{"hourly":{"time":["2024-01-01T00:00"],"precipitation":[0.0]}}', {
            "status": 200,
            "url": "fixture://weather",
        }


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
