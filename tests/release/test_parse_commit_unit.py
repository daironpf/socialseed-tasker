from tools.release.changelog import _parse_commit_message


def test_parse_simple():
    msg = "feat(api): add endpoint\n\nAdds new endpoint\n\nPR: #12\n"
    p = _parse_commit_message(msg)
    assert p["type"] == "feat"
    assert p["scope"] == "api"
    assert p["pr"] == 12


def test_parse_no_scope():
    msg = "fix: resolve crash"
    p = _parse_commit_message(msg)
    assert p["type"] == "fix"
    assert p["scope"] is None
    assert p["description"] == "resolve crash"


def test_parse_merge_pr():
    msg = "Merge pull request #42 from feature/branch\n\nSome description"
    p = _parse_commit_message(msg)
    assert p["pr"] == 42
    assert p["type"] == "chore"


def test_parse_issues():
    msg = "feat: add login (#123, GH-456)"
    p = _parse_commit_message(msg)
    assert 123 in p["issues"]
    assert 456 in p["issues"]


def test_parse_chore_fallback():
    msg = "random message without conventional prefix"
    p = _parse_commit_message(msg)
    assert p["type"] == "chore"
    assert p["description"] == "random message without conventional prefix"
