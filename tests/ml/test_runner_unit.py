import pickle
import os
import random
from socialseed_tasker.ml.runner import ModelRunner
from socialseed_tasker.ml.feature_store import FeatureStore
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage


class DummyModel:
    def predict(self, features, rnd: random.Random):
        s = sum(v for v in features.values() if isinstance(v, (int, float)))
        return s + rnd.random()


class CallableModel:
    def __call__(self, features):
        return sum(v for v in features.values() if isinstance(v, (int, float)))


def _make_runner(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    mdir = models_dir / "dm"
    mdir.mkdir()
    with open(mdir / "latest.pkl", "wb") as fh:
        pickle.dump(DummyModel(), fh)
    s = MemoryStorage()
    fs = FeatureStore(s)
    runner = ModelRunner(storage=s, feature_store=fs, models_dir=str(models_dir))
    return runner


def test_runner_predict(tmp_path):
    runner = _make_runner(tmp_path)
    res = runner.predict("dm", {"x": 1, "y": 2}, seed=123)
    assert "prediction" in res
    assert isinstance(res["prediction"], float)


def test_deterministic_seed(tmp_path):
    runner = _make_runner(tmp_path)
    r1 = runner.predict("dm", {"x": 10}, seed=42)
    r2 = runner.predict("dm", {"x": 10}, seed=42)
    assert r1["prediction"] == r2["prediction"]


def test_runner_no_predict_method(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    mdir = models_dir / "cm"
    mdir.mkdir()
    with open(mdir / "latest.pkl", "wb") as fh:
        pickle.dump(CallableModel(), fh)
    s = MemoryStorage()
    fs = FeatureStore(s)
    runner = ModelRunner(storage=s, feature_store=fs, models_dir=str(models_dir))
    res = runner.predict("cm", {"a": 5, "b": 3}, seed=0)
    assert res["prediction"] == 8


def test_model_caching(tmp_path):
    runner = _make_runner(tmp_path)
    res1 = runner.predict("dm", {"x": 1}, seed=0)
    res2 = runner.predict("dm", {"x": 1}, seed=0)
    assert res1["prediction"] == res2["prediction"]
