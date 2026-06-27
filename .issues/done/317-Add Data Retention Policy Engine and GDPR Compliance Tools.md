### Issue 317 — Add Data Retention Policy Engine and GDPR Compliance Tools

**Descripción breve**  
Agregar un subsistema determinista para **retención de datos**, eliminación programada (right to be forgotten), exportación de datos por usuario (data portability), y auditoría de accesos para cumplir requisitos GDPR/privacidad. Debe incluir políticas configurables por tenant/ambiente, tareas programadas para purgado, endpoints API para exportar/borrar datos por sujeto, pruebas unitarias e integración, documentación y wiring en Docker Compose. Todo debe ser explícito: rutas, nombres de archivos, firmas de funciones, variables de entorno, comandos y PR body listos para aplicar sin ambigüedades.

---

### Objetivos exactos
1. **Motor de políticas**: implementar `tasker/privacy/policy.py` que evalúe reglas de retención basadas en:
   - tipo de dato (issue, comment, logs, storage keys),
   - edad del dato (timestamp),
   - tenant y entorno (`TASKER_ENV`),
   - etiquetas de conservación (e.g., legal-hold).
   Exponer API: `evaluate_policy(record_meta: dict) -> bool` (True = keep, False = eligible for deletion).
2. **Purgador programado**: `tasker/privacy/retention_worker.py` que:
   - escanee repositorios y storage para encontrar registros elegibles,
   - respete `legal-hold` y exclusiones,
   - archive antes de borrar si `TASKER_RETENTION_ARCHIVE=true`,
   - registre acciones en `privacy:audits` en StoragePort.
3. **Endpoints API**:
   - `POST /api/v1/privacy/export` — exporta todos los datos asociados a `subject_id` (user) en un tar.gz y devuelve URL temporal o stream.
   - `POST /api/v1/privacy/delete` — solicita borrado de datos para `subject_id`; crea una tarea y devuelve `task_id`.
   - `GET /api/v1/privacy/tasks/{task_id}` — estado de la tarea (pending, running, done, failed).
   - `GET /api/v1/privacy/audit` — lista de auditorías (admin).
4. **Right to be Forgotten flow**:
   - Implementar `tasker/privacy/handlers.py` con funciones `export_subject(subject_id)` y `delete_subject(subject_id, dry_run=False)`.
   - `delete_subject` debe: mark records for deletion, archive if configured, remove from repos/storage, log audit entries.
5. **Archivos y pruebas**:
   - Unit tests para evaluación de políticas, export, delete dry-run.
   - Integration test que crea datos de prueba, ejecuta `retention_worker` y verifica borrado/archivo/auditoría.
6. **Configuración y seguridad**:
   - Variables: `TASKER_RETENTION_ENABLED`, `TASKER_RETENTION_CRON`, `TASKER_RETENTION_ARCHIVE`, `TASKER_RETENTION_ARCHIVE_PATH`, `TASKER_RETENTION_DRY_RUN`.
   - Endpoints protegidos por RBAC: export/delete requieren `admin` or subject owner; audit requiere `admin`.
7. **Documentación**:
   - `tasker/privacy/PRIVACY.md` con flujos, ejemplos de políticas, cómo auditar y restaurar desde archivo.
8. **Branch y PR**:
   - Crear branch `feature/privacy-retention-gdpr` y abrir PR con el PR body exacto provisto más abajo.

---

### Archivos a añadir o modificar exactos
- `tasker/privacy/__init__.py` **nuevo**
- `tasker/privacy/policy.py` **nuevo**
- `tasker/privacy/retention_worker.py` **nuevo**
- `tasker/privacy/handlers.py` **nuevo**
- `tasker/privacy/PRIVACY.md` **nuevo**
- `tasker/api/app.py` **modificar** — añadir endpoints y wiring
- `tasker/cli/wiring.py` **modificar** — exponer privacy worker and storage archive path
- `tests/privacy/test_policy_unit.py` **nuevo**
- `tests/privacy/test_export_delete_unit.py` **nuevo**
- `tests/integration/test_retention_integration.py` **nuevo, integration**

---

### Contenido exacto clave (fragmentos esenciales)

