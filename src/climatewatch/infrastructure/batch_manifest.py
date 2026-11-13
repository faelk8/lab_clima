"""Manifesto JSON durável para controle e replay de lotes."""

import fcntl
import hashlib
import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast


class BatchManifest:
    """Mantém estados de lote com lock exclusivo entre processos."""

    def __init__(self, path: Path) -> None:
        """Configura o caminho do manifesto e o lock lateral."""
        self.path = path
        self.lock_path = path.with_suffix(path.suffix + ".lock")

    @staticmethod
    def batch_id(params: dict[str, Any]) -> str:
        """Gera ID estável a partir de parâmetros normalizados."""
        payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def begin(
        self,
        params: dict[str, Any],
        *,
        force: bool = False,
        _claimed: bool = False,
    ) -> tuple[str, dict[str, Any]]:
        """Marca lote como running; lote já concluído é devolvido sem alteração."""
        batch_id = self.batch_id(params)
        with self._locked() as batches:
            existing = batches.get(batch_id)
            if existing and existing["status"] == "succeeded" and not force:
                return batch_id, existing
            if existing and existing["status"] == "running" and not _claimed:
                raise RuntimeError(f"lote {batch_id} já possui execução ativa")
            entry = existing or {
                "batch_id": batch_id,
                "params": params,
                "attempts": 0,
                "versions": [],
            }
            entry.update(status="running", started_at=self._now(), updated_at=self._now())
            entry["attempts"] += 1
            batches[batch_id] = entry
        return batch_id, entry

    @contextmanager
    def claim(
        self, params: dict[str, Any], *, force: bool = False
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Serializa toda a execução do lote e recupera estado deixado por processo morto."""
        batch_id = self.batch_id(params)
        claim_path = self.path.with_name(f"{self.path.name}.{batch_id}.claim")
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        with claim_path.open("a+") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                claimed_id, entry = self.begin(params, force=force, _claimed=True)
                yield claimed_id, entry
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def succeed(self, batch_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
        """Marca lote como concluído somente depois da persistência raw."""
        with self._locked() as batches:
            entry = self._require_running(batches, batch_id)
            digest = manifest["sha256"]
            known = {version["sha256"] for version in entry["versions"]}
            if digest not in known:
                entry["versions"].append(
                    {
                        "sha256": digest,
                        "raw_path": manifest["raw_path"],
                        "ingested_at": manifest["ingested_at"],
                    }
                )
            entry.update(
                status="succeeded",
                sha256=digest,
                raw_path=manifest["raw_path"],
                byte_count=manifest.get("byte_count", 0),
                completed_at=self._now(),
                updated_at=self._now(),
                error=None,
            )
            batches[batch_id] = entry
        return entry

    def fail(
        self,
        batch_id: str,
        error: str,
        quarantine_path: str | None = None,
        raw_manifest: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Registra falha explícita sem apagar raw ou tentativas anteriores."""
        with self._locked() as batches:
            entry = self._require_running(batches, batch_id)
            entry.update(status="failed", error=error, updated_at=self._now())
            if quarantine_path:
                entry["quarantine_path"] = quarantine_path
            if raw_manifest:
                entry["raw_path"] = raw_manifest["raw_path"]
                entry["sha256"] = raw_manifest["sha256"]
            batches[batch_id] = entry
        return entry

    def entries(self, statuses: set[str] | None = None) -> list[dict[str, Any]]:
        """Lista lotes em ordem estável, opcionalmente filtrados por estado."""
        with self._locked() as batches:
            values = list(batches.values())
        return sorted(
            (item for item in values if statuses is None or item["status"] in statuses),
            key=lambda item: item["batch_id"],
        )

    @staticmethod
    def _require_running(batches: dict[str, Any], batch_id: str) -> dict[str, Any]:
        entry = batches.get(batch_id)
        if not entry or entry["status"] != "running":
            raise ValueError(f"lote {batch_id} não está running")
        return cast(dict[str, Any], entry)

    class _Lock:
        """Context manager para lock exclusivo e gravação atômica do manifesto."""

        def __init__(self, owner: "BatchManifest") -> None:
            self.owner = owner
            self.stream: Any = None
            self.batches: dict[str, Any] = {}

        def __enter__(self) -> dict[str, Any]:
            self.owner.path.parent.mkdir(parents=True, exist_ok=True)
            self.stream = self.owner.lock_path.open("a+")
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX)
            if self.owner.path.exists():
                self.batches = json.loads(self.owner.path.read_text(encoding="utf-8"))
            return self.batches

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            try:
                if exc_type is None:
                    self.owner._write(self.batches)
            finally:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
                self.stream.close()

    def _locked(self) -> "BatchManifest._Lock":
        """Cria contexto de leitura/escrita protegido por flock."""
        return self._Lock(self)

    def _write(self, batches: dict[str, Any]) -> None:
        """Grava manifesto com replace atômico no mesmo diretório."""
        fd, temp = tempfile.mkstemp(dir=self.path.parent, prefix=".manifest-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(batches, stream, ensure_ascii=False, sort_keys=True, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, self.path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    @staticmethod
    def _now() -> str:
        """Retorna timestamp UTC ISO 8601."""
        return datetime.now(timezone.utc).isoformat()
