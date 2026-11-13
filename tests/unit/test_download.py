"""Testes do caso de uso sem serviço externo."""

from pathlib import Path

import pytest

from climatewatch.application.download import download_weather
from climatewatch.domain.weather import Location


class Client:
    """Cliente falso para execução inteiramente offline."""

    def fetch(self, **kwargs):
        """Devolve payload e metadados determinísticos."""
        return b'{"hourly":{}}', {"status": 200, "url": "fixture://weather"}


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
