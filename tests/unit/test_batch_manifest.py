"""Testes de transições e histórico do manifesto batch."""

import multiprocessing
import time
from pathlib import Path
from queue import Empty

import pytest

from climatewatch.infrastructure.batch_manifest import BatchManifest


def _claim_batch_process(
    manifest_path,
    params,
    results,
    request_count,
    release,
    acquired=None,
    attempting=None,
):
    """Claim worker para comprovar o lock entre processos separados."""
    if attempting is not None:
        attempting.set()
    store = BatchManifest(manifest_path)
    with store.claim(params) as (batch_id, entry):
        if entry["status"] == "running":
            with request_count.get_lock():
                request_count.value += 1
            if acquired is not None:
                acquired.set()
                release.wait(timeout=5)
            store.succeed(
                batch_id,
                {"sha256": "digest", "raw_path": "/raw", "ingested_at": "now"},
            )
            status = "succeeded"
        else:
            status = entry["status"]
        results.put(status)


def _hold_running_claim(manifest_path: Path, params: dict[str, str], acquired) -> None:
    """Mantém claim ativo para o pai simular encerramento abrupto do processo."""
    with BatchManifest(manifest_path).claim(params):
        acquired.set()
        time.sleep(10)


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


def test_running_batch_rejects_second_unclaimed_begin(tmp_path: Path) -> None:
    """Um segundo escritor não pode assumir um lote ainda em execução."""
    store = BatchManifest(tmp_path / "state.json")
    params = {"location_id": "x"}
    store.begin(params)
    with pytest.raises(RuntimeError, match="execução ativa"):
        store.begin(params)


def test_claim_serializes_writers_and_reclaims_abandoned_batch(tmp_path: Path) -> None:
    """Claim serializa writers e a liberação do lock permite retomar órfão."""
    params = {"location_id": "x"}
    context = multiprocessing.get_context("fork")
    manifest_path = tmp_path / "state.json"
    results = context.Queue()
    request_count = context.Value("i", 0)
    release = context.Event()
    acquired = context.Event()
    attempting = context.Event()
    first = context.Process(
        target=_claim_batch_process,
        args=(manifest_path, params, results, request_count, release, acquired),
    )
    second = context.Process(
        target=_claim_batch_process,
        args=(manifest_path, params, results, request_count, release, None, attempting),
    )
    first.start()
    try:
        assert acquired.wait(timeout=2)
        second.start()
        assert attempting.wait(timeout=2)
        with pytest.raises(Empty):
            results.get(timeout=0.1)
    finally:
        release.set()
        first.join(timeout=2)
        if second.pid is not None:
            second.join(timeout=2)
        if first.is_alive():
            first.terminate()
            first.join()
        if second.is_alive():
            second.terminate()
            second.join()
    statuses = [results.get(timeout=1), results.get(timeout=1)]
    assert first.exitcode == 0
    assert second.exitcode == 0
    assert statuses == ["succeeded", "succeeded"]
    assert request_count.value == 1

    store = BatchManifest(manifest_path)

    interrupted = {"location_id": "interrupted"}
    owner_acquired = context.Event()
    owner = context.Process(
        target=_hold_running_claim,
        args=(manifest_path, interrupted, owner_acquired),
    )
    owner.start()
    try:
        assert owner_acquired.wait(timeout=2)
    finally:
        if owner.is_alive():
            owner.terminate()
        owner.join(timeout=2)
    assert owner.exitcode is not None
    with store.claim(interrupted) as (_, resumed):
        assert resumed["status"] == "running"
        assert resumed["attempts"] == 2
