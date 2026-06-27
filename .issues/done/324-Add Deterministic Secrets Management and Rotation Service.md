### Issue 324 — Add Deterministic Secrets Management and Rotation Service

**Descripción breve**  
Agregar un servicio reproducible y determinista para **gestión de secretos** y rotación automática: almacenamiento cifrado de secretos, control de acceso por roles, rotación programada con políticas, auditoría inmutable, integración con `StoragePort` y contenedores, CLI y API para CRUD de secretos, pruebas unitarias e integración, y documentación clara. Todos los nombres de archivos, rutas, variables de entorno, comandos, firmas de funciones, comportamientos y el cuerpo del PR son explícitos para que un agente o desarrollador pueda implementar y verificar sin ambigüedades.

---

### Objetivos exactos
1. **Core secrets module** `tasker/secrets` que exponga:
   - `class SecretsStore` con métodos:
     - `put_secret(name: str, value: bytes, metadata: dict | None = None) -> None`
     - `get_secret(name: str) -> dict` (devuelve `{"value": bytes, "metadata": {...}}`)
     - `delete_secret(name: str) -> None`
     - `list_secrets(prefix: str = "") -> list[str]`
   - `class Rotator` que:
     - `schedule_rotation(name: str, interval_seconds: int, policy: dict) -> str` (devuelve `rotation_id`)
     - `run_rotation(rotation_id: str) -> dict` (ejecuta rotación determinista y devuelve resultado)
     - `list_rotations() -> list[dict]`
2. **Cifrado en reposo**:
   - Usar AES-256-GCM con clave derivada de `TASKER_SECRETS_MASTER_KEY` (hex) para cifrar secretos antes de persistir en `StoragePort`.
   - Implementar envoltorio en `tasker/secrets/crypto.py` con funciones `encrypt(plaintext: bytes) -> bytes` y `decrypt(ciphertext: bytes) -> bytes`.
3. **Auditoría inmutable**:
   - Cada operación `put`, `delete`, `rotate` escribe un registro JSON en `secrets:audit` (append) en `StoragePort` con campos: `action`, `name`, `actor`, `timestamp`, `rotation_id` (si aplica), `prev_hash`, `new_hash`.
   - Calcular `prev_hash` y `new_hash` como SHA256 del valor cifrado para detectar cambios.
4. **API HTTP**:
   - Endpoints bajo `/api/v1/secrets`:
     - `POST /api/v1/secrets` — crear/actualizar secreto (body: `{"name":"", "value":"base64", "metadata":{}}`) — requiere permiso `secrets.write`.
     - `GET /api/v1/secrets/{name}` — obtener metadata (no devuelve valor por defecto) — requiere `secrets.read`.
     - `GET /api/v1/secrets/{name}/value` — devuelve valor descifrado — requiere `secrets.read_value`.
     - `DELETE /api/v1/secrets/{name}` — borrar secreto — requiere `secrets.delete`.
     - `POST /api/v1/secrets/rotate` — programar rotación (body: `{"name":"", "interval_seconds":3600, "policy":{}}`) — requires `secrets.rotate`.
     - `POST /api/v1/secrets/rotate/run` — ejecutar rotación inmediata (body: `{"rotation_id":""}`).
     - `GET /api/v1/secrets/audit` — listar auditoría (admin).
5. **CLI** `tools/secrets/secretctl.py` con comandos:
   - `secretctl put --name <name> --file <path> [--meta '{"k":"v"}']`
   - `secretctl get --name <name> [--value]`
   - `secretctl delete --name <name>`
   - `secretctl rotate --name <name> --interval <seconds> --policy '{"strategy":"random","length":32}'`
   - `secretctl rotate-run --id <rotation_id>`
   - `secretctl audit --out <path>`
6. **Rotación determinista**:
   - Políticas soportadas: `random` (cryptographically secure RNG seeded from master key + name + timestamp for deterministic test runs when `TASKER_SECRETS_DETERMINISTIC=1`), `incremental` (append counter), `external` (call user-provided webhook).
   - `Rotator.run_rotation` debe produce el nuevo secreto, cifrarlo, persistirlo, y registrar auditoría.
