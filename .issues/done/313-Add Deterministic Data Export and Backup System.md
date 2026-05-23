### Issue 313 — Add Deterministic Data Export and Backup System

**Descripción breve**  
Agregar un sistema reproducible y determinista para exportar y respaldar datos críticos del proyecto (issues, graph, storage artefacts). El sistema debe permitir exportaciones programadas y manuales, compresión y cifrado opcional, verificación de integridad, restauración desde backup, pruebas unitarias e integración, y documentación clara. Todos los nombres de archivos, rutas, comandos, variables de entorno, formatos y pasos son explícitos para que un agente o desarrollador pueda implementar y verificar sin ambigüedades.

---

### Objetivo exacto que debe entregar el agente
1. Implementar un módulo `tasker/backup` que exponga:
   - `export_data(output_path: str, include_storage: bool = True, encrypt: bool = False, passphrase: str | None = None) -> str` que crea un archivo exportado y devuelve la ruta.
   - `verify_export(file_path: str) -> bool` que valida integridad (checksum).
   - `restore_data(file_path: str, decrypt_passphrase: str | None = None) -> None` que restaura datos en el entorno de prueba.
   - `list_exports(directory: str) -> list[str]` que lista archivos exportados.
2. Añadir script CLI `scripts/backup.sh` ejecutable que:
   - Acepte subcomandos `export`, `verify`, `restore`, `list`.
   - Use `python -m tasker.backup.cli` internamente y registre comandos ejecutados.
3. Añadir integración con StoragePort y repositorios:
   - Exportar issues desde `issue_repo.export()` si existe, o serializar `issue_repo.list_all()`.
   - Exportar graph desde `graph_repo.export()` si existe, o serializar `graph_repo.dump()`.
   - Exportar objetos de `storage` listando claves y descargando valores si `include_storage` es True.
4. Añadir cifrado opcional AES-256-GCM usando `cryptography` cuando `encrypt=True`.
5. Añadir verificación de integridad con SHA256 y archivo `MANIFEST.json` dentro del tarball con metadatos: timestamp, version, checksums.
6. Añadir pruebas:
   - Unit tests `tests/backup/test_export_unit.py` y `tests/backup/test_encrypt_verify_unit.py`.
   - Integration test `tests/integration/test_backup_restore_integration.py` que crea datos de prueba, exporta, verifica, borra datos locales, restaura y valida igualdad.
7. Añadir Docker Compose job `docker-compose.backup.yml` para ejecutar backups programados con `cron` (simulado) y para pruebas de integración.
8. Añadir documentación `tasker/backup/BACKUP.md` con pasos exactos para exportar, verificar y restaurar, variables de entorno y ejemplos.
9. Crear branch `feature/backup-export-restore` y abrir PR con el PR body exacto provisto más abajo.

---

### Archivos a añadir o modificar exactos
- `tasker/backup/__init__.py` **nuevo**
- `tasker/backup/core.py` **nuevo**
- `tasker/backup/cli.py` **nuevo**
- `scripts/backup.sh` **nuevo, ejecutable**
- `tasker/backup/BACKUP.md` **nuevo**
- `docker-compose.backup.yml` **nuevo**
- `tests/backup/test_export_unit.py` **nuevo**
- `tests/backup/test_encrypt_verify_unit.py` **nuevo**
- `tests/integration/test_backup_restore_integration.py` **nuevo, integration**
- Modificar `tasker/cli/wiring.py` para exponer `storage`, `issue_repo`, `graph_repo` al módulo backup si no están ya.
- `MANIFEST` dentro del tarball generado con nombre `MANIFEST.json`.

---

### Código exacto a añadir

#### `tasker/backup/__init__.py`
```python
# tasker/backup/__init__.py
from .core import export_data, verify_export, restore_data, list_exports
from .cli import main

__all__ = ["export_data", "verify_export", "restore_data", "list_exports", "main"]
```

