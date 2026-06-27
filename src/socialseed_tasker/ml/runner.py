from __future__ import annotations
import os
import time
import pickle
import threading
import random
from typing import Any, Dict, Optional
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.ml.feature_store import FeatureStore

DEFAULT_SEED = int(os.getenv("TASKER_ML_SEED", "42"))


class ModelRunner:
    def __init__(self, storage: StoragePort, feature_store: FeatureStore, models_dir: Optional[str] = None):
        self.storage = storage
        self.feature_store = feature_store
        self.models_dir = models_dir or os.getenv("TASKER_MODELS_DIR", "models")
        self._cache = {}
        self._lock = threading.RLock()

    def _model_path(self, model_name: str, version: Optional[str] = None) -> str:
        if version:
            return f"{self.models_dir}/{model_name}/{version}.pkl"
        return f"{self.models_dir}/{model_name}/latest.pkl"

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
        rnd = random.Random(seed)
        start = time.time()
        if hasattr(model, "predict"):
            pred = model.predict(features, rnd)
        else:
            pred = model(features)
        latency = (time.time() - start) * 1000.0
        return {"prediction": pred, "latency_ms": latency, "version": version or "latest", "seed": seed}
