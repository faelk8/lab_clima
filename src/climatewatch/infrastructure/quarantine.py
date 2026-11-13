"""Quarentena durável de payloads raw que falham contrato."""

import json
from pathlib import Path
from typing import Any

from climatewatch.infrastructure.raw_store import RawStore


class QuarantineStore:
    """Registra motivo e ponteiro ao raw para correção e replay."""

    def __init__(self, root: Path) -> None:
        """Define a pasta de quarentena."""
        self.root = root

    def save(self, raw_manifest: dict[str, Any], reason: str) -> Path:
        """Grava registro de quarentena atomicamente sem copiar nem remover raw."""
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{raw_manifest['sha256']}.json"
        RawStore._atomic_write(
            path,
            json.dumps(
                {
                    "reason": reason,
                    "raw_path": raw_manifest["raw_path"],
                    "sha256": raw_manifest["sha256"],
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode(),
        )
        return path
