"""Retoma lotes failed/running do manifesto local."""

import argparse
from pathlib import Path

from climatewatch.application.download import download_weather
from climatewatch.application.resume import resume_incomplete
from climatewatch.infrastructure.batch_manifest import BatchManifest
from climatewatch.interfaces.cli import load_locations


def main() -> int:
    """Reexecuta somente entradas incompletas mantendo parâmetros do lote."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/state/batches.json"))
    parser.add_argument("--catalog", type=Path, default=Path("config/locations.json"))
    parser.add_argument("--output", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    manifest = BatchManifest(args.manifest)
    results = resume_incomplete(
        manifest, load_locations(args.catalog), args.output, download_weather
    )
    print(f"Lotes retomados: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
