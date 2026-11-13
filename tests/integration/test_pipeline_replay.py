"""Replay e correção histórica do DAG Bronze → Silver → Gold em Docker."""

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "f3-replay-test"
SPEC = "/app/spark-pipeline.yml"


def _docker(*args: str) -> str:
    result = subprocess.run(
        ["docker", "compose", "run", "--build", "--rm", "climatewatch", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]
    return result.stdout


def _fixture(
    temperature: float,
    ingested_at: str,
    optional: bool = False,
    location: str = "f3-replay-location",
    missing_hour: int | None = None,
) -> tuple[Path, Path]:
    hours = [f"2024-06-01T{hour:02d}:00" for hour in range(24) if hour != missing_hour]
    body = {
        "model": "replay-model",
        "hourly_units": {"temperature_2m": "°C", "precipitation": "mm"},
        "hourly": {
            "time": hours,
            "temperature_2m": [temperature] * len(hours),
            "precipitation": [1.0] * len(hours),
        },
        "fixture_location": location,
    }
    if optional:
        body["optional_note"] = "campo novo tolerado"
    payload = json.dumps(body).encode()
    digest = hashlib.sha256(payload).hexdigest()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw = RAW_DIR / f"{digest}.json"
    sidecar = RAW_DIR / f"{digest}.manifest.json"
    raw.write_bytes(payload)
    sidecar.write_text(json.dumps({
        "sha256": digest,
        "source": "replay-fixture",
        "batch_id": f"replay-{digest[:12]}",
        "location_id": location,
        "timezone_name": "UTC",
        "variables": ["temperature_2m", "precipitation"],
        "ingested_at": ingested_at,
    }), encoding="utf-8")
    return raw, sidecar


def _snapshot() -> dict:
    code = """
import json
from pyspark.sql import SparkSession
s = SparkSession.builder.getOrCreate()
d = s.table('climatewatch_f3.gold_daily').where("location_id = 'f3-replay-location'").first()
i = s.table('climatewatch_f3.gold_indicators').where("location_id = 'f3-replay-location'")
last = i.orderBy('observed_at_utc', ascending=False).first()
gap = s.table('climatewatch_f3.gold_daily').where("location_id = 'f3-gap-location'").first()
rank = s.table('climatewatch_f3.gold_daily_ranking')
rank = rank.where("location_id IN ('f3-replay-location', 'f3-tie-location')")
print('SNAPSHOT=' + json.dumps({'daily': d.asDict() if d else None,
  'hours': i.count(), 'last': last.asDict() if last else None,
  'gap': gap.asDict() if gap else None,
  'ranks': sorted([(r.location_id, r.precipitation_rank) for r in rank.collect()])},
  default=str))
"""
    output = _docker("python", "-c", code)
    return json.loads(next(line.removeprefix("SNAPSHOT=") for line in output.splitlines()
                           if line.startswith("SNAPSHOT=")))


@pytest.mark.skipif(
    os.getenv("CLIMATEWATCH_F3_REPLAY") != "1" or shutil.which("docker") is None,
    reason="requer Docker (CLIMATEWATCH_F3_REPLAY=1)",
)
def test_replay_correction_optional_schema_and_gold() -> None:
    """Replay preserva valores e correção mais recente recalcula Gold."""
    paths: list[Path] = []
    try:
        paths.extend(_fixture(10.0, "2024-06-02T00:00:00Z"))
        paths.extend(_fixture(
            10.0, "2024-06-02T00:00:00Z", location="f3-gap-location", missing_hour=12
        ))
        paths.extend(_fixture(
            10.0, "2024-06-02T00:00:00Z", location="f3-tie-location"
        ))
        _docker("spark-pipelines", "run", "--spec", SPEC)
        initial = _snapshot()
        assert initial["daily"]["observed_hours"] == 24
        assert initial["daily"]["expected_hours"] == 24
        assert initial["daily"]["incomplete_day"] is False
        assert initial["daily"]["precipitation_mm"] == 24.0
        assert initial["daily"]["temperature_avg_c"] == 10.0
        assert initial["hours"] == 24
        assert initial["last"]["precipitation_24h_mm"] == 24.0
        assert initial["last"]["complete_24h_window"] is True
        assert initial["gap"]["observed_hours"] == 23
        assert initial["gap"]["incomplete_day"] is True
        assert initial["ranks"] == [["f3-replay-location", 1], ["f3-tie-location", 1]]
        _docker("spark-pipelines", "run", "--spec", SPEC)
        assert _snapshot() == initial
        paths.extend(_fixture(20.0, "2024-06-03T00:00:00Z", optional=True))
        _docker("spark-pipelines", "run", "--spec", SPEC)
        corrected = _snapshot()
        assert corrected["hours"] == 24
        assert corrected["daily"]["observed_hours"] == 24
        assert corrected["daily"]["temperature_avg_c"] == 20.0
        assert corrected["last"]["temperature_avg_24h_c"] == 20.0
    finally:
        for path in paths:
            path.unlink(missing_ok=True)
        try:
            RAW_DIR.rmdir()
        except OSError:
            pass
