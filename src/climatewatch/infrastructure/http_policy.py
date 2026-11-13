"""Cache TTL, retry de falhas temporárias e orçamento de requests."""

import hashlib
import json
import os
import tempfile
import time
import urllib.error
from pathlib import Path
from typing import Any, Callable

from climatewatch.infrastructure.weather_http import WeatherHttpClient, WeatherSourceError


class RequestBudgetExceeded(RuntimeError):
    """Orçamento de chamadas HTTP excedido."""


class ResponseBudgetExceeded(RuntimeError):
    """Orçamento de bytes recebidos excedido."""


class CachedWeatherClient:
    """Decorator do cliente HTTP com cache persistente e retry limitado."""

    def __init__(
        self,
        client: WeatherHttpClient,
        cache_dir: Path,
        *,
        ttl_seconds: int = 86400,
        max_requests: int = 30,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_response_bytes: int = 10 * 1024 * 1024,
        max_total_bytes: int = 100 * 1024 * 1024,
        clock: Callable[[], float] = time.time,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        """Configura limites e dependências de tempo substituíveis em teste."""
        if (
            ttl_seconds < 0
            or max_requests < 1
            or max_attempts < 1
            or base_delay < 0
            or max_response_bytes < 1
            or max_total_bytes < 1
        ):
            raise ValueError("parâmetros da política inválidos")
        self.client = client
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.max_requests = max_requests
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_response_bytes = max_response_bytes
        self.max_total_bytes = max_total_bytes
        self.bytes_downloaded = 0
        self.clock = clock
        self.sleeper = sleeper
        self.requests_made = 0

    def fetch(self, *, bypass_cache: bool = False, **params: Any) -> tuple[bytes, dict[str, Any]]:
        """Usa cache válido; em miss, faz retry para timeout, 429 e 5xx."""
        canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
        key = hashlib.sha256(canonical.encode()).hexdigest()
        cache_path = self.cache_dir / f"{key}.json"
        if cache_path.exists() and not bypass_cache:
            try:
                cache = json.loads(cache_path.read_text(encoding="utf-8"))
                if self.clock() - cache["stored_at"] <= self.ttl_seconds:
                    return bytes.fromhex(cache["body_hex"]), {**cache["metadata"], "cache": "hit"}
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                cache_path.unlink(missing_ok=True)
        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            remaining_bytes = self.max_total_bytes - self.bytes_downloaded
            if remaining_bytes <= 0:
                raise ResponseBudgetExceeded(
                    f"execução excede {self.max_total_bytes} bytes recebidos"
                )
            if self.requests_made >= self.max_requests:
                raise RequestBudgetExceeded(f"limite de {self.max_requests} requests atingido")
            self.requests_made += 1
            response_limit = min(self.max_response_bytes, remaining_bytes)
            try:
                body, metadata = self.client.fetch(**params, max_response_bytes=response_limit)
                self.bytes_downloaded += len(body)
                if len(body) > self.max_response_bytes:
                    raise ResponseBudgetExceeded(f"resposta excede {self.max_response_bytes} bytes")
                if self.bytes_downloaded > self.max_total_bytes:
                    raise ResponseBudgetExceeded(
                        f"execução excede {self.max_total_bytes} bytes recebidos"
                    )
                self._write_cache(cache_path, body, metadata)
                return body, {**metadata, "cache": "miss"}
            except (WeatherSourceError, urllib.error.URLError, TimeoutError) as exc:
                error_body = getattr(exc, "body", None)
                if error_body is not None:
                    self.bytes_downloaded += len(error_body)
                last_error = exc
                status = getattr(exc, "status_code", None)
                if status is not None and status != 429 and status < 500:
                    raise
                if attempt + 1 < self.max_attempts:
                    delay = getattr(exc, "retry_after", None)
                    self.sleeper(delay if delay is not None else self.base_delay * 2**attempt)
        if last_error:
            raise last_error
        raise RuntimeError("retry encerrou sem resposta")

    def _write_cache(self, path: Path, body: bytes, metadata: dict[str, Any]) -> None:
        """Escreve cache via arquivo temporário e rename atômico."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps({"stored_at": self.clock(), "body_hex": body.hex(), "metadata": metadata})
        fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".cache-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
