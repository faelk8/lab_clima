"""Interface CLI para coletar dados históricos."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from climatewatch.application.download import download_weather
from climatewatch.domain.weather import Location


def load_locations(path: Path) -> dict[str, Location]:
    """Carrega catálogo de localidades configurável."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["location_id"]: Location(
            item["location_id"], item["name"], item["latitude"], item["longitude"], item["timezone"]
        )
        for item in data["locations"]
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a coleta e imprime manifesto sem segredos."""
    parser = argparse.ArgumentParser(description="Baixa clima histórico Open-Meteo")
    parser.add_argument("--location-id", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--variables", default="temperature_2m,precipitation")
    parser.add_argument("--locations", type=Path, default=Path("config/locations.json"))
    parser.add_argument("--output", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--force-refresh", action="store_true", help="ignora o estado concluído do lote"
    )
    args = parser.parse_args(argv)
    locations = load_locations(args.locations)
    if args.location_id not in locations:
        parser.error("location-id não consta no catálogo")
    try:
        result = download_weather(
            locations[args.location_id],
            args.start,
            args.end,
            [value.strip() for value in args.variables.split(",")],
            args.output,
            force_refresh=args.force_refresh,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
