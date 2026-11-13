"""Testes do adapter HTTP com transporte substituído."""

import json
from unittest.mock import patch

import pytest

from climatewatch.infrastructure.http_policy import CachedWeatherClient, ResponseBudgetExceeded
from climatewatch.infrastructure.weather_http import WeatherHttpClient, WeatherSourceError


class Response:
    """Resposta HTTP mínima para mock."""

    status = 200
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, size=-1):
        body = json.dumps({"hourly": {"time": []}}).encode()
        return body if size < 0 else body[:size]


def test_http_builds_query_and_returns_bytes() -> None:
    """Confere URL parametrizada e bytes preservados."""
    with patch("urllib.request.urlopen", return_value=Response()) as open_url:
        body, metadata = WeatherHttpClient().fetch(
            latitude=1,
            longitude=2,
            start="2024-01-01",
            end="2024-01-01",
            variables=["precipitation"],
            timezone_name="UTC",
        )
    assert json.loads(body) == {"hourly": {"time": []}}
    assert metadata["status"] == 200
    assert "latitude=1" in open_url.call_args.args[0].full_url


def test_http_error_is_translated() -> None:
    """Traduz HTTP 404 para erro de origem identificável."""
    from urllib.error import HTTPError

    import pytest

    from climatewatch.infrastructure.weather_http import WeatherSourceError

    error = HTTPError("https://example.invalid", 404, "not found", {}, None)
    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(WeatherSourceError, match="HTTP 404"):
            WeatherHttpClient().fetch(
                latitude=1,
                longitude=2,
                start="2024-01-01",
                end="2024-01-01",
                variables=["precipitation"],
                timezone_name="UTC",
            )


def test_timeout_is_translated() -> None:
    """Converte timeout em falha explícita de origem."""
    import pytest

    from climatewatch.infrastructure.weather_http import WeatherSourceError

    with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
        with pytest.raises(WeatherSourceError, match="falha consultando"):
            WeatherHttpClient().fetch(
                latitude=1,
                longitude=2,
                start="2024-01-01",
                end="2024-01-01",
                variables=["precipitation"],
                timezone_name="UTC",
            )


def test_invalid_json_is_translated() -> None:
    """Rejeita JSON de resposta malformado."""
    import pytest

    from climatewatch.infrastructure.weather_http import WeatherSourceError

    class InvalidResponse(Response):
        """Resposta HTTP com corpo malformado."""

        def read(self, size: int = -1) -> bytes:
            """Retorna bytes JSON inválidos para o caso de falha."""
            body = b"{"
            return body if size < 0 else body[:size]

    with patch("urllib.request.urlopen", return_value=InvalidResponse()):
        with pytest.raises(WeatherSourceError, match="resposta JSON inválida"):
            WeatherHttpClient().fetch(
                latitude=1,
                longitude=2,
                start="2024-01-01",
                end="2024-01-01",
                variables=["precipitation"],
                timezone_name="UTC",
            )


def test_invalid_utf8_preserves_response_body() -> None:
    """Falha de decoding UTF-8 mantém os bytes recebidos no erro de origem."""
    import pytest

    from climatewatch.infrastructure.weather_http import WeatherSourceError

    class InvalidUtf8Response(Response):
        def read(self, size: int = -1) -> bytes:
            body = b"\xff"
            return body if size < 0 else body[:size]

    with patch("urllib.request.urlopen", return_value=InvalidUtf8Response()):
        with pytest.raises(WeatherSourceError, match="resposta JSON inválida") as caught:
            WeatherHttpClient().fetch(
                latitude=1,
                longitude=2,
                start="2024-01-01",
                end="2024-01-01",
                variables=["precipitation"],
                timezone_name="UTC",
            )
    assert caught.value.body == b"\xff"


def test_policy_passes_remaining_byte_budget_to_http_reader(tmp_path) -> None:
    """O transporte lê no máximo o saldo mais um byte para detectar excesso."""

    class SizedResponse:
        status = 200
        headers = {}

        def __init__(self, body: bytes) -> None:
            self.body = body
            self.read_sizes = []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, size=-1):
            self.read_sizes.append(size)
            return self.body if size < 0 else self.body[:size]

    first = SizedResponse(b'{"a":1}')
    oversized = SizedResponse(b"x" * 1014)
    with patch("urllib.request.urlopen", side_effect=[first, oversized]) as open_url:
        policy = CachedWeatherClient(
            WeatherHttpClient(max_response_bytes=1024),
            tmp_path,
            max_response_bytes=8,
            max_total_bytes=10,
            max_attempts=1,
        )
        common_params = {
            "latitude": 1,
            "longitude": 2,
            "end": "2024-01-01",
            "variables": ["precipitation"],
            "timezone_name": "UTC",
        }
        policy.fetch(start="2024-01-01", **common_params)
        with pytest.raises(WeatherSourceError, match="limite de bytes"):
            policy.fetch(start="2024-01-02", **common_params)

        assert first.read_sizes == [9]
        assert oversized.read_sizes == [4]
        assert policy.bytes_downloaded == 11
        with pytest.raises(ResponseBudgetExceeded):
            policy.fetch(start="2024-01-03", **common_params)
        assert open_url.call_count == 2


def test_http_date_retry_after_is_parsed() -> None:
    """Lê Retry-After em formato de data HTTP."""
    from datetime import datetime, timedelta, timezone
    from email.utils import format_datetime
    from urllib.error import HTTPError

    import pytest

    from climatewatch.infrastructure.weather_http import WeatherSourceError

    future = datetime.now(timezone.utc) + timedelta(seconds=6)
    error = HTTPError(
        "https://example.invalid",
        429,
        "rate limited",
        {"Retry-After": format_datetime(future, usegmt=True)},
        None,
    )
    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(WeatherSourceError) as caught:
            WeatherHttpClient().fetch(
                latitude=1,
                longitude=2,
                start="2024-01-01",
                end="2024-01-01",
                variables=["precipitation"],
                timezone_name="UTC",
            )
    assert caught.value.retry_after is not None
    assert 0 < caught.value.retry_after <= 6
