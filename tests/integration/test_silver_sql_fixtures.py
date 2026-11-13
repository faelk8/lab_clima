"""Cobertura de fixtures do Silver no runtime Spark SDP, opt-in com Docker."""

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = "/app/tests/integration/silver-fixture-pipeline.yml"
BATCH_PREFIX = "silver-fixture-"


def _body(hourly: dict, units: dict | None = None, model: str = "fixture-model") -> bytes:
    return json.dumps(
        {
            "model": model,
            "hourly_units": units
            or {
                "temperature_2m": "°C",
                "precipitation": "mm",
                "relative_humidity_2m": "%",
                "wind_speed_10m": "km/h",
            },
            "hourly": hourly,
        }
    ).encode()


def _write_fixture(
    payload: bytes, label: str, timezone_name: str, variables: list[str] | None = None
) -> tuple[Path, Path]:
    digest = hashlib.sha256(payload).hexdigest()
    directory = ROOT / "data" / "raw" / "silver-fixtures"
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / f"{digest}.json"
    sidecar_path = directory / f"{digest}.manifest.json"
    raw_path.write_bytes(payload)
    manifest = {
        "sha256": digest,
        "source": "silver-fixture-source",
        "batch_id": f"{BATCH_PREFIX}{label}",
        "location_id": f"silver-{label}",
        "timezone_name": timezone_name,
        "variables": variables if variables is not None else [
            "temperature_2m",
            "precipitation",
            "relative_humidity_2m",
            "wind_speed_10m",
        ],
        "params": {
            "location_id": f"silver-{label}",
            "start": "2024-01-01",
            "end": "2024-01-02",
            "timezone_name": timezone_name,
            "variables": variables if variables is not None else [
                "temperature_2m",
                "precipitation",
                "relative_humidity_2m",
                "wind_speed_10m",
            ],
        },
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    sidecar_path.write_text(json.dumps(manifest), encoding="utf-8")
    return raw_path, sidecar_path


def _docker(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["docker", "compose", "run", "--build", "--rm", "climatewatch", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode:
        raise AssertionError((result.stdout + result.stderr)[-4000:])
    return result


@pytest.mark.skipif(
    os.getenv("CLIMATEWATCH_SILVER_FIXTURES") != "1" or shutil.which("docker") is None,
    reason="requer Docker SDP (CLIMATEWATCH_SILVER_FIXTURES=1)",
)
def test_silver_sql_fixture_quality_timezone_dst_and_deduplication() -> None:
    """Confere aceitação/rejeição, UTC, DST e resolução determinística de duplicatas."""
    fixtures: list[tuple[Path, Path]] = []
    try:
        fixtures.extend(
            [
                _write_fixture(
                    _body(
                        {
                            "time": ["2024-01-15T12:00"],
                            "temperature_2m": [20.0],
                            "precipitation": [0.0],
                            "relative_humidity_2m": [40.0],
                            "wind_speed_10m": [5.0],
                        }
                    ),
                    "utc",
                    "America/Sao_Paulo",
                ),
                _write_fixture(
                    _body(
                        {
                            "time": ["2024-03-10T02:30"],
                            "temperature_2m": [10.0],
                            "precipitation": [0.0],
                            "relative_humidity_2m": [50.0],
                            "wind_speed_10m": [2.0],
                        }
                    ),
                    "dst-gap",
                    "America/New_York",
                ),
                _write_fixture(
                    _body(
                        {
                            "time": ["2024-11-03T01:30"],
                            "temperature_2m": [11.0],
                            "precipitation": [0.0],
                            "relative_humidity_2m": [50.0],
                            "wind_speed_10m": [2.0],
                        }
                    ),
                    "dst-fold",
                    "America/New_York",
                ),
                _write_fixture(
                    _body(
                        {
                            "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                            "temperature_2m": [1.0],
                            "precipitation": [0.0, 0.0],
                            "relative_humidity_2m": [None, 50.0],
                            "wind_speed_10m": [1.0, 1.0],
                        }
                    ),
                    "misaligned-null",
                    "UTC",
                ),
                _write_fixture(
                    _body(
                        {
                            "time": ["2024-01-01T00:00"],
                            "temperature_2m": [1.0],
                            "precipitation": [0.0],
                            "relative_humidity_2m": [50.0],
                            "wind_speed_10m": [1.0],
                        },
                        units={
                            "temperature_2m": "kelvin",
                            "precipitation": "mm",
                            "relative_humidity_2m": "%",
                            "wind_speed_10m": "km/h",
                        },
                    ),
                    "bad-unit",
                    "UTC",
                ),
                _write_fixture(
                    _body(
                        {
                            "time": ["2024-01-01T00:00"],
                            "precipitation": [0.0],
                            "relative_humidity_2m": [50.0],
                            "wind_speed_10m": [1.0],
                        }
                    ),
                    "missing-required",
                    "UTC",
                ),
                _write_fixture(
                    _body(
                        {
                            "time": ["2024-01-01T00:00"],
                            "temperature_2m": [1.0],
                            "precipitation": [0.0],
                            "relative_humidity_2m": [50.0],
                            "wind_speed_10m": [1.0],
                        }
                    ),
                    "empty-requested",
                    "UTC",
                    variables=[],
                ),
            ]
        )
        # Duas respostas para a mesma chave lógica. A ingestão mais recente vence.
        for temp, label, ingested_at in [
            (18.0, "dedupe-old", "2025-01-01T00:00:00+00:00"),
            (19.0, "dedupe-new", "2025-01-02T00:00:00+00:00"),
        ]:
            payload = _body(
                {
                    "time": ["2024-02-01T00:00"],
                    "temperature_2m": [temp],
                    "precipitation": [0.0],
                    "relative_humidity_2m": [50.0],
                    "wind_speed_10m": [1.0],
                }
            )
            raw, sidecar = _write_fixture(payload, label, "UTC")
            manifest = json.loads(sidecar.read_text(encoding="utf-8"))
            manifest["location_id"] = "silver-dedupe"
            manifest["params"]["location_id"] = "silver-dedupe"
            manifest["ingested_at"] = ingested_at
            sidecar.write_text(json.dumps(manifest), encoding="utf-8")
            fixtures.append((raw, sidecar))

        tie_digests: dict[str, str] = {}
        for temp, label in [(22.0, "tie-a"), (23.0, "tie-b")]:
            payload = _body(
                {
                    "time": ["2024-02-02T00:00"],
                    "temperature_2m": [temp],
                    "precipitation": [0.0],
                    "relative_humidity_2m": [50.0],
                    "wind_speed_10m": [1.0],
                }
            )
            raw, sidecar = _write_fixture(payload, label, "UTC")
            manifest = json.loads(sidecar.read_text(encoding="utf-8"))
            manifest["location_id"] = "silver-tie"
            manifest["params"]["location_id"] = "silver-tie"
            manifest["ingested_at"] = "2025-01-03T00:00:00+00:00"
            sidecar.write_text(json.dumps(manifest), encoding="utf-8")
            fixtures.append((raw, sidecar))
            tie_digests[label] = hashlib.sha256(payload).hexdigest()

        _docker(
            "python", "-c",
            "from pyspark.sql import SparkSession; "
            "SparkSession.builder.getOrCreate().sql("
            "'CREATE DATABASE IF NOT EXISTS climatewatch_silver_fixture_test')",
        )
        _docker("spark-pipelines", "run", "--spec", SPEC)
        query = (
            "from pyspark.sql import SparkSession; import json; "
            "s=SparkSession.builder.getOrCreate(); "
            "d='climatewatch_silver_fixture_test.'; "
            f"b='{BATCH_PREFIX}'; "
            "a=s.table(d+'silver_observations').where(\"batch_id like '" + BATCH_PREFIX + "%'\"); "
            "r=s.table(d+'silver_rejected').where(\"batch_id like '" + BATCH_PREFIX + "%'\"); "
            "print('ACCEPTED='+json.dumps([x.asDict(recursive=True) for x in a.collect()], "
            "default=str)); "
            "print('REJECTED='+json.dumps([x.asDict(recursive=True) for x in r.collect()], "
            "default=str))"
        )
        result = _docker("python", "-c", query)
        accepted_line = next(
            line.removeprefix("ACCEPTED=")
            for line in result.stdout.splitlines()
            if line.startswith("ACCEPTED=")
        )
        rejected_line = next(
            line.removeprefix("REJECTED=")
            for line in result.stdout.splitlines()
            if line.startswith("REJECTED=")
        )
        accepted = json.loads(accepted_line)
        rejected = json.loads(rejected_line)

        def by_batch(rows: list[dict], suffix: str) -> list[dict]:
            return [row for row in rows if row["batch_id"] == f"{BATCH_PREFIX}{suffix}"]

        utc = by_batch(accepted, "utc")
        assert len(utc) == 1
        assert utc[0]["observed_at_utc"].startswith("2024-01-15 15:00:00")
        dst_gap = by_batch(accepted, "dst-gap")
        dst_fold = by_batch(accepted, "dst-fold")
        assert len(dst_gap) == 1
        assert dst_gap[0]["observed_at_utc"].startswith("2024-03-10 07:30:00")
        assert len(dst_fold) == 1
        assert dst_fold[0]["observed_at_utc"].startswith("2024-11-03 05:30:00")
        misaligned = by_batch(rejected, "misaligned-null")
        assert any("misaligned_temperature_array" in row["quality_flags"] for row in misaligned)
        assert any("missing_humidity" in row["quality_flags"] for row in misaligned)
        assert "invalid_temperature_unit" in by_batch(rejected, "bad-unit")[0]["quality_flags"]
        assert "missing_temperature" in by_batch(rejected, "missing-required")[0]["quality_flags"]
        assert (
            "missing_requested_variables"
            in by_batch(rejected, "empty-requested")[0]["quality_flags"]
        )
        deduped = by_batch(accepted, "dedupe-new")
        assert len(deduped) == 1 and deduped[0]["temperature_c"] == 19.0
        assert not by_batch(accepted, "dedupe-old")
        tie_winner = max(tie_digests, key=tie_digests.get)
        assert len(by_batch(accepted, tie_winner)) == 1
        assert not by_batch(accepted, "tie-a" if tie_winner == "tie-b" else "tie-b")
    finally:
        for raw_path, sidecar_path in fixtures:
            raw_path.unlink(missing_ok=True)
            sidecar_path.unlink(missing_ok=True)
        fixture_dir = ROOT / "data" / "raw" / "silver-fixtures"
        try:
            fixture_dir.rmdir()
        except OSError:
            pass
