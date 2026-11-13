"""Adapter HTTP simples sem dependências externas."""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class WeatherSourceError(RuntimeError):
    """Falha explícita ao consultar a origem climática."""


class WeatherHttpClient:
    """Cliente Open-Meteo histórico com timeout configurável."""

    endpoint = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        """Define tempo máximo de espera por resposta."""
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds deve ser positivo")
        self.timeout_seconds = timeout_seconds

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
                body = response.read()
                if response.status != 200:
                    raise WeatherSourceError(f"origem retornou HTTP {response.status}")
                payload = json.loads(body)
                if not isinstance(payload, dict):
                    raise WeatherSourceError("resposta JSON deve ser objeto")
                return body, {"status": response.status, "url": request.full_url}
        except urllib.error.HTTPError as exc:
            raise WeatherSourceError(f"origem retornou HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise WeatherSourceError(f"falha consultando origem climática: {exc}") from exc
