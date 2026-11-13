"""Adapter HTTP simples sem dependências externas."""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class WeatherSourceError(RuntimeError):
    """Falha HTTP que preserva status e cabeçalho para política de retry."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        retry_after: float | None = None,
        body: bytes | None = None,
    ) -> None:
        """Guarda metadados de retry quando a origem os fornece."""
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after
        self.body = body


class WeatherHttpClient:
    """Cliente Open-Meteo histórico com timeout configurável."""

    endpoint = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(
        self, timeout_seconds: float = 15.0, max_response_bytes: int = 10 * 1024 * 1024
    ) -> None:
        """Define tempo máximo de espera por resposta."""
        if timeout_seconds <= 0 or max_response_bytes < 1:
            raise ValueError("timeout e limite de bytes precisam ser positivos")
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes

    def fetch(
        self,
        *,
        latitude: float,
        longitude: float,
        start: str,
        end: str,
        variables: list[str],
        timezone_name: str,
    ) -> tuple[bytes, dict[str, Any]]:
        """Busca payload histórico e retorna bytes íntegros e metadados seguros."""
        query = urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start,
                "end_date": end,
                "hourly": ",".join(variables),
                "timezone": timezone_name,
            }
        )
        request = urllib.request.Request(
            f"{self.endpoint}?{query}", headers={"User-Agent": "ClimateWatch/0.1"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > self.max_response_bytes:
                    raise WeatherSourceError("resposta excede limite de bytes", response.status)
                body = response.read(self.max_response_bytes + 1)
                if len(body) > self.max_response_bytes:
                    raise WeatherSourceError("resposta excede limite de bytes", response.status)
                if response.status != 200:
                    raise WeatherSourceError(f"origem retornou HTTP {response.status}")
                try:
                    payload = json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    raise WeatherSourceError(
                        "resposta JSON inválida", response.status, body=body
                    ) from exc
                if not isinstance(payload, dict):
                    raise WeatherSourceError(
                        "resposta JSON deve ser objeto", response.status, body=body
                    )
                return body, {"status": response.status, "url": request.full_url}
        except urllib.error.HTTPError as exc:
            retry_after = _retry_after_seconds(
                exc.headers.get("Retry-After") if exc.headers else None
            )
            raise WeatherSourceError(
                f"origem retornou HTTP {exc.code}", exc.code, retry_after
            ) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise WeatherSourceError(f"falha consultando origem climática: {exc}") from exc


def _retry_after_seconds(value: str | None) -> float | None:
    """Interpreta Retry-After como segundos ou data HTTP."""
    if value is None:
        return None
    from datetime import datetime, timezone
    from email.utils import parsedate_to_datetime

    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            return max(0.0, (date - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None