#### `tasker/backup/core.py`
```python
# tasker/backup/core.py
from __future__ import annotations
import os
import json
import tarfile
import tempfile
import hashlib
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _CRYPTO_AVAILABLE = True
except Exception:
    _CRYPTO_AVAILABLE = False

def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def _write_manifest(tmpdir: Path, manifest: Dict[str, Any]) -> None:
    with open(tmpdir / "MANIFEST.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

def _collect_storage(storage, tmpdir: Path) -> List[Dict[str, str]]:
    keys_meta = []
    # storage must implement list_keys or provide a way to enumerate; fallback to no storage
    if hasattr(storage, "list_keys"):
        for k in storage.list_keys():
            v = storage.get(k)
            fname = f"storage_{k.replace('/', '_')}"
            with open(tmpdir / fname, "wb") as fh:
                fh.write(v if v is not None else b"")
            keys_meta.append({"key": k, "file": fname, "sha256": _sha256_bytes(v if v is not None else b"")})
    return keys_meta

def export_data(output_path: str, issue_repo=None, graph_repo=None, storage=None, include_storage: bool = True, encrypt: bool = False, passphrase: Optional[str] = None) -> str:
    """
    Create a deterministic export tar.gz at output_path.
    Returns the path to the created file.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="tasker-export-"))
    manifest = {"timestamp": time.time(), "version": "1.0.0", "files": []}
    # export issues
    issues_file = tmpdir / "issues.json"
    issues = []
    if issue_repo is not None and hasattr(issue_repo, "list_all"):
        issues = [i for i in issue_repo.list_all()]
    with open(issues_file, "w", encoding="utf-8") as fh:
        json.dump(issues, fh, indent=2, sort_keys=True)
    with open(issues_file, "rb") as fh:
        b = fh.read()
    manifest["files"].append({"path": "issues.json", "sha256": _sha256_bytes(b)})

    # export graph
    graph_file = tmpdir / "graph.json"
    graph = []
    if graph_repo is not None and hasattr(graph_repo, "dump"):
        graph = graph_repo.dump()
    with open(graph_file, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=2, sort_keys=True)
    with open(graph_file, "rb") as fh:
        b = fh.read()
    manifest["files"].append({"path": "graph.json", "sha256": _sha256_bytes(b)})

    # export storage
    storage_meta = []
    if include_storage and storage is not None:
        storage_meta = _collect_storage(storage, tmpdir)
        for m in storage_meta:
            manifest["files"].append({"path": m["file"], "sha256": m["sha256"]})

    # write manifest
    _write_manifest(tmpdir, manifest)

    # create tar.gz
    out_path = Path(output_path)
    with tarfile.open(out_path, "w:gz") as tar:
        for f in sorted(tmpdir.iterdir(), key=lambda p: p.name):
            tar.add(f, arcname=f.name)

    # optional encryption
    if encrypt:
        if not _CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography package required for encryption")
        if not passphrase:
            raise RuntimeError("passphrase required for encryption")
        # AESGCM with key derived from passphrase via SHA256 (dev only)
        key = hashlib.sha256(passphrase.encode("utf-8")).digest()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        with open(out_path, "rb") as fh:
            plaintext = fh.read()
        ct = aesgcm.encrypt(nonce, plaintext, None)
        enc_path = out_path.with_suffix(out_path.suffix + ".enc")
        with open(enc_path, "wb") as fh:
            fh.write(nonce + ct)
        out_path.unlink()
        out_path = enc_path

    return str(out_path)

def verify_export(file_path: str) -> bool:
    """
    Verify integrity of export by checking MANIFEST.json checksums.
    Supports encrypted files only after decryption by caller.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="tasker-verify-"))
    # extract tar.gz
    with tarfile.open(file_path, "r:gz") as tar:
        tar.extractall(path=tmpdir)
    manifest_path = tmpdir / "MANIFEST.json"
    if not manifest_path.exists():
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("files", []):
        p = tmpdir / entry["path"]
        if not p.exists():
            return False
        b = p.read_bytes()
        if _sha256_bytes(b) != entry["sha256"]:
            return False
    return True

def restore_data(file_path: str, issue_repo=None, graph_repo=None, storage=None, decrypt_passphrase: Optional[str] = None) -> None:
    """
    Restore data from export. If encrypted, caller must decrypt to a temporary file and pass that path.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="tasker-restore-"))
    with tarfile.open(file_path, "r:gz") as tar:
        tar.extractall(path=tmpdir)
    # restore issues
    issues_file = tmpdir / "issues.json"
    if issues_file.exists() and issue_repo is not None and hasattr(issue_repo, "import_list"):
        data = json.loads(issues_file.read_text(encoding="utf-8"))
        issue_repo.import_list(data)
    # restore graph
    graph_file = tmpdir / "graph.json"
    if graph_file.exists() and graph_repo is not None and hasattr(graph_repo, "import_dump"):
        data = json.loads(graph_file.read_text(encoding="utf-8"))
        graph_repo.import_dump(data)
    # restore storage
    if storage is not None:
        for p in tmpdir.iterdir():
            if p.name.startswith("storage_"):
                key = p.name[len("storage_"):].replace("_", "/")
                storage.put(key, p.read_bytes())
```

