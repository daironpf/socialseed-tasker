# ML Serving and Feature Store Guide

## Start ML Service
```bash
docker compose -f docker-compose.ml.yml up -d --build
```
Service endpoint: `POST http://localhost:8090/api/v1/models/{model_name}/infer`

## Request Format
```json
{
  "key": "optional-feature-key",
  "features": {"f1": 1.0, "f2": "x"},
  "params": {}
}
```

## Reproducibility
- Set `TASKER_ML_SEED` to a fixed integer for deterministic predictions.
- Store features in FeatureStore to reuse exact inputs.

## Feature Store
- `put_features(key, features)` — store feature set
- `get_features(key)` — retrieve feature set
- `list_keys(prefix)` — list stored feature keys
- `compute_input_hash(features)` — SHA-256 hash for traceability

## Packaging Models
- Place pickled models under `models/{model_name}/{version}.pkl`
- Create `models/{model_name}/latest.pkl` as the default version
- Models should implement `predict(features, rnd: random.Random) -> Any` for deterministic behavior

## Testing
- `pytest tests/ml/test_feature_store.py -q`
- `pytest tests/ml/test_runner_unit.py -q`
- Integration: `TASKER_INTEGRATION=1 pytest tests/integration/test_ml_inference_integration.py -q`
