"""Testes determinísticos de cache e retry HTTP."""

from pathlib import Path

import pytest

from climatewatch.infrastructure.http_policy import CachedWeatherClient, RequestBudgetExceeded
from climatewatch.infrastructure.weather_http import WeatherSourceError


class FakeClient:
    """Cliente configurável para simular sucessos e erros HTTP."""

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def fetch(self, **params):
        """Retorna o próximo item configurado."""
        self.calls += 1
        item = next(self.responses)
        if isinstance(item, Exception):
            raise item
        return item


def params():
    """Parâmetros normalizados de exemplo."""
    return {
        "latitude": 1,
        "longitude": 2,
        "start": "2024-01-01",
        "end": "2024-01-01",
        "variables": ["precipitation"],
        "timezone_name": "UTC",
    }


def test_cache_hit_and_expiry(tmp_path: Path) -> None:
    """Reusa cache até TTL e volta à rede após expiração."""
    now = [10.0]
    fake = FakeClient([(b"first", {"status": 200}), (b"second", {"status": 200})])
    policy = CachedWeatherClient(fake, tmp_path, ttl_seconds=5, clock=lambda: now[0])
    assert policy.fetch(**params())[0] == b"first"
    assert policy.fetch(**params())[0] == b"first"
    assert fake.calls == 1
    now[0] = 16.0
    assert policy.fetch(**params())[0] == b"second"
    assert fake.calls == 2


def test_retry_after_429_then_success(tmp_path: Path) -> None:
    """Retry 429 respeita Retry-After e depois armazena resposta."""
    fake = FakeClient([WeatherSourceError("rate limited", 429, 3.5), (b"ok", {"status": 200})])
    waits = []
    policy = CachedWeatherClient(fake, tmp_path, sleeper=waits.append)
    assert policy.fetch(**params())[0] == b"ok"
    assert waits == [3.5]


def test_server_error_retries_but_client_error_does_not(tmp_path: Path) -> None:
    """Repete 5xx e interrompe imediatamente 4xx não recuperável."""
    server = FakeClient([WeatherSourceError("server", 503), (b"ok", {"status": 200})])
    policy = CachedWeatherClient(server, tmp_path, sleeper=lambda _: None)
    assert policy.fetch(**params())[0] == b"ok"
    assert server.calls == 2
    client = FakeClient([WeatherSourceError("bad request", 400)])
    with pytest.raises(WeatherSourceError):
        CachedWeatherClient(client, tmp_path / "other").fetch(**params())
    assert client.calls == 1


def test_request_budget_blocks_extra_attempts(tmp_path: Path) -> None:
    """Limita chamadas externas ao teto configurado."""
    fake = FakeClient([WeatherSourceError("timeout"), WeatherSourceError("timeout")])
    policy = CachedWeatherClient(
        fake, tmp_path, max_requests=1, max_attempts=3, sleeper=lambda _: None
    )
    with pytest.raises(RequestBudgetExceeded):
        policy.fetch(**params())
    assert fake.calls == 1
    with pytest.raises(RequestBudgetExceeded):
        policy.fetch(**params())


def test_response_and_execution_byte_budgets(tmp_path: Path) -> None:
    """Bloqueia respostas acima do limite individual e agregado."""
    from climatewatch.infrastructure.http_policy import ResponseBudgetExceeded

    oversized = FakeClient([(b"123", {"status": 200})])
    one = CachedWeatherClient(oversized, tmp_path / "one", max_response_bytes=2)
    with pytest.raises(ResponseBudgetExceeded, match="resposta excede"):
        one.fetch(**params())
    small = FakeClient([(b"123", {"status": 200}), (b"45", {"status": 200})])
    two = CachedWeatherClient(small, tmp_path / "two", max_response_bytes=4, max_total_bytes=4)
    two.fetch(**params())
    with pytest.raises(ResponseBudgetExceeded, match="execução excede"):
        two.fetch(**{**params(), "start": "2024-01-02"})
