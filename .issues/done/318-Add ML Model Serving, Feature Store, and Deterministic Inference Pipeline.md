### Issue 318 — Add ML Model Serving, Feature Store, and Deterministic Inference Pipeline

**Descripción breve**  
Agregar una capa reproducible y determinista para servir modelos de Machine Learning: un **servicio de inferencia** HTTP, un **feature store** simple persistente, integración con la canalización de datos existente, tests unitarios e integración, Docker Compose para despliegue local, y documentación. Todo debe ser explícito: rutas, nombres de archivos, firmas de funciones, variables de entorno, comandos y cuerpo de PR listos para aplicar sin ambigüedades.

---

### Objetivo exacto
1. **Servicio de inferencia**: exponer endpoint `POST /api/v1/models/<model_name>/infer` que reciba features JSON, valide esquema, ejecute inferencia determinista y devuelva predicción y metadatos (model version, latency, trace id).  
2. **Feature Store**: implementar `tasker/ml/feature_store.py` con API: `put_features(key, features)`, `get_features(key)`, `list_keys(prefix)`, persistencia via `StoragePort`.  
3. **Model loader y runner**: `tasker/ml/runner.py` que carga modelos desde `models/` (formato Pickle para dev), soporta versiones y caching, y ejecuta inferencia con semilla determinista.  
4. **Batch inference worker**: `tasker/ml/batch_worker.py` que procesa colas de inferencia en StoragePort (lista de jobs), escribe resultados y métricas.  
5. **Validación y esquema**: añadir `tasker/ml/schemas.py` con Pydantic schemas para requests y responses.  
6. **Observabilidad y reproducibilidad**: registrar **model_version**, **seed**, **input_hash**, **latency**, y guardar trazas mínimas en StoragePort bajo `ml:traces`.  
7. **Tests**: unit tests para feature store, runner, endpoint; integración que levanta servicio y ejecuta inferencia end-to-end.  
8. **Docker Compose**: añadir servicio `ml` en `docker-compose.ml.yml` que construya `Dockerfile.ml` y exponga puerto **8090**.  
9. **Documentación**: `tasker/ml/ML.md` con instrucciones para entrenar, empaquetar y servir modelos, y cómo reproducir inferencias.  
10. **Branch y PR**: crear branch `feature/ml-serving-feature-store` y abrir PR con el PR body exacto provisto más abajo.

---

### Archivos a añadir o modificar
- `tasker/ml/__init__.py` **nuevo**  
- `tasker/ml/schemas.py` **nuevo**  
- `tasker/ml/feature_store.py` **nuevo**  
- `tasker/ml/runner.py` **nuevo**  
- `tasker/ml/batch_worker.py` **nuevo**  
- `tasker/ml/ML.md` **nuevo**  
- `models/README.md` **nuevo** (convención de modelos)  
- `Dockerfile.ml` **nuevo**  
- `docker-compose.ml.yml` **nuevo**  
- `tasker/api/app.py` **modificar** — añadir rutas de inferencia y wiring para ML container  
- `tasker/cli/wiring.py` **modificar** — exponer `ml_runner` y `feature_store` en container  
- `tests/ml/test_feature_store.py` **nuevo**  
- `tests/ml/test_runner_unit.py` **nuevo**  
- `tests/integration/test_ml_inference_integration.py` **nuevo, integration**

---

### Código exacto a añadir

#### `tasker/ml/__init__.py`
```python
# tasker/ml/__init__.py
from .schemas import InferenceRequest, InferenceResponse
from .feature_store import FeatureStore
from .runner import ModelRunner
from .batch_worker import BatchWorker

__all__ = ["InferenceRequest", "InferenceResponse", "FeatureStore", "ModelRunner", "BatchWorker"]
```

#### `tasker/ml/schemas.py`
```python
# tasker/ml/schemas.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class InferenceRequest(BaseModel):
    key: Optional[str] = Field(None, description="Feature store key to fetch features")
    features: Optional[Dict[str, Any]] = Field(None, description="Inline features if not using feature store")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)

class InferenceResponse(BaseModel):
    model: str
    version: str
    prediction: Any
    input_hash: str
    seed: int
    latency_ms: float
    meta: Dict[str, Any] = Field(default_factory=dict)
```

