"""Caso de uso de coleta histórica transacional por arquivo/manifesto."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from climatewatch.domain.weather import ContractError, Location, parse_hourly_payload
from climatewatch.infrastructure.batch_manifest import BatchManifest
from climatewatch.infrastructure.http_policy import CachedWeatherClient
from climatewatch.infrastructure.quarantine import QuarantineStore
from climatewatch.infrastructure.raw_store import RawStore
from climatewatch.infrastructure.weather_http import WeatherHttpClient

ALLOWED_VARIABLES = {"temperature_2m", "precipitation", "relative_humidity_2m", "wind_speed_10m"}


def download_weather(
    location: Location,
    start: str,
    end: str,
    variables: list[str],
    output: Path,
    client: WeatherHttpClient | CachedWeatherClient | None = None,
    *,
    cache_dir: Path | None = None,
    manifest: BatchManifest | None = None,
    quarantine_dir: Path | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Valida, coleta, verifica contrato, preserva raw e finaliza estado do lote."""
    start_day, end_day = date.fromisoformat(start), date.fromisoformat(end)
    if start_day > end_day:
        raise ValueError("start deve ser anterior ou igual a end")
    if not variables or set(variables) - ALLOWED_VARIABLES:
        raise ValueError("variáveis vazias ou não suportadas")
    params: dict[str, Any] = {
        "location_id": location.location_id,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "start": start,
        "end": end,
        "variables": sorted(set(variables)),
        "timezone_name": location.timezone_name,
    }
    batch_manifest = manifest or BatchManifest(output.parent / "state" / "batches.json")
    http = (
        client
        if isinstance(client, CachedWeatherClient)
        else CachedWeatherClient(
            client or WeatherHttpClient(), cache_dir or output.parent / "cache"
        )
    )
    with batch_manifest.claim(params, force=force_refresh) as (batch_id, entry):
        if entry["status"] == "succeeded":
            return {
                "batch_id": batch_id,
                "status": "succeeded",
                "raw_path": entry["raw_path"],
                "sha256": entry["sha256"],
                "byte_count": entry.get("byte_count", Path(entry["raw_path"]).stat().st_size),
                "batch_replay": "hit",
            }
        try:
            try:
                body, response = http.fetch(
                    latitude=location.latitude,
                    longitude=location.longitude,
                    start=start,
                    end=end,
                    variables=variables,
                    timezone_name=location.timezone_name,
                    bypass_cache=force_refresh or entry.get("force_refresh_pending", False),
                )
            except Exception as source_error:
                invalid_body = getattr(source_error, "body", None)
                if invalid_body is not None:
                    raw = RawStore(output).save(
                        invalid_body,
                        {
                            "source": "open-meteo",
                            **params,
                            "batch_id": batch_id,
                            "validation_error": str(source_error),
                        },
                    )
                    quarantine_path = QuarantineStore(
                        quarantine_dir or output.parent / "quarantine"
                    ).save(raw, str(source_error))
                    batch_manifest.fail(batch_id, str(source_error), str(quarantine_path), raw)
                raise
            raw = RawStore(output).save(
                body, {"source": "open-meteo", **params, "batch_id": batch_id, **response}
            )
            try:
                payload = json.loads(body)
                parse_hourly_payload(payload, location, requested_variables=set(variables))
            except (json.JSONDecodeError, ContractError, TypeError, ValueError) as exc:
                quarantine = QuarantineStore(quarantine_dir or output.parent / "quarantine")
                quarantine_path = quarantine.save(raw, str(exc))
                batch_manifest.fail(batch_id, str(exc), str(quarantine_path), raw)
                raise ContractError(f"payload preservado em quarentena: {exc}") from exc
            batch_manifest.succeed(batch_id, raw)
            return {
                **raw,
                "batch_id": batch_id,
                "status": "succeeded",
                "request_cache": response.get("cache"),
            }
        except Exception as exc:
            current = next(
                (item for item in batch_manifest.entries() if item["batch_id"] == batch_id), None
            )
            if current and current["status"] == "running":
                batch_manifest.fail(batch_id, str(exc))
            raise
