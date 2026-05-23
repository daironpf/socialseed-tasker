# Model Packaging Convention

- Place model pickles under `models/{model_name}/{version}.pkl`
- For development convenience, create `models/{model_name}/latest.pkl` as the default
- Models should implement a method `predict(features: dict, rnd: random.Random) -> Any` for deterministic behavior