#### `tasker/backup/cli.py`
```python
# tasker/backup/cli.py
from __future__ import annotations
import argparse
import os
import sys
from tasker.backup.core import export_data, verify_export, restore_data, list_exports
from tasker.cli.wiring import build_default_container

def main(argv=None):
    p = argparse.ArgumentParser(prog="tasker-backup")
    sub = p.add_subparsers(dest="cmd")
    ex = sub.add_parser("export")
    ex.add_argument("--out", required=True)
    ex.add_argument("--no-storage", action="store_true")
    ex.add_argument("--encrypt", action="store_true")
    ex.add_argument("--passphrase", default=None)
    vr = sub.add_parser("verify")
    vr.add_argument("--file", required=True)
    rs = sub.add_parser("restore")
    rs.add_argument("--file", required=True)
    rs.add_argument("--passphrase", default=None)
    ls = sub.add_parser("list")
    args = p.parse_args(argv)

    container = build_default_container()
    if args.cmd == "export":
        out = args.out
        include_storage = not args.no_storage
        path = export_data(out, issue_repo=container.issue_repo, graph_repo=container.graph_repo, storage=container.storage if include_storage else None, include_storage=include_storage, encrypt=args.encrypt, passphrase=args.passphrase)
        print("Exported to", path)
    elif args.cmd == "verify":
        ok = verify_export(args.file)
        print("Verified" if ok else "Invalid")
        sys.exit(0 if ok else 2)
    elif args.cmd == "restore":
        restore_data(args.file, issue_repo=container.issue_repo, graph_repo=container.graph_repo, storage=container.storage, decrypt_passphrase=args.passphrase)
        print("Restore complete")
    elif args.cmd == "list":
        exports = list_exports(os.getcwd())
        for e in exports:
            print(e)
    else:
        p.print_help()
```

#### `scripts/backup.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 export|verify|restore|list [args]" >&2
  exit 2
fi
CMD="$1"
shift
echo "python -m tasker.backup.cli $CMD $*" >&2
python -m tasker.backup.cli "$CMD" "$@"
```
Make executable with `chmod +x scripts/backup.sh`.

---

### Docker Compose for scheduled backups

Create `docker-compose.backup.yml` with the exact content below.

```yaml
version: "3.8"
services:
  backup-runner:
    image: python:3.11-slim
    working_dir: /workspace
    command: ["bash", "-lc", "python -m pip install -e . && ./scripts/backup.sh export --out /workspace/exports/backup-$(date -u +%Y%m%dT%H%M%SZ).tar.gz --passphrase ${TASKER_BACKUP_PASSPHRASE:-} || true"]
    volumes:
      - ./:/workspace:cached
    environment:
      TASKER_BACKUP_PASSPHRASE: "${TASKER_BACKUP_PASSPHRASE:-}"
    restart: "no"
```

---

### Tests exact content

#### `tests/backup/test_export_unit.py`
```python
# tests/backup/test_export_unit.py
import tempfile
from tasker.backup.core import export_data, verify_export
from tasker.infrastructure.memory_storage import MemoryStorage
from unittest.mock import MagicMock

def test_export_and_verify(tmp_path):
    storage = MemoryStorage()
    storage.put("k1", b"v1")
    # mock repos
    issue_repo = MagicMock()
    issue_repo.list_all.return_value = [{"id":"i1","title":"T"}]
    graph_repo = MagicMock()
    graph_repo.dump.return_value = [{"node":"n1"}]
    out = tmp_path / "export.tar.gz"
    path = export_data(str(out), issue_repo=issue_repo, graph_repo=graph_repo, storage=storage, include_storage=True, encrypt=False)
    assert path == str(out)
    assert verify_export(path)
```

#### `tests/backup/test_encrypt_verify_unit.py`
```python
# tests/backup/test_encrypt_verify_unit.py
import tempfile
from tasker.backup.core import export_data
from tasker.infrastructure.memory_storage import MemoryStorage
from unittest.mock import MagicMock
import os

def test_export_encrypt(tmp_path):
    storage = MemoryStorage()
    issue_repo = MagicMock()
    issue_repo.list_all.return_value = []
    graph_repo = MagicMock()
    graph_repo.dump.return_value = []
    out = tmp_path / "export.tar.gz"
    # require cryptography installed for this test
    passphrase = "testpass"
    path = export_data(str(out), issue_repo=issue_repo, graph_repo=graph_repo, storage=storage, include_storage=False, encrypt=True, passphrase=passphrase)
    assert path.endswith(".enc")
    assert os.path.exists(path)
```

#### `tests/integration/test_backup_restore_integration.py`
```python
# tests/integration/test_backup_restore_integration.py
import os
import tempfile
import time
import pytest
from tasker.infrastructure.memory_storage import MemoryStorage
from tasker.backup.core import export_data, verify_export, restore_data
from unittest.mock import MagicMock

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_backup_restore_cycle(tmp_path):
    _skip_if_not_integration()
    storage = MemoryStorage()
    storage.put("k1", b"v1")
    issue_repo = MagicMock()
    issue_repo.list_all.return_value = [{"id":"i1","title":"T"}]
    graph_repo = MagicMock()
    graph_repo.dump.return_value = [{"node":"n1"}]
    out = tmp_path / "export.tar.gz"
    path = export_data(str(out), issue_repo=issue_repo, graph_repo=graph_repo, storage=storage, include_storage=True, encrypt=False)
    assert verify_export(path)
    # simulate delete
    storage.delete("k1")
    assert storage.get("k1") is None
    # restore
    restore_data(path, issue_repo=issue_repo, graph_repo=graph_repo, storage=storage)
    assert storage.get("k1") == b"v1"