7. **Integración con wiring**:
   - Añadir `secrets_store` y `secrets_rotator` al `Container` en `tasker/cli/wiring.py`.
8. **Pruebas**:
   - Unit tests:
     - `tests/secrets/test_crypto_unit.py` — cifrado/descifrado roundtrip.
     - `tests/secrets/test_store_unit.py` — put/get/delete/list y auditoría append.
     - `tests/secrets/test_rotator_unit.py` — schedule/run rotation deterministic.
   - Integration tests:
     - `tests/integration/test_secrets_api_integration.py` — arranca API, crea secreto, rota, verifica auditoría y que valor rotado es distinto.
9. **Documentación**:
   - `tasker/secrets/SECRETS.md` con ejemplos de uso, políticas de rotación, variables de entorno y recomendaciones de seguridad.
10. **Branch y PR**:
    - Crear branch `feature/secrets-rotation-management` y abrir PR con el PR body exacto provisto más abajo.

---

### Archivos a añadir o modificar (exactos)
- `tasker/secrets/__init__.py` **(nuevo)**
- `tasker/secrets/core.py` **(nuevo)**
- `tasker/secrets/crypto.py` **(nuevo)**
- `tasker/secrets/rotator.py` **(nuevo)**
- `tools/secrets/secretctl.py` **(nuevo, ejecutable)**
- `tasker/secrets/SECRETS.md` **(nuevo)**
- `tests/secrets/test_crypto_unit.py` **(nuevo)**
- `tests/secrets/test_store_unit.py` **(nuevo)**
- `tests/secrets/test_rotator_unit.py` **(nuevo)**
- `tests/integration/test_secrets_api_integration.py` **(nuevo, integration)**
- Modificar `tasker/cli/wiring.py` para exponer `secrets_store` y `secrets_rotator`.
- Modificar `tasker/api/app.py` para montar rutas `/api/v1/secrets`.

---

### Código exacto a añadir (fragmentos clave)

#### `tasker/secrets/__init__.py`
```python
# tasker/secrets/__init__.py
from .core import SecretsStore
from .crypto import encrypt, decrypt
from .rotator import Rotator

__all__ = ["SecretsStore", "encrypt", "decrypt", "Rotator"]
```

#### `tasker/secrets/crypto.py`
```python
# tasker/secrets/crypto.py
from __future__ import annotations
import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MASTER_KEY_HEX = os.getenv("TASKER_SECRETS_MASTER_KEY", "")
if not MASTER_KEY_HEX:
    # For safety in tests/dev, allow a default but warn in docs
    MASTER_KEY = hashlib.sha256(b"default-tasker-secrets-key").digest()
else:
    MASTER_KEY = bytes.fromhex(MASTER_KEY_HEX)

def _derive_nonce(suffix: bytes) -> bytes:
    # deterministic 12-byte nonce derived from suffix (for tests); in prod use random nonce stored with ciphertext
    h = hashlib.sha256(suffix).digest()
    return h[:12]

def encrypt(plaintext: bytes, associated_data: bytes | None = None) -> bytes:
    aes = AESGCM(MASTER_KEY)
    nonce = os.urandom(12) if os.getenv("TASKER_SECRETS_USE_RANDOM_NONCE","1") == "1" else _derive_nonce(plaintext)
    ct = aes.encrypt(nonce, plaintext, associated_data)
    # store nonce + ct
    return nonce + ct

def decrypt(ciphertext: bytes, associated_data: bytes | None = None) -> bytes:
    aes = AESGCM(MASTER_KEY)
    nonce = ciphertext[:12]
    ct = ciphertext[12:]
    return aes.decrypt(nonce, ct, associated_data)
```

