"""Testes do adapter HTTP com transporte substituído."""

import json
from unittest.mock import patch

from climatewatch.infrastructure.weather_http import WeatherHttpClient


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