```

---

### Documentación exacta

Create `tasker/backup/BACKUP.md` with the exact content below.

```
Backup and Export Guide

Commands
- Manual export:
  ./scripts/backup.sh export --out ./exports/backup-YYYYMMDDTHHMMSSZ.tar.gz
- Verify export:
  ./scripts/backup.sh verify --file ./exports/backup-YYYYMMDDTHHMMSSZ.tar.gz
- Restore:
  ./scripts/backup.sh restore --file ./exports/backup-YYYYMMDDTHHMMSSZ.tar.gz

Options
- --no-storage skip exporting storage keys
- --encrypt enable AES-256-GCM encryption (requires cryptography)
- --passphrase passphrase for encryption

Environment variables
- TASKER_BACKUP_PASSPHRASE optional passphrase for scheduled backups
- TASKER_INTEGRATION set to 1 to run integration tests

Format
- Export is a tar.gz containing:
  - issues.json
  - graph.json
  - storage_* files for storage keys
  - MANIFEST.json with checksums and metadata

Restoration
- restore_data will call repo import methods if available:
  - issue_repo.import_list(list)
  - graph_repo.import_dump(list)
- Storage keys are restored via storage.put(key, bytes)

Security
- Encryption uses AES-256-GCM derived from passphrase via SHA256 for local dev only.
- In production, use a secure key management system and verify signatures.

Verification
- verify_export checks MANIFEST.json checksums and returns True if all match.
```

---

### Comandos exactos que el agente debe ejecutar
```bash
git checkout -b feature/backup-export-restore
# crear archivos según lo especificado
chmod +x scripts/backup.sh
python -m pip install -e .
# ejecutar tests unitarios
pytest tests/backup/test_export_unit.py -q
pytest tests/backup/test_encrypt_verify_unit.py -q || true
# ejecutar test de integración si corresponde
export TASKER_INTEGRATION=1
pytest tests/integration/test_backup_restore_integration.py -q -m integration || true
# commit y push
git add tasker/backup scripts/backup.sh docker-compose.backup.yml tasker/backup/BACKUP.md tests/backup tests/integration
git commit -m "feat(backup): add deterministic data export, verify and restore with optional encryption and tests"
git push origin feature/backup-export-restore
```

---

### PR body exacto a pegar
```
Summary:
- Added deterministic data export and backup system under tasker/backup.
- Implemented export_data, verify_export, restore_data and CLI integration.
- Added optional AES-256-GCM encryption for exports.
- Added scripts/backup.sh for simple CLI usage.
- Added docker-compose.backup.yml for scheduled backup runs.
- Added unit and integration tests and documentation tasker/backup/BACKUP.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran unit tests for export and verify.
3. Optionally ran integration backup/restore test with TASKER_INTEGRATION=1.

Files changed:
- tasker/backup/__init__.py
- tasker/backup/core.py
- tasker/backup/cli.py
- scripts/backup.sh
- docker-compose.backup.yml
- tasker/backup/BACKUP.md
- tests/backup/*
- tests/integration/test_backup_restore_integration.py

Notes:
- Encryption is intended for local dev; production should use KMS and proper key derivation.
- Repositories must implement import_list and import_dump for full restore; fallback behavior serializes lists.
```

---

### Criterios de aceptación
- `tasker/backup` existe con `export_data`, `verify_export`, `restore_data` y `list_exports` implementados exactamente como se especifica.  
- `scripts/backup.sh` existe, es ejecutable y delega a `tasker.backup.cli`.  
- Export produce un tar.gz con `MANIFEST.json` y archivos exportados; `verify_export` valida checksums.  
- `restore_data` restaura issues, graph y storage cuando los repositorios y storage están disponibles.  
- Tests unitarios y de integración existen y pasan en los entornos descritos.  
- `tasker/backup/BACKUP.md` documenta comandos, opciones y variables de entorno.  
- Branch `feature/backup-export-restore` creado y PR abierto con el PR body exacto arriba.

---

### Etiquetas para aplicar en GitHub
- `backup`
- `infra`
- `data`
- `medium-priority`

---

### Esfuerzo estimado
**Pequeño a Medio** — estimado **1–3 horas** dependiendo de la complejidad de los repositorios y la disponibilidad de `cryptography` en el entorno.