#### `tasker/secrets/core.py`
```python
# tasker/secrets/core.py
from __future__ import annotations
import json
import time
import base64
import hashlib
from typing import Optional, Dict, Any, List
from tasker.application.ports import StoragePort
from .crypto import encrypt, decrypt

AUDIT_KEY = "secrets:audit"
SECRETS_PREFIX = "secrets:"

def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

class SecretsStore:
    def __init__(self, storage: StoragePort):
        self.storage = storage

    def _key(self, name: str) -> str:
        return SECRETS_PREFIX + name

    def put_secret(self, name: str, value: bytes, metadata: Optional[Dict[str,Any]] = None, actor: Optional[str] = None) -> None:
        enc = encrypt(value)
        meta = metadata or {}
        entry = {"value": base64.b64encode(enc).decode("utf-8"), "metadata": meta, "ts": int(time.time())}
        self.storage.put(self._key(name), json.dumps(entry).encode("utf-8"))
        # audit
        self._write_audit({"action":"put","name":name,"actor": actor or "cli","timestamp": int(time.time()), "new_hash": _hash_bytes(enc)})

    def get_secret(self, name: str, reveal: bool = False) -> Dict[str,Any]:
        raw = self.storage.get(self._key(name))
        if not raw:
            raise KeyError("secret not found")
        entry = json.loads(raw.decode("utf-8"))
        if reveal:
            enc = base64.b64decode(entry["value"].encode("utf-8"))
            val = decrypt(enc)
            return {"value": val, "metadata": entry.get("metadata", {}), "ts": entry.get("ts")}
        return {"metadata": entry.get("metadata", {}), "ts": entry.get("ts")}

    def delete_secret(self, name: str, actor: Optional[str] = None) -> None:
        # record prev hash
        raw = self.storage.get(self._key(name))
        prev_hash = None
        if raw:
            entry = json.loads(raw.decode("utf-8"))
            prev_hash = _hash_bytes(base64.b64decode(entry["value"].encode("utf-8")))
        self.storage.delete(self._key(name))
        self._write_audit({"action":"delete","name":name,"actor": actor or "cli","timestamp": int(time.time()), "prev_hash": prev_hash})

    def list_secrets(self, prefix: str = "") -> List[str]:
        if not hasattr(self.storage, "list_keys"):
            # best-effort: try known keys if storage supports get of index
            return []
        keys = self.storage.list_keys()
        out = []
        for k in keys:
            if k.startswith(SECRETS_PREFIX):
                name = k[len(SECRETS_PREFIX):]
                if prefix and not name.startswith(prefix):
                    continue
                out.append(name)
        return sorted(out)

    def _write_audit(self, audit: Dict[str,Any]) -> None:
        raw = self.storage.get(AUDIT_KEY) or b"[]"
        try:
            arr = json.loads(raw.decode("utf-8")) if raw else []
        except Exception:
            arr = []
        arr.append(audit)
        self.storage.put(AUDIT_KEY, json.dumps(arr).encode("utf-8"))
```

