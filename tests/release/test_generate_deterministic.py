import os
import subprocess
import tempfile

import pytest

from tools.release.changelog import generate_changelog


@pytest.fixture(scope="module")
def fixture_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = tmpdir
        subprocess.run(["git", "init"], cwd=cwd, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=cwd, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=cwd, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "feat: initial commit"],
            cwd=cwd, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "tag", "v0.0.1"],
            cwd=cwd, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "feat(api): add endpoint\n\nPR: #12"],
            cwd=cwd, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "fix: resolve crash"],
            cwd=cwd, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "docs: update readme"],
            cwd=cwd, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "tag", "v0.0.2"],
            cwd=cwd, check=True, capture_output=True,
        )
        yield cwd


def test_generate_with_fixture(fixture_repo):
    out = os.path.join(fixture_repo, "ch.md")
    result = generate_changelog(
        str(out), "v0.0.1", "v0.0.2", template_path=None, include_prs=False, cwd=fixture_repo,
    )
    assert result == out
    assert os.path.exists(out)
    with open(out, encoding="utf-8") as f:
        txt = f.read()
    assert "Changes from v0.0.1 to v0.0.2" in txt
    assert "add endpoint" in txt
    assert "resolve crash" in txt
    assert "update readme" in txt


def test_generate_deterministic_output(fixture_repo):
    out1 = os.path.join(fixture_repo, "ch1.md")
    out2 = os.path.join(fixture_repo, "ch2.md")
    generate_changelog(str(out1), "v0.0.1", "v0.0.2", include_prs=False, cwd=fixture_repo)
    generate_changelog(str(out2), "v0.0.1", "v0.0.2", include_prs=False, cwd=fixture_repo)
    with open(out1, encoding="utf-8") as f:
        txt1 = f.read()
    with open(out2, encoding="utf-8") as f:
        txt2 = f.read()
    lines1 = [line for line in txt1.splitlines() if not line.startswith("Generated:")]
    lines2 = [line for line in txt2.splitlines() if not line.startswith("Generated:")]
    assert lines1 == lines2
