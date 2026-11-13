"""Armazenamento local atômico para resposta raw e manifesto de proveniência."""

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RawStore:
    """Salva bytes de origem sem transformá-los e metadados sem credenciais."""

    def __init__(self, root: Path) -> None:
        """Define a raiz de persistência raw."""
        self.root = root

    def save(self, body: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
        """Persiste payload e sidecar com replace atômico e devolve o manifesto."""
        digest = hashlib.sha256(body).hexdigest()
        directory = self.root / digest[:2]
        directory.mkdir(parents=True, exist_ok=True)
        data_path = directory / f"{digest}.json"
        safe = {
            key: value
            for key, value in metadata.items()
            if not any(secret in key.lower() for secret in ("token", "password", "secret", "key"))
        }
        manifest = {
            **safe,
            "sha256": digest,
            "byte_count": len(body),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "raw_path": str(data_path),
        }
        self._atomic_write(data_path, body)
        self._atomic_write(
            data_path.with_suffix(".manifest.json"),
            json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode(),
        )
        return manifest

    @staticmethod
    def _atomic_write(path: Path, data: bytes) -> None:
        """Escreve arquivo temporário no mesmo filesystem e substitui atomicamente."""
        fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