#### `tasker/ml/feature_store.py`
```python
# tasker/ml/feature_store.py
from __future__ import annotations
import json
import hashlib
from typing import Dict, Any, List, Optional
from tasker.application.ports import StoragePort

class FeatureStore:
    """
    Simple feature store backed by StoragePort. Keys are arbitrary strings.
    """

    PREFIX = "ml:features:"

    def __init__(self, storage: StoragePort):
        self.storage = storage

    def _key(self, key: str) -> str:
        return self.PREFIX + key

    def put_features(self, key: str, features: Dict[str, Any]) -> None:
        payload = json.dumps(features, sort_keys=True).encode("utf-8")
        self.storage.put(self._key(key), payload)

    def get_features(self, key: str) -> Optional[Dict[str, Any]]:
        raw = self.storage.get(self._key(key))
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))

    def list_keys(self, prefix: str = "") -> List[str]:
        if not hasattr(self.storage, "list_keys"):
            return []
        all_keys = self.storage.list_keys()
        ks = [k[len(self.PREFIX):] for k in all_keys if k.startswith(self.PREFIX)]
        if prefix:
            return [k for k in ks if k.startswith(prefix)]
        return ks

    def compute_input_hash(self, features: Dict[str, Any]) -> str:
        b = json.dumps(features, sort_keys=True).encode("utf-8")
        return hashlib.sha256(b).hexdigest()
```

#### `tasker/ml/runner.py`
```python
# tasker/ml/runner.py
from __future__ import annotations
import os
import time
import pickle
import threading
import random
from typing import Any, Dict, Optional
from tasker.application.ports import StoragePort
from tasker.ml.feature_store import FeatureStore

MODELS_DIR = os.getenv("TASKER_MODELS_DIR", "models")
DEFAULT_SEED = int(os.getenv("TASKER_ML_SEED", "42"))

class ModelRunner:
    """
    Loads models from models/<model_name>/version.pkl
    Exposes predict(model_name, features, seed) -> prediction
    """

    def __init__(self, storage: StoragePort, feature_store: FeatureStore):
        self.storage = storage
        self.feature_store = feature_store
        self._cache = {}
        self._lock = threading.RLock()

    def _model_path(self, model_name: str, version: Optional[str] = None) -> str:
        if version:
            return f"{MODELS_DIR}/{model_name}/{version}.pkl"
        # pick latest by listing directory
        return f"{MODELS_DIR}/{model_name}/latest.pkl"

    def load_model(self, model_name: str, version: Optional[str] = None):
        key = f"{model_name}:{version or 'latest'}"
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            path = self._model_path(model_name, version)
            with open(path, "rb") as fh:
                model = pickle.load(fh)
            self._cache[key] = model
            return model

    def predict(self, model_name: str, features: Dict[str, Any], version: Optional[str] = None, seed: Optional[int] = None) -> Dict[str, Any]:
        seed = int(seed) if seed is not None else DEFAULT_SEED
        model = self.load_model(model_name, version)
        # deterministic seed
        rnd = random.Random(seed)
        start = time.time()
        # model must implement predict(features, rnd) for deterministic behavior in dev
        if hasattr(model, "predict"):
            pred = model.predict(features, rnd)
        else:
            # fallback: if model is a callable
            pred = model(features)
        latency = (time.time() - start) * 1000.0
        return {"prediction": pred, "latency_ms": latency, "version": version or "latest", "seed": seed}
```

#### `tasker/ml/batch_worker.py`
```python
# tasker/ml/batch_worker.py
from __future__ import annotations
import time
import threading
import json
from typing import Optional, Dict, Any
from tasker.application.ports import StoragePort
from tasker.ml.runner import ModelRunner

JOBS_KEY = "ml:jobs"
RESULTS_PREFIX = "ml:results:"

class BatchWorker:
    def __init__(self, storage: StoragePort, runner: ModelRunner, poll_interval: float = 1.0):
        self.storage = storage
        self.runner = runner
        self.poll_interval = poll_interval
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
            time.sleep(self.poll_interval)

    def run_once(self):
        raw = self.storage.get(JOBS_KEY) or b"[]"
        jobs = json.loads(raw.decode("utf-8")) if raw else []
        if not jobs:
            return
        remaining = []
        for job in jobs:
            try:
                model = job["model"]
                features = job.get("features") or {}
                version = job.get("version")
                seed = job.get("seed")
                res = self.runner.predict(model, features, version=version, seed=seed)
                rid = f"{model}:{int(time.time()*1000)}"
                self.storage.put(RESULTS_PREFIX + rid, json.dumps({"job": job, "result": res}).encode("utf-8"))
            except Exception:
                remaining.append(job)
        # write back remaining jobs
        self.storage.put(JOBS_KEY, json.dumps(remaining).encode("utf-8"))
```

