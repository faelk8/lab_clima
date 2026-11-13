"""Reconciliação e replay de lotes interrompidos ou falhos."""

from pathlib import Path
from typing import Any, Callable

from climatewatch.domain.weather import Location
from climatewatch.infrastructure.batch_manifest import BatchManifest
from climatewatch.infrastructure.http_policy import CachedWeatherClient
from climatewatch.infrastructure.weather_http import WeatherHttpClient


def resume_incomplete(
    manifest: BatchManifest,
    locations: dict[str, Location],
    output: Path,
    download: Callable[..., dict[str, Any]],
    *,
    client: WeatherHttpClient | CachedWeatherClient | None = None,
    cache_dir: Path | None = None,
    max_requests: int = 30,
    max_total_bytes: int = 100 * 1024 * 1024,
) -> list[dict[str, Any]]:
    """Reexecuta lotes incompletos com uma política e orçamento compartilhados."""
    policy = (
        client
        if isinstance(client, CachedWeatherClient)
        else CachedWeatherClient(
            client or WeatherHttpClient(),
            cache_dir or output.parent / "cache",
            max_requests=max_requests,
            max_total_bytes=max_total_bytes,
        )
    )
    results = []
    for entry in manifest.entries({"failed", "running"}):
        if policy.requests_made >= policy.max_requests:
            break
        params = entry["params"]
        catalog_location = locations.get(params["location_id"])
        location = Location(
            location_id=params["location_id"],
            name=catalog_location.name if catalog_location else params["location_id"],
            latitude=params["latitude"],
            longitude=params["longitude"],
            timezone_name=params["timezone_name"],
        )
        results.append(
            download(
                location,
                params["start"],
                params["end"],
                params["variables"],
                output,
                client=policy,
                manifest=manifest,
            )
        )
    return results