#### `tasker/secrets/rotator.py`
```python
# tasker/secrets/rotator.py
from __future__ import annotations
import time
import json
import hmac
import hashlib
import os
import base64
from typing import Dict, Any, Optional, List
from tasker.application.ports import StoragePort
from .core import SecretsStore
from .crypto import encrypt

ROTATIONS_KEY = "secrets:rotations"
DETERMINISTIC = os.getenv("TASKER_SECRETS_DETERMINISTIC", "0") == "1"

def _seed_master(name: str, ts: int) -> bytes:
    # deterministic seed derived from master key and name+ts
    mk = os.getenv("TASKER_SECRETS_MASTER_KEY", "")
    data = f"{mk}:{name}:{ts}".encode("utf-8")
    return hashlib.sha256(data).digest()

class Rotator:
    def __init__(self, storage: StoragePort, secrets_store: SecretsStore):
        self.storage = storage
        self.secrets = secrets_store

    def _load_rotations(self) -> Dict[str, Dict]:
        raw = self.storage.get(ROTATIONS_KEY) or b"{}"
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return {}

    def _persist_rotations(self, data: Dict[str, Dict]) -> None:
        self.storage.put(ROTATIONS_KEY, json.dumps(data).encode("utf-8"))

    def schedule_rotation(self, name: str, interval_seconds: int, policy: Dict[str,Any]) -> str:
        rotations = self._load_rotations()
        rid = f"rot-{int(time.time()*1000)}"
        rotations[rid] = {"id": rid, "name": name, "interval": interval_seconds, "policy": policy, "created_at": int(time.time())}
        self._persist_rotations(rotations)
        return rid

    def list_rotations(self) -> List[Dict[str,Any]]:
        return list(self._load_rotations().values())

    def run_rotation(self, rotation_id: str) -> Dict[str,Any]:
        rotations = self._load_rotations()
        if rotation_id not in rotations:
            raise KeyError("rotation not found")
        r = rotations[rotation_id]
        name = r["name"]
        policy = r.get("policy", {})
        strategy = policy.get("strategy", "random")
        length = int(policy.get("length", 32))
        ts = int(time.time())
        if strategy == "random":
            if DETERMINISTIC:
                seed = _seed_master(name, ts)
                # deterministic bytes from HMAC-SHA256
                new_bytes = hmac.new(seed, b"rotate", hashlib.sha256).digest()[:length]
            else:
                new_bytes = os.urandom(length)
        elif strategy == "incremental":
            # derive from timestamp for deterministic tests
            new_bytes = str(ts).encode("utf-8")[:length].ljust(length, b'0')
        elif strategy == "external":
            # call webhook if provided
            webhook = policy.get("webhook")
            if not webhook:
                raise ValueError("external strategy requires webhook")
            import requests
            resp = requests.post(webhook, json={"name": name, "rotation_id": rotation_id}, timeout=10)
            new_bytes = resp.content[:length]
        else:
            raise ValueError("unknown strategy")
        # persist new secret
        self.secrets.put_secret(name, new_bytes, metadata={"rotated_at": ts}, actor="rotator")
        # record rotation result
        result = {"rotation_id": rotation_id, "name": name, "timestamp": ts, "strategy": strategy, "length": length}
        # append to audit via secrets_store
        return result
```

#### `tools/secrets/secretctl.py`
```python
#!/usr/bin/env python3
# tools/secrets/secretctl.py
from __future__ import annotations
import argparse
import base64
import json
import sys
from tasker.cli.wiring import build_default_container

def main(argv=None):
    p = argparse.ArgumentParser(prog="secretctl")
    sub = p.add_subparsers(dest="cmd")
    put = sub.add_parser("put")
    put.add_argument("--name", required=True)
    put.add_argument("--file", required=True)
    put.add_argument("--meta", default=None)
    get = sub.add_parser("get")
    get.add_argument("--name", required=True)
    get.add_argument("--value", action="store_true")
    delete = sub.add_parser("delete")
    delete.add_argument("--name", required=True)
    rotate = sub.add_parser("rotate")
    rotate.add_argument("--name", required=True)
    rotate.add_argument("--interval", type=int, required=True)
    rotate.add_argument("--policy", required=True)
    rotate_run = sub.add_parser("rotate-run")
    rotate_run.add_argument("--id", required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--out", required=True)
    args = p.parse_args(argv)
    container = build_default_container()
    ss = container.secrets_store
    rot = container.secrets_rotator
    if args.cmd == "put":
        with open(args.file, "rb") as fh:
            b = fh.read()
        meta = json.loads(args.meta) if args.meta else {}
        ss.put_secret(args.name, b, metadata=meta, actor="cli")
        print("ok")
    elif args.cmd == "get":
        if args.value:
            res = ss.get_secret(args.name, reveal=True)
            sys.stdout.buffer.write(res["value"])
        else:
            res = ss.get_secret(args.name, reveal=False)
            print(json.dumps(res["metadata"], indent=2))
    elif args.cmd == "delete":
        ss.delete_secret(args.name, actor="cli")
        print("ok")
    elif args.cmd == "rotate":
        policy = json.loads(args.policy)
        rid = rot.schedule_rotation(args.name, args.interval, policy)
        print(rid)
    elif args.cmd == "rotate-run":
        res = rot.run_rotation(args.id)
        print(json.dumps(res, indent=2))
    elif args.cmd == "audit":
        raw = container.storage.get("secrets:audit") or b"[]"
        with open(args.out, "wb") as fh:
            fh.write(raw)
        print("wrote", args.out)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
```

