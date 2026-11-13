"""Testes de transições e histórico do manifesto batch."""

from pathlib import Path

import pytest

from climatewatch.infrastructure.batch_manifest import BatchManifest


def test_manifest_replay_and_content_revision(tmp_path: Path) -> None:
    """Mesmo hash não duplica versão; conteúdo novo preserva a versão antiga."""
    store = BatchManifest(tmp_path / "state.json")
    params = {"location_id": "x", "start": "2024-01-01"}
    batch_id, entry = store.begin(params)
    assert entry["status"] == "running"
    store.succeed(batch_id, {"sha256": "a", "raw_path": "/raw/a", "ingested_at": "t1"})
    _, completed = store.begin(params)
    assert completed["status"] == "succeeded"
    assert len(completed["versions"]) == 1
    store.begin(params, force=True)
    store.succeed(batch_id, {"sha256": "b", "raw_path": "/raw/b", "ingested_at": "t2"})
    assert [v["sha256"] for v in store.entries()[0]["versions"]] == ["a", "b"]


def test_manifest_failure_can_resume_and_invalid_transition_fails(tmp_path: Path) -> None:
    """Falha mantém causa e lote pode recomeçar com contador de tentativas."""
    store = BatchManifest(tmp_path / "state.json")
    batch_id, _ = store.begin({"location_id": "x"})
    store.fail(batch_id, "timeout")
    _, retry = store.begin({"location_id": "x"})
    assert retry["attempts"] == 2
    with pytest.raises(ValueError, match="running"):
        store.succeed("missing", {"sha256": "x", "raw_path": "/x", "ingested_at": "t"})
