from __future__ import annotations
import os
import time
import json
from fastapi import FastAPI, HTTPException
from socialseed_tasker.ml.schemas import InferenceRequest, InferenceResponse
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.ml.feature_store import FeatureStore
from socialseed_tasker.ml.runner import ModelRunner

app = FastAPI(title="Tasker ML Serving")

_storage = MemoryStorage()
_feature_store = FeatureStore(_storage)
_runner = ModelRunner(storage=_storage, feature_store=_feature_store)


@app.post("/api/v1/models/{model_name}/infer")
def api_model_infer(model_name: str, req: InferenceRequest):
    features = {}
    if req.key:
        f = _feature_store.get_features(req.key)
        if f is None:
            raise HTTPException(status_code=404, detail="feature key not found")
        features = f
    elif req.features:
        features = req.features
    else:
        raise HTTPException(status_code=400, detail="missing features or key")
    seed = req.params.get("seed") or int(os.getenv("TASKER_ML_SEED", "42"))
    start = time.time()
    res = _runner.predict(model_name, features, version=req.params.get("version"), seed=seed)
    latency = (time.time() - start) * 1000.0
    input_hash = _feature_store.compute_input_hash(features)
    trace = {"model": model_name, "version": res["version"], "input_hash": input_hash, "seed": res["seed"], "latency_ms": res["latency_ms"], "ts": int(time.time())}
    try:
        raw = _storage.get("ml:traces") or b"[]"
        arr = json.loads(raw.decode("utf-8")) if raw else []
        arr.append(trace)
        _storage.put("ml:traces", json.dumps(arr).encode("utf-8"))
    except Exception:
        pass
    return InferenceResponse(model=model_name, version=res["version"], prediction=res["prediction"], input_hash=input_hash, seed=res["seed"], latency_ms=res["latency_ms"], meta={})
