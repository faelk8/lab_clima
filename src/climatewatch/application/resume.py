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
        location = locations[params["location_id"]]
        results.append(
            download(location, params["start"], params["end"], params["variables"], output)
        )
    return results