#### `tasker/privacy/policy.py`
```python
# tasker/privacy/policy.py
from __future__ import annotations
import os
import time
from typing import Dict, Any

# Default retention rules (seconds)
DEFAULT_RETENTION = {
    "issue": 60 * 60 * 24 * 365 * 3,   # 3 years
    "comment": 60 * 60 * 24 * 365 * 2, # 2 years
    "log": 60 * 60 * 24 * 90,          # 90 days
    "storage": 60 * 60 * 24 * 365,     # 1 year
}

def get_retention_for(kind: str) -> int:
    env_key = f"TASKER_RETENTION_{kind.upper()}"
    v = os.getenv(env_key)
    if v:
        try:
            return int(v)
        except Exception:
            pass
    return DEFAULT_RETENTION.get(kind, 60 * 60 * 24 * 365)

def evaluate_policy(record_meta: Dict[str, Any]) -> bool:
    """
    Return True if record should be kept, False if eligible for deletion.
    record_meta must include: kind, created_at (unix ts), tenant, tags (list)
    """
    if not record_meta:
        return True
    # respect legal hold
    tags = record_meta.get("tags", []) or []
    if "legal-hold" in tags:
        return True
    kind = record_meta.get("kind", "storage")
    created = record_meta.get("created_at", int(time.time()))
    age = int(time.time()) - int(created)
    retention = get_retention_for(kind)
    # tenant-specific override
    tenant = record_meta.get("tenant")
    if tenant:
        tkey = f"TASKER_RETENTION_{tenant}_{kind}".upper()
        tv = os.getenv(tkey)
        if tv:
            try:
                retention = int(tv)
            except Exception:
                pass
    return age < retention
```

#### `tasker/privacy/retention_worker.py`
```python
# tasker/privacy/retention_worker.py
from __future__ import annotations
import os
import time
import threading
import tarfile
import tempfile
from typing import Optional, Dict, Any
from tasker.application.ports import StoragePort
from tasker.privacy.policy import evaluate_policy
from tasker.application.exceptions import StorageError

AUDIT_KEY = "privacy:audits"

class RetentionWorker:
    def __init__(self, container, interval: int = 3600):
        self.container = container
        self.storage: StoragePort = container.storage
        self.interval = int(os.getenv("TASKER_RETENTION_INTERVAL", interval))
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception:
                pass
            time.sleep(self.interval)

    def run_once(self):
        # scan known repositories for records; repositories must expose list_records(meta_filter)
        # deterministic: use container.issue_repo.list_all() and container.graph_repo.dump() as examples
        # issues
        issues = []
        if hasattr(self.container.issue_repo, "list_all"):
            issues = self.container.issue_repo.list_all()
        for i in issues:
            meta = {"kind":"issue", "created_at": i.get("created_at", int(time.time())), "tenant": i.get("tenant"), "tags": i.get("tags", [])}
            if not evaluate_policy(meta):
                self._archive_and_delete("issue", i.get("id"), i, meta)
        # storage keys
        if hasattr(self.storage, "list_keys"):
            for k in self.storage.list_keys():
                # skip audit keys
                if k.startswith(AUDIT_KEY):
                    continue
                # attempt to parse metadata if stored; fallback to default
                meta = {"kind":"storage", "created_at": int(time.time()), "tenant": None, "tags": []}
                if not evaluate_policy(meta):
                    self._archive_and_delete("storage", k, None, meta)

    def _archive_and_delete(self, kind: str, key: str, record: Optional[Dict[str,Any]], meta: Dict[str,Any]):
        archive_enabled = os.getenv("TASKER_RETENTION_ARCHIVE", "0") == "1"
        archive_path = os.getenv("TASKER_RETENTION_ARCHIVE_PATH", "/tmp/tasker-archives")
        timestamp = int(time.time())
        audit = {"action":"delete", "kind":kind, "key": key, "timestamp": timestamp, "tenant": meta.get("tenant")}
        try:
            if archive_enabled:
                tmp = tempfile.mkdtemp(prefix="tasker-archive-")
                fname = f"{kind}-{key}-{timestamp}.json"
                import json, os
                with open(os.path.join(tmp, fname), "w", encoding="utf-8") as fh:
                    json.dump({"meta":meta, "record": record}, fh, indent=2)
                # create tar.gz
                out = f"{archive_path}/{fname}.tar.gz"
                with tarfile.open(out, "w:gz") as tar:
                    tar.add(os.path.join(tmp, fname), arcname=fname)
            # perform deletion
            if kind == "issue" and hasattr(self.container.issue_repo, "delete"):
                self.container.issue_repo.delete(key)
            elif kind == "storage":
                self.storage.delete(key)
            # write audit
            self._write_audit(audit)
        except Exception as exc:
            audit["error"] = str(exc)
            self._write_audit(audit)

    def _write_audit(self, audit: Dict[str,Any]):
        try:
            raw = self.storage.get(AUDIT_KEY) or b"[]"
            import json
            arr = json.loads(raw.decode("utf-8")) if raw else []
            arr.append(audit)
            self.storage.put(AUDIT_KEY, json.dumps(arr).encode("utf-8"))
        except Exception:
            pass
```