> Hacer `chmod +x tools/secrets/secretctl.py`.

---

### API snippets to añadir en `tasker/api/app.py` (exact)

**Importar y montar rutas** (añadir en imports):
```python
from tasker.cli.wiring import build_api_container
from fastapi import Body
import base64
```

**Endpoints** (insertar en la sección de rutas administrativas):
```python
@app.post("/api/v1/secrets")
def api_put_secret(req: dict = Body(...), user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "secrets.write"):
        raise HTTPException(status_code=403, detail="forbidden")
    name = req.get("name")
    val_b64 = req.get("value")
    meta = req.get("metadata", {})
    if not name or not val_b64:
        raise HTTPException(status_code=400, detail="missing name or value")
    val = base64.b64decode(val_b64.encode("utf-8"))
    container.secrets_store.put_secret(name, val, metadata=meta, actor=user_id)
    return {"status":"ok"}

@app.get("/api/v1/secrets/{name}")
def api_get_secret_meta(name: str, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "secrets.read"):
        raise HTTPException(status_code=403, detail="forbidden")
    try:
        res = container.secrets_store.get_secret(name, reveal=False)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")
    return {"status":"ok","metadata": res["metadata"], "ts": res["ts"]}

@app.get("/api/v1/secrets/{name}/value")
def api_get_secret_value(name: str, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "secrets.read_value"):
        raise HTTPException(status_code=403, detail="forbidden")
    try:
        res = container.secrets_store.get_secret(name, reveal=True)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")
    return {"status":"ok","value": base64.b64encode(res["value"]).decode("utf-8")}

@app.delete("/api/v1/secrets/{name}")
def api_delete_secret(name: str, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "secrets.delete"):
        raise HTTPException(status_code=403, detail="forbidden")
    container.secrets_store.delete_secret(name, actor=user_id)
    return {"status":"ok"}

@app.post("/api/v1/secrets/rotate")
def api_schedule_rotate(req: dict = Body(...), user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "secrets.rotate"):
        raise HTTPException(status_code=403, detail="forbidden")
    name = req.get("name")
    interval = int(req.get("interval_seconds", 3600))
    policy = req.get("policy", {})
    rid = container.secrets_rotator.schedule_rotation(name, interval, policy)
    return {"status":"ok","rotation_id": rid}

@app.post("/api/v1/secrets/rotate/run")
def api_run_rotate(req: dict = Body(...), user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "secrets.rotate"):
        raise HTTPException(status_code=403, detail="forbidden")
    rid = req.get("rotation_id")
    if not rid:
        raise HTTPException(status_code=400, detail="missing rotation_id")
    res = container.secrets_rotator.run_rotation(rid)
    return {"status":"ok","result": res}

@app.get("/api/v1/secrets/audit")
def api_get_audit(user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    raw = container.storage.get("secrets:audit") or b"[]"
    import json
    arr = json.loads(raw.decode("utf-8")) if raw else []
    return {"status":"ok","audit": arr}
```

---

### Wiring changes for `tasker/cli/wiring.py` (exact excerpt)
Insert after storage creation:

```python
from tasker.secrets.core import SecretsStore
from tasker.secrets.rotator import Rotator

secrets_store = SecretsStore(storage)
secrets_rotator = Rotator(storage=storage, secrets_store=secrets_store)

# include in Container return
return Container(
    # existing attributes...
    storage=storage,
    secrets_store=secrets_store,
    secrets_rotator=secrets_rotator,
    # other attributes...
)
```

---

### Tests exact content

