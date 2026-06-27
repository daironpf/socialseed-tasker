# src/socialseed_tasker/backup/core.py
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
    if hasattr(storage, "list_keys"):
        for k in storage.list_keys():
            v = storage.get(k)
            fname = f"storage_{k.replace('/', '_')}"
            with open(tmpdir / fname, "wb") as fh:
                fh.write(v if v is not None else b"")
            keys_meta.append({"key": k, "file": fname, "sha256": _sha256_bytes(v if v is not None else b"")})
    return keys_meta

def export_data(output_path: str, issue_repo=None, graph_repo=None, storage=None, include_storage: bool = True, encrypt: bool = False, passphrase: Optional[str] = None) -> str:
    tmpdir = Path(tempfile.mkdtemp(prefix="tasker-export-"))
    manifest = {"timestamp": time.time(), "version": "1.0.0", "files": []}
    issues_file = tmpdir / "issues.json"
    issues = []
    if issue_repo is not None and hasattr(issue_repo, "list_all"):
        issues = [i for i in issue_repo.list_all()]
    with open(issues_file, "w", encoding="utf-8") as fh:
        json.dump(issues, fh, indent=2, sort_keys=True)
    with open(issues_file, "rb") as fh:
        b = fh.read()
    manifest["files"].append({"path": "issues.json", "sha256": _sha256_bytes(b)})

    graph_file = tmpdir / "graph.json"
    graph = []
    if graph_repo is not None and hasattr(graph_repo, "dump"):
        graph = graph_repo.dump()
    with open(graph_file, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=2, sort_keys=True)
    with open(graph_file, "rb") as fh:
        b = fh.read()
    manifest["files"].append({"path": "graph.json", "sha256": _sha256_bytes(b)})

    storage_meta = []
    if include_storage and storage is not None:
        storage_meta = _collect_storage(storage, tmpdir)
        for m in storage_meta:
            manifest["files"].append({"path": m["file"], "sha256": m["sha256"]})

    _write_manifest(tmpdir, manifest)

    out_path = Path(output_path)
    with tarfile.open(out_path, "w:gz") as tar:
        for f in sorted(tmpdir.iterdir(), key=lambda p: p.name):
            tar.add(f, arcname=f.name)

    if encrypt:
        if not _CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography package required for encryption")
        if not passphrase:
            raise RuntimeError("passphrase required for encryption")
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
    tmpdir = Path(tempfile.mkdtemp(prefix="tasker-verify-"))
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
    tmpdir = Path(tempfile.mkdtemp(prefix="tasker-restore-"))
    with tarfile.open(file_path, "r:gz") as tar:
        tar.extractall(path=tmpdir)
    issues_file = tmpdir / "issues.json"
    if issues_file.exists() and issue_repo is not None and hasattr(issue_repo, "import_list"):
        data = json.loads(issues_file.read_text(encoding="utf-8"))
        issue_repo.import_list(data)
    graph_file = tmpdir / "graph.json"
    if graph_file.exists() and graph_repo is not None and hasattr(graph_repo, "import_dump"):
        data = json.loads(graph_file.read_text(encoding="utf-8"))
        graph_repo.import_dump(data)
    if storage is not None:
        for p in tmpdir.iterdir():
            if p.name.startswith("storage_"):
                key = p.name[len("storage_"):].replace("_", "/")
                storage.put(key, p.read_bytes())

def list_exports(directory: str) -> list[str]:
    return sorted([str(p) for p in Path(directory).glob("*.tar.gz*")])