#### `Dockerfile.ml`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN python -m pip install --upgrade pip && pip install -e . uvicorn pydantic
EXPOSE 8090
CMD ["uvicorn", "tasker.ml.server:app", "--host", "0.0.0.0", "--port", "8090"]
```

#### `docker-compose.ml.yml`
```yaml
version: "3.8"
services:
  ml:
    build:
      context: .
      dockerfile: Dockerfile.ml
    image: tasker-ml:local
    environment:
      TASKER_MODELS_DIR: "/app/models"
      TASKER_ML_SEED: "42"
    ports:
      - "8090:8090"
    volumes:
      - ./models:/app/models:cached
    depends_on:
      - api
```

#### `models/README.md`
```text
Model packaging convention

- Place model pickles under models/<model_name>/<version>.pkl
- For development convenience, create models/<model_name>/latest.pkl as the default.
- Models should implement a method predict(features: dict, rnd: random.Random) -> Any for deterministic behavior.
```

#### `tasker/ml/ML.md`
```markdown
ML Serving and Feature Store Guide

Start ML service
- Build and run:
  docker compose -f docker-compose.ml.yml up -d --build
- Service endpoint:
  POST http://localhost:8090/api/v1/models/<model_name>/infer

Request format
- JSON body matching InferenceRequest:
  {
    "key": "optional-feature-key",
    "features": {"f1": 1.0, "f2": "x"},
    "params": {}
  }

Reproducibility
- Set TASKER_ML_SEED to a fixed integer to ensure deterministic predictions when models use the provided random.Random.
- Store features in FeatureStore to reuse exact inputs.

Feature Store
- Use FeatureStore API via wiring container or HTTP endpoints (if exposed) to put/get features.

Packaging models
- Place pickled models under models/<model_name>/<version>.pkl
- Implement predict(features, rnd) for deterministic behavior.

Testing
- Unit tests in tests/ml validate feature store and runner.
- Integration test tests/integration/test_ml_inference_integration.py runs end-to-end.
```

---

### Integración con API y wiring

#### `tasker/api/app.py` snippets to add
**Importar schemas y runner**
```python
from tasker.ml.schemas import InferenceRequest, InferenceResponse
```

**Endpoint de inferencia**
```python
@app.post("/api/v1/models/{model_name}/infer")
def api_model_infer(model_name: str, req: InferenceRequest, container = Depends(get_container)):
    # resolve features
    fs = container.feature_store
    features = {}
    if req.key:
        f = fs.get_features(req.key)
        if f is None:
            raise HTTPException(status_code=404, detail="feature key not found")
        features = f
    elif req.features:
        features = req.features
    else:
        raise HTTPException(status_code=400, detail="missing features or key")
    # deterministic seed optional
    seed = req.params.get("seed") or int(os.getenv("TASKER_ML_SEED", "42"))
    runner = container.ml_runner
    start = time.time()
    res = runner.predict(model_name, features, version=req.params.get("version"), seed=seed)
    latency = (time.time() - start) * 1000.0
    input_hash = fs.compute_input_hash(features)
    # trace record
    trace = {"model": model_name, "version": res["version"], "input_hash": input_hash, "seed": res["seed"], "latency_ms": res["latency_ms"], "ts": int(time.time())}
    try:
        raw = container.storage.get("ml:traces") or b"[]"
        import json
        arr = json.loads(raw.decode("utf-8")) if raw else []
        arr.append(trace)
        container.storage.put("ml:traces", json.dumps(arr).encode("utf-8"))
    except Exception:
        pass
    resp = InferenceResponse(model=model_name, version=res["version"], prediction=res["prediction"], input_hash=input_hash, seed=res["seed"], latency_ms=res["latency_ms"], meta={})
    return resp
```

#### `tasker/cli/wiring.py` excerpt to add
```python
from tasker.ml.feature_store import FeatureStore
from tasker.ml.runner import ModelRunner
from tasker.ml.batch_worker import BatchWorker

feature_store = FeatureStore(storage)
ml_runner = ModelRunner(storage=storage, feature_store=feature_store)
ml_batch_worker = BatchWorker(storage=storage, runner=ml_runner)
# include in Container return
return Container(..., feature_store=feature_store, ml_runner=ml_runner, ml_batch_worker=ml_batch_worker, ...)
```

---

### Tests y verificación

#### `tests/ml/test_feature_store.py`
```python
# tests/ml/test_feature_store.py
from tasker.ml.feature_store import FeatureStore
from tasker.infrastructure.memory_storage import MemoryStorage

