import os


def test_artifacts_exist():
    assert os.path.isdir("dist"), "dist/ directory not found"
    files = [
        f
        for f in os.listdir("dist")
        if f.endswith(".whl") or f.endswith(".tar.gz")
    ]
    assert len(files) >= 1


def test_provenance_template():
    assert os.path.exists("artifacts/provenance_template.json")


def test_gitkeep_exists():
    assert os.path.exists("artifacts/.gitkeep")


def test_local_pipeline_script():
    assert os.path.exists("scripts/ci/run_local_pipeline.sh")


def test_sign_script():
    assert os.path.exists("scripts/ci/sign_artifact.sh")