#### `tests/secrets/test_crypto_unit.py`
```python
# tests/secrets/test_crypto_unit.py
from tasker.secrets.crypto import encrypt, decrypt
def test_encrypt_decrypt_roundtrip():
    b = b"supersecret"
    c = encrypt(b)
    p = decrypt(c)
    assert p == b
```

#### `tests/secrets/test_store_unit.py`
```python
# tests/secrets/test_store_unit.py
from tasker.secrets.core import SecretsStore
from tasker.infrastructure.memory_storage import MemoryStorage
def test_put_get_delete_list_and_audit(tmp_path):
    s = MemoryStorage()
    ss = SecretsStore(s)
    ss.put_secret("k1", b"v1", metadata={"env":"dev"}, actor="tester")
    meta = ss.get_secret("k1", reveal=False)
    assert meta["metadata"]["env"] == "dev"
    names = ss.list_secrets()
    assert "k1" in names
    ss.delete_secret("k1", actor="tester")
    # audit exists
    raw = s.get("secrets:audit")
    assert raw is not None
```

#### `tests/secrets/test_rotator_unit.py`
```python
# tests/secrets/test_rotator_unit.py
import os
from tasker.secrets.core import SecretsStore
from tasker.secrets.rotator import Rotator
from tasker.infrastructure.memory_storage import MemoryStorage
def test_schedule_and_run_rotation(tmp_path, monkeypatch):
    os.environ["TASKER_SECRETS_DETERMINISTIC"] = "1"
    s = MemoryStorage()
    ss = SecretsStore(s)
    ss.put_secret("krot", b"old", actor="tester")
    rot = Rotator(storage=s, secrets_store=ss)
    rid = rot.schedule_rotation("krot", 10, {"strategy":"random","length":16})
    res = rot.run_rotation(rid)
    assert res["rotation_id"] == rid
    # new secret exists
    val = ss.get_secret("krot", reveal=True)
    assert val["value"] != b"old"
```

#### `tests/integration/test_secrets_api_integration.py`
```python
# tests/integration/test_secrets_api_integration.py
import os, time, base64, requests, pytest
pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_api_put_rotate_and_audit():
    _skip_if_not_integration()
    base = "http://localhost:8000"
    # put secret
    val = base64.b64encode(b"initval").decode("utf-8")
    r = requests.post(f"{base}/api/v1/secrets", json={"name":"itest","value": val, "metadata": {"owner":"ci"}}, timeout=5, headers={"Authorization":"Bearer admin"})
    assert r.status_code == 200
    # schedule rotation
    r2 = requests.post(f"{base}/api/v1/secrets/rotate", json={"name":"itest","interval_seconds":1,"policy":{"strategy":"random","length":8}}, timeout=5, headers={"Authorization":"Bearer admin"})
    assert r2.status_code == 200
    rid = r2.json().get("rotation_id")
    # run rotation
    r3 = requests.post(f"{base}/api/v1/secrets/rotate/run", json={"rotation_id": rid}, timeout=5, headers={"Authorization":"Bearer admin"})
    assert r3.status_code == 200
    # audit contains entries
    r4 = requests.get(f"{base}/api/v1/secrets/audit", timeout=5, headers={"Authorization":"Bearer admin"})
    assert r4.status_code == 200
    assert len(r4.json().get("audit", [])) >= 2
```

---

### Documentación exacta

Create `tasker/secrets/SECRETS.md` with the exact content below.

