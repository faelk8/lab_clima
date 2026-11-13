"""Teste de ponta a ponta da camada Bronze no runtime SDP fixado."""

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(
    os.getenv("CLIMATEWATCH_SDP_SMOKE") != "1" or shutil.which("docker") is None,
    reason="requer Docker SDP validado (CLIMATEWATCH_SDP_SMOKE=1)",
)
def test_sdp_run_persists_raw_payload_and_provenance() -> None:
    """Executa a pipeline localmente e confere a linha persistida na tabela Bronze."""
    payload = b'{"hourly":{"time":["2024-01-01T00:00"],"temperature_2m":[12.5]}}'
    digest = hashlib.sha256(payload).hexdigest()
    batch_id = "integration-bronze-" + digest
    raw_dir = ROOT / "data" / "raw" / digest[:2]
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{digest}.json"
    sidecar_path = raw_path.with_suffix(".manifest.json")
    manifest = {
        "sha256": digest,
        "raw_path": f"/app/data/raw/{digest[:2]}/{digest}.json",
        "source": "integration-fixture",
        "batch_id": batch_id,
        "params": {"location_id": "fixture", "start": "2024-01-01"},
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    raw_path.write_bytes(payload)
    sidecar_path.write_text(json.dumps(manifest), encoding="utf-8")
    run = [
        "docker",
        "compose",
        "run",
        "--build",
        "--rm",
        "climatewatch",
        "spark-pipelines",
        "run",
        "--spec",
        "/app/spark-pipeline.yml",
    ]
    query_code = (
        "from pyspark.sql import SparkSession; "
        "s=SparkSession.builder.getOrCreate(); "
        f"r=s.read.table('bronze_raw').where(\"sha256 = '{digest}'\").limit(1).first(); "
        "print('BRONZE_ROW=' + repr(r.asDict(recursive=True) if r else None)); "
        "print('BRONZE_PAYLOAD_HEX=' + (r['payload'].hex() if r else 'missing'))"
    )
    query = [
        "docker",
        "compose",
        "run",
        "--rm",
        "climatewatch",
        "python",
        "-c",
        query_code,
    ]
    did_run = False
    try:
        subprocess.run(run, cwd=ROOT, check=True, capture_output=True, text=True, timeout=600)
        did_run = True
        result = subprocess.run(
            query, cwd=ROOT, check=True, capture_output=True, text=True, timeout=180
        )
        assert "BRONZE_ROW=" in result.stdout
        assert digest in result.stdout
        assert batch_id in result.stdout
        assert "integration-fixture" in result.stdout
        assert "2024-01-01" in result.stdout
        assert payload.hex() in result.stdout
    finally:
        raw_path.unlink(missing_ok=True)
        sidecar_path.unlink(missing_ok=True)
        try:
            raw_dir.rmdir()
        except OSError:
            pass
        if did_run:
            subprocess.run(run, cwd=ROOT, capture_output=True, text=True, timeout=600)