def test_put_get_list():
    s = MemoryStorage()
    fs = FeatureStore(s)
    fs.put_features("k1", {"a":1})
    assert fs.get_features("k1") == {"a":1}
    assert "k1" in fs.list_keys()
```

#### `tests/ml/test_runner_unit.py`
```python
# tests/ml/test_runner_unit.py
import pickle, os, tempfile, random
from tasker.ml.runner import ModelRunner
from tasker.ml.feature_store import FeatureStore
from tasker.infrastructure.memory_storage import MemoryStorage

class DummyModel:
    def predict(self, features, rnd: random.Random):
        # deterministic: sum numeric features plus rnd.random()
        s = sum(v for v in features.values() if isinstance(v, (int,float)))
        return s + rnd.random()

def test_runner_predict(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    mdir = models_dir / "dm"
    mdir.mkdir()
    with open(mdir / "latest.pkl", "wb") as fh:
        pickle.dump(DummyModel(), fh)
    os.environ["TASKER_MODELS_DIR"] = str(tmp_path / "models")
    s = MemoryStorage()
    fs = FeatureStore(s)
    runner = ModelRunner(storage=s, feature_store=fs)
    res = runner.predict("dm", {"x":1, "y":2}, seed=123)
    assert "prediction" in res
```

#### `tests/integration/test_ml_inference_integration.py`
```python
# tests/integration/test_ml_inference_integration.py
import os, time, requests, pickle
import pytest
from tasker.infrastructure.memory_storage import MemoryStorage
from tasker.ml.feature_store import FeatureStore

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_infer_endpoint(tmp_path):
    _skip_if_not_integration()
    # ensure model exists under models/demo/latest.pkl
    import models
    # call endpoint
    url = "http://localhost:8090/api/v1/models/demo/infer"
    payload = {"features": {"a":1, "b":2}}
    r = requests.post(url, json=payload, timeout=5)
    assert r.status_code == 200
    j = r.json()
    assert "prediction" in j
```

---

### Comandos exactos para ejecutar y verificar
```bash
git checkout -b feature/ml-serving-feature-store
# crear archivos y modelos de ejemplo
python -m pip install -e .
# construir y levantar servicio ML
docker compose -f docker-compose.ml.yml up -d --build
# ejecutar tests unitarios
pytest tests/ml/test_feature_store.py -q
pytest tests/ml/test_runner_unit.py -q
# integración opcional
export TASKER_INTEGRATION=1
# asegúrate de tener un modelo demo en models/demo/latest.pkl
pytest tests/integration/test_ml_inference_integration.py -q -m integration || true
# commit y push
git add tasker/ml Dockerfile.ml docker-compose.ml.yml models README.md tests/ml tests/integration
git commit -m "feat(ml): add model serving, feature store, runner and batch worker with tests"
git push origin feature/ml-serving-feature-store
```

---

### PR body exacto a pegar
```
Summary:
- Added ML model serving and feature store.
- Implemented FeatureStore, ModelRunner, BatchWorker and Pydantic schemas.
- Added endpoint POST /api/v1/models/{model_name}/infer for deterministic inference.
- Added Dockerfile.ml and docker-compose.ml.yml to run ML service on port 8090.
- Added unit and integration tests and documentation tasker/ml/ML.md.
- Wired feature_store and ml_runner into container wiring.

Verification steps executed by this agent:
1. Installed package in editable mode.
2. Ran unit tests for feature store and runner.
3. Optionally started ML service via docker compose and ran integration inference test.

Files changed:
- tasker/ml/*
- Dockerfile.ml
- docker-compose.ml.yml
- models/README.md
- Modified: tasker/api/app.py, tasker/cli/wiring.py
- Tests: tests/ml/* tests/integration/test_ml_inference_integration.py

Notes:
- Models for development must implement predict(features, rnd) for deterministic behavior.
- Use TASKER_ML_SEED to control randomness for reproducible inference.
```

---

### Criterios de aceptación
- `FeatureStore` existe y persiste features en `StoragePort` con `put_features`, `get_features`, `list_keys`, `compute_input_hash`.  
- `ModelRunner` carga modelos desde `models/` y ejecuta `predict` con semilla determinista.  
- Endpoint `POST /api/v1/models/{model_name}/infer` responde con `InferenceResponse` y registra trazas en `ml:traces`.  
- `BatchWorker` procesa trabajos desde `ml:jobs` y escribe resultados en `ml:results:` keys.  
- Unit tests pasan y la integración opcional funciona cuando `TASKER_INTEGRATION=1`.  
- Branch `feature/ml-serving-feature-store` creado y PR abierto con el PR body exacto arriba.