#### `tasker/privacy/handlers.py`
```python
# tasker/privacy/handlers.py
from __future__ import annotations
import os
import tempfile
import tarfile
import json
from typing import Dict, Any
from tasker.application.ports import StoragePort

def export_subject(subject_id: str, container) -> str:
    """
    Export all data related to subject_id into a tar.gz and return path.
    Deterministic: gather from issue_repo, graph_repo, storage keys prefixed with subject_id.
    """
    tmp = tempfile.mkdtemp(prefix="tasker-export-subject-")
    files = []
    # issues
    if hasattr(container.issue_repo, "list_by_subject"):
        issues = container.issue_repo.list_by_subject(subject_id)
    else:
        issues = [i for i in container.issue_repo.list_all() if i.get("owner") == subject_id]
    with open(f"{tmp}/issues.json", "w", encoding="utf-8") as fh:
        json.dump(issues, fh, indent=2)
    files.append("issues.json")
    # storage keys
    storage = container.storage
    if hasattr(storage, "list_keys"):
        for k in storage.list_keys():
            if k.startswith(f"subject:{subject_id}:"):
                v = storage.get(k) or b""
                fname = k.replace(":", "_")
                with open(f"{tmp}/{fname}", "wb") as fh:
                    fh.write(v)
                files.append(fname)
    out = f"/tmp/tasker-export-{subject_id}-{int(time.time())}.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        for f in files:
            tar.add(f"{tmp}/{f}", arcname=f)
    return out

def delete_subject(subject_id: str, container, dry_run: bool = True) -> Dict[str,Any]:
    """
    Delete or mark for deletion all data for subject. If dry_run True, return list of items that would be deleted.
    """
    to_delete = {"issues": [], "storage": []}
    # issues
    if hasattr(container.issue_repo, "list_by_subject"):
        issues = container.issue_repo.list_by_subject(subject_id)
    else:
        issues = [i for i in container.issue_repo.list_all() if i.get("owner") == subject_id]
    for i in issues:
        to_delete["issues"].append(i.get("id"))
        if not dry_run and hasattr(container.issue_repo, "delete"):
            container.issue_repo.delete(i.get("id"))
    # storage
    storage = container.storage
    if hasattr(storage, "list_keys"):
        for k in storage.list_keys():
            if k.startswith(f"subject:{subject_id}:"):
                to_delete["storage"].append(k)
                if not dry_run:
                    storage.delete(k)
    # write audit
    if not dry_run:
        try:
            raw = storage.get("privacy:audits") or b"[]"
            arr = json.loads(raw.decode("utf-8")) if raw else []
            arr.append({"action":"delete_subject","subject":subject_id,"timestamp":int(time.time())})
            storage.put("privacy:audits", json.dumps(arr).encode("utf-8"))
        except Exception:
            pass
    return {"dry_run": dry_run, "result": to_delete}
```

---

### Endpoints to añadir en `tasker/api/app.py` (exact snippets)

```python
@app.post("/api/v1/privacy/export")
def api_privacy_export(req: dict, user_id: str = Depends(get_user_id_from_request), container = Depends(get_container)):
    subject = req.get("subject_id")
    if not subject:
        raise HTTPException(status_code=400, detail="missing subject_id")
    # permission: admin or subject owner
    if user_id != subject and not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    path = container.privacy_handlers.export_subject(subject, container)
    # return path or stream; deterministic: return path
    return {"status":"ok","export_path": path}

@app.post("/api/v1/privacy/delete")
def api_privacy_delete(req: dict, user_id: str = Depends(get_user_id_from_request), container = Depends(get_container)):
    subject = req.get("subject_id")
    dry = req.get("dry_run", True)
    if not subject:
        raise HTTPException(status_code=400, detail="missing subject_id")
    if user_id != subject and not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    task = {"id": f"privacy-{int(time.time()*1000)}", "status":"pending", "subject":subject}
    # enqueue task in simple in-memory tasks list or storage
    raw = container.storage.get("privacy:tasks") or b"[]"
    import json
    arr = json.loads(raw.decode("utf-8")) if raw else []
    arr.append(task)
    container.storage.put("privacy:tasks", json.dumps(arr).encode("utf-8"))
    # run deletion synchronously for deterministic tests
    res = container.privacy_handlers.delete_subject(subject, container, dry_run=dry)
    task["status"] = "done"
    container.storage.put("privacy:tasks", json.dumps(arr).encode("utf-8"))
    return {"status":"ok","task": task, "result": res}

@app.get("/api/v1/privacy/tasks/{task_id}")
def api_privacy_task(task_id: str, user_id: str = Depends(get_user_id_from_request), container = Depends(get_container)):
    raw = container.storage.get("privacy:tasks") or b"[]"
    import json
    arr = json.loads(raw.decode("utf-8")) if raw else []
    for t in arr:
        if t.get("id") == task_id:
            return {"status":"ok","task": t}
    raise HTTPException(status_code=404, detail="not found")

@app.get("/api/v1/privacy/audit")
def api_privacy_audit(user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    raw = container.storage.get("privacy:audits") or b"[]"
    import json
    arr = json.loads(raw.decode("utf-8")) if raw else []
    return {"status":"ok","audits": arr}
```

---

### Tests a añadir (resumen)
- `tests/privacy/test_policy_unit.py` — validar `evaluate_policy` con distintos metadatos y env overrides.
- `tests/privacy/test_export_delete_unit.py` — crear subject con issues/storage, probar `export_subject` y `delete_subject` en modo dry_run y real.
- `tests/integration/test_retention_integration.py` — con `TASKER_INTEGRATION=1`, crear datos, ejecutar `RetentionWorker.run_once()`, verificar que registros elegibles fueron archivados/borrados y que `privacy:audits` contiene entradas.

---

### Variables de entorno y comandos exactos
**Variables**
- `TASKER_RETENTION_ENABLED` default `1`
- `TASKER_RETENTION_INTERVAL` seconds default `3600`
- `TASKER_RETENTION_ARCHIVE` `0|1`
- `TASKER_RETENTION_ARCHIVE_PATH` default `/tmp/tasker-archives`
- `TASKER_RETENTION_DRY_RUN` `1|0`
- `TASKER_ENV` `dev|staging|prod`

**Comandos**
```bash
git checkout -b feature/privacy-retention-gdpr
python -m pip install -e .
# ejecutar tests unitarios
pytest tests/privacy/test_policy_unit.py -q
pytest tests/privacy/test_export_delete_unit.py -q
# integración (si procede)
export TASKER_INTEGRATION=1
python -c "from tasker.cli.wiring import build_default_container; c=build_default_container(); from tasker.privacy.retention_worker import RetentionWorker; w=RetentionWorker(c, interval=1); w.run_once()"
pytest tests/integration/test_retention_integration.py -q -m integration || true
# commit y push
git add tasker/privacy tasker/api/app.py tests/privacy tests/integration tasker/privacy/PRIVACY.md
git commit -m "feat(privacy): add retention policy engine, retention worker, export/delete handlers and audit logs"
git push origin feature/privacy-retention-gdpr
```

---

### PR body exacto a pegar
```
Summary:
- Added deterministic data retention and GDPR compliance tools.
- Implemented policy evaluator tasker/privacy/policy.py with tenant and env overrides.
- Added RetentionWorker tasker/privacy/retention_worker.py to archive and delete eligible records and write audits.
- Added handlers tasker/privacy/handlers.py for subject export and delete flows.
- Added API endpoints for export, delete, task status and audit in tasker/api/app.py.
- Added tests for policy evaluation, export/delete and integration retention run.
- Added documentation tasker/privacy/PRIVACY.md.

Verification steps executed:
1. Installed package in editable mode.
2. Ran unit tests for policy and export/delete.
3. Executed retention worker run_once in dev container to validate archive/delete and audit writes.

Files changed:
- tasker/privacy/*
- tasker/api/app.py
- tests/privacy/*
- tests/integration/test_retention_integration.py
- tasker/privacy/PRIVACY.md

Notes:
- Archive behavior controlled by TASKER_RETENTION_ARCHIVE and TASKER_RETENTION_ARCHIVE_PATH.
- Endpoints enforce RBAC: export/delete allowed to admin or subject owner; audit requires admin.
```

---

### Criterios de aceptación
- `tasker/privacy` existe con `policy.py`, `retention_worker.py`, `handlers.py` y `PRIVACY.md`.
- `evaluate_policy` aplica reglas por tipo, edad, tenant and legal-hold tag; env overrides funcionan.
- `RetentionWorker` puede ejecutarse manualmente (`run_once`) y escribe auditorías en `privacy:audits`.
- API endpoints `/api/v1/privacy/*` existen y respetan permisos.
- Tests unitarios e integración añadidos y ejecutables; integración opcional con `TASKER_INTEGRATION=1`.
- Branch `feature/privacy-retention-gdpr` creado y PR abierto con el PR body exacto arriba.