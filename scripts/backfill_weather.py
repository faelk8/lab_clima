"""Backfill batch limitado por janelas com manifesto e relatório de cobertura."""

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from climatewatch.application.coverage import hourly_coverage
from climatewatch.application.download import download_weather
from climatewatch.application.windows import plan_windows
from climatewatch.domain.weather import Location
from climatewatch.infrastructure.http_policy import CachedWeatherClient
from climatewatch.infrastructure.weather_http import WeatherHttpClient


def load_locations(path: Path) -> dict[str, Location]:
    """Lê localidades do catálogo versionado."""
    catalog = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["location_id"]: Location(
            item["location_id"], item["name"], item["latitude"], item["longitude"], item["timezone"]
        )
        for item in catalog["locations"]
    }


def main() -> int:
    """Executa janela de localidades e grava relatório de contagens em JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--locations", default="br-sp-sao-paulo,br-pe-recife,br-am-manaus")
    parser.add_argument("--catalog", type=Path, default=Path("config/locations.json"))
    parser.add_argument("--output", type=Path, default=Path("data/raw"))
    parser.add_argument("--max-days", type=int, default=7)
    parser.add_argument("--max-requests", type=int, default=30)
    parser.add_argument("--report", type=Path, default=Path("data/state/backfill-report.json"))
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    windows = plan_windows(start, end, max_days=args.max_days, max_requests=args.max_requests)
    locations = load_locations(args.catalog)
    ids = [value.strip() for value in args.locations.split(",")]
    unknown = set(ids) - locations.keys()
    if unknown:
        parser.error(f"localidades fora do catálogo: {sorted(unknown)}")
    policy = CachedWeatherClient(
        WeatherHttpClient(), args.output.parent / "cache", max_requests=args.max_requests
    )
    rows = []
    for location_id in ids:
        location = locations[location_id]
        requests_before = policy.requests_made
        timestamps: list[str] = []
        bytes_saved = 0
        for window in windows:
            result = download_weather(
                location,
                window.start.isoformat(),
                window.end.isoformat(),
                ["temperature_2m", "precipitation", "relative_humidity_2m", "wind_speed_10m"],
                args.output,
                policy,
            )
            payload = json.loads(Path(result["raw_path"]).read_text(encoding="utf-8"))
            timestamps.extend(payload["hourly"]["time"])
            bytes_saved += result["byte_count"]
        coverage = hourly_coverage(start, end, location.timezone_name, timestamps)
        rows.append(
            {
                "location_id": location_id,
                "start": start.isoformat(),
                "end": end.isoformat(),
                **coverage,
                "byte_count": bytes_saved,
                "windows": len(windows),
                "api_requests_including_retries": policy.requests_made - requests_before,
            }
        )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(
            {
                "source": "Open-Meteo Historical Weather API",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(args.report.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