```
Secrets Management and Rotation Guide

Overview
- Secrets are stored encrypted using AES-256-GCM derived from TASKER_SECRETS_MASTER_KEY.
- SecretsStore persists encrypted blobs in StoragePort under keys secrets:<name>.
- Rotator schedules and runs deterministic rotations for tests when TASKER_SECRETS_DETERMINISTIC=1.

Environment variables
- TASKER_SECRETS_MASTER_KEY (hex) required in production.
- TASKER_SECRETS_DETERMINISTIC=1 to enable deterministic rotation for tests.
- TASKER_SECRETS_USE_RANDOM_NONCE=0 to use deterministic nonce (dev only).

API usage
- Create secret:
  POST /api/v1/secrets
  { "name":"db/password", "value":"<base64>", "metadata": {"env":"prod"} }
- Read metadata:
  GET /api/v1/secrets/db/password
- Read value:
  GET /api/v1/secrets/db/password/value
- Schedule rotation:
  POST /api/v1/secrets/rotate { "name":"db/password", "interval_seconds":3600, "policy": {"strategy":"random","length":32} }

CLI
- Put secret:
  tools/secrets/secretctl.py put --name db/password --file ./pw.bin
- Get secret value:
  tools/secrets/secretctl.py get --name db/password --value

Security notes
- Never commit TASKER_SECRETS_MASTER_KEY to source control.
- In production, use a secure KMS and set TASKER_SECRETS_MASTER_KEY from KMS-derived key.
- Deterministic modes are for tests only.
```

---

### Comandos exactos que el agente debe ejecutar
```bash
git checkout -b feature/secrets-rotation-management
# create files as specified
chmod +x tools/secrets/secretctl.py
python -m pip install -e .
# run unit tests
pytest tests/secrets/test_crypto_unit.py -q
pytest tests/secrets/test_store_unit.py -q
pytest tests/secrets/test_rotator_unit.py -q
# optional integration test (requires TASKER_INTEGRATION=1 and API running)
export TASKER_INTEGRATION=1
pytest tests/integration/test_secrets_api_integration.py -q -m integration || true
# commit and push
git add tasker/secrets tools/secrets tests/secrets tests/integration
git commit -m "feat(secrets): add deterministic secrets store, AES-256-GCM encryption, rotator, API and CLI"
git push origin feature/secrets-rotation-management
```

---

### PR body exacto a pegar

```
Summary:
- Added deterministic Secrets Management and Rotation service under tasker/secrets.
- Implemented SecretsStore with AES-256-GCM encryption (tasker/secrets/crypto.py) and audit logs.
- Implemented Rotator to schedule and run deterministic rotations for tests and secure rotations in production.
- Added HTTP API endpoints for CRUD, rotation scheduling and audit retrieval.
- Added CLI tools tools/secrets/secretctl.py for local operations.
- Added unit and integration tests and documentation tasker/secrets/SECRETS.md.

Verification steps executed by this agent:
1. Installed package in editable mode.
2. Ran unit tests for crypto, store and rotator.
3. Optionally ran integration API test with TASKER_INTEGRATION=1.

Files changed:
- tasker/secrets/*
- tools/secrets/secretctl.py
- tests/secrets/*
- tests/integration/test_secrets_api_integration.py

Notes:
- Use TASKER_SECRETS_MASTER_KEY from a secure KMS in production.
- Deterministic rotation mode (TASKER_SECRETS_DETERMINISTIC=1) is intended for CI and tests only.
```

---

### Criterios de aceptación
- `tasker/secrets` existe con `core.py`, `crypto.py`, `rotator.py` y `SECRETS.md`.
- `SecretsStore` implementa `put_secret`, `get_secret`, `delete_secret`, `list_secrets` y escribe auditoría en `secrets:audit`.
- `crypto.encrypt` y `crypto.decrypt` realizan AES-256-GCM con `TASKER_SECRETS_MASTER_KEY`.
- `Rotator` soporta `random`, `incremental` y `external` y `run_rotation` persiste el nuevo secreto y registra auditoría.
- API endpoints `/api/v1/secrets/*` existen y respetan permisos RBAC.
- CLI `tools/secrets/secretctl.py` existe y funciona según especificación.
- Tests unitarios e integración existen y pasan en los entornos descritos.
- Branch `feature/secrets-rotation-management` creado y PR abierto con el PR body exacto arriba.

---

### Labels to apply on GitHub
- `security`
- `secrets`
- `infra`
- `medium-priority`

---

### Estimación de esfuerzo
**Medio (M)** — esperado **2–4 horas** dependiendo de la disponibilidad de `cryptography` y del entorno de CI.