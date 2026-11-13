"""Testes de persistência raw."""

import hashlib
import json
from pathlib import Path

from climatewatch.infrastructure.raw_store import RawStore


def test_store_preserves_bytes_hash_and_filters_secrets(tmp_path: Path) -> None:
    """Confere bytes, hash, sidecar e remoção de campos sensíveis."""
    body = b'{"hello":"clima"}'
    manifest = RawStore(tmp_path).save(body, {"source": "fixture", "api_token": "nao-salvar"})
    path = Path(manifest["raw_path"])
    assert path.read_bytes() == body
    assert manifest["sha256"] == hashlib.sha256(body).hexdigest()
    sidecar = json.loads(path.with_suffix(".manifest.json").read_text())
    assert "api_token" not in sidecar
    assert not list(path.parent.glob(".*.tmp"))
