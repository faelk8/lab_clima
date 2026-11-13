"""Reconciliação e replay de lotes interrompidos ou falhos."""

from pathlib import Path
from typing import Any, Callable

from climatewatch.domain.weather import Location
from climatewatch.infrastructure.batch_manifest import BatchManifest


def resume_incomplete(
    manifest: BatchManifest,
    locations: dict[str, Location],
    output: Path,
    download: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
    """Reexecuta lotes failed/running usando os mesmos parâmetros estáveis."""
    results = []
    for entry in manifest.entries({"failed", "running"}):
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
                manifest=manifest,
            )
        )
    return results
