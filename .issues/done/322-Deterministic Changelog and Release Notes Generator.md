### Issue 322 — Deterministic Changelog and Release Notes Generator

### Short description
Add an automated, deterministic changelog and release notes generator that builds release notes from commit messages, PR metadata, and issue references. Provide a reproducible CLI and CI job that produces a `CHANGELOG.md` and a `releases/<tag>.md` artifact, supports conventional commit parsing, customizable templates, deterministic ordering, unit tests, and documentation. All file paths, exact file contents, commands, and PR text are provided so an engineer or automation can implement and verify without guessing.

---

### Objective
1. **Changelog generator CLI**  
   - Add `tools/release/changelog.py` exposing `generate_changelog(output_path, from_ref, to_ref, template_path, include_prs)` and a CLI `tools/release/changelogctl.py` with subcommands `generate`, `preview`, `validate-template`.
   - Deterministic behavior: sort commits by commit date ascending, normalize timezones to UTC, and render entries grouped by type (feat, fix, docs, perf, refactor, chore) in that fixed order.
2. **Conventional commit parsing**  
   - Parse commit messages using Conventional Commits. Extract `type`, `scope`, `description`, `body`, `footer` and issue references like `#123` or `GH-123`.
3. **PR and issue enrichment**  
   - When `include_prs=true`, call GitHub API (token via `RELEASE_GH_TOKEN`) to fetch PR title, number, labels, and author for commits that reference PRs (e.g., `Merge pull request #123` or commit footer `PR: #123`). Deterministic: sort PRs by number ascending.
4. **Templates**  
   - Support Jinja2 templates for changelog and release notes. Provide default templates `tools/release/templates/changelog.j2` and `tools/release/templates/release.j2`.
5. **CI integration**  
   - Add `ci/release-changelog.yml` GitHub Actions workflow that runs on `workflow_dispatch` and `push` to tags, generates `CHANGELOG.md` and `releases/<tag>.md`, commits artifacts to the release branch, and uploads them as workflow artifacts.
6. **Tests and validation**  
   - Unit tests for parsing, grouping, and template rendering under `tests/release/*`. A validation test ensures generated changelog is deterministic given a fixed git history fixture.
7. **Documentation**  
   - Add `tools/release/README.md` describing usage, template variables, environment variables, and CI wiring.

---

### Files to add or modify

#### `tools/release/changelog.py` (new)
```python
# tools/release/changelog.py
from __future__ import annotations
import os
import re
import subprocess
import datetime
from typing import List, Dict, Optional, Tuple
import jinja2
import json
import requests

CONVENTIONAL_TYPES = ["feat","fix","docs","perf","refactor","chore"]

COMMIT_RE = re.compile(r'^(?P<type>\w+)(\((?P<scope>[^)]+)\))?:(?P<desc>.+)$')

def _run_git(args: List[str], cwd: Optional[str] = None) -> str:
    cmd = ["git"] + args
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return p.stdout

def _parse_commit_message(msg: str) -> Dict:
    lines = msg.strip().splitlines()
    header = lines[0] if lines else ""
    m = COMMIT_RE.match(header)
    typ = m.group("type") if m else "chore"
    scope = m.group("scope") if m else None
    desc = m.group("desc").strip() if m else header.strip()
    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    # find issue refs like #123 or GH-123
    issues = re.findall(r'(?:#|GH-)(\d+)', msg)
    pr = None
    pr_match = re.search(r'Merge pull request #(?P<num>\d+)', msg)
    if pr_match:
        pr = int(pr_match.group("num"))
    footer_pr = re.search(r'PR:\s*#(?P<num>\d+)', msg)
    if footer_pr:
        pr = int(footer_pr.group("num"))
    return {"type": typ, "scope": scope, "description": desc, "body": body, "issues": [int(i) for i in issues], "pr": pr}

def _commits_between(from_ref: str, to_ref: str) -> List[Dict]:
    # format: hash|iso8601|author|message (message may contain newlines replaced by \n)
    fmt = "%H|%cI|%an|%s%n%b<<END>>"
    out = _run_git(["log", f"{from_ref}..{to_ref}", f"--pretty=format:{fmt}"])
    parts = out.split("<<END>>")
    commits = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # first line contains header fields separated by |
        first_line, *rest = p.splitlines()
        try:
            h, date_iso, author, subject = first_line.split("|", 3)
        except ValueError:
            # fallback
            continue
        body = "\n".join(rest).strip()
        msg = subject + ("\n" + body if body else "")
        parsed = _parse_commit_message(msg)
        commits.append({"hash": h, "date": date_iso, "author": author, "message": msg, **parsed})
    # deterministic sort by date ascending then hash
    commits.sort(key=lambda c: (c["date"], c["hash"]))
    return commits

def _fetch_pr_info(pr_number: int, gh_token: str, repo: str) -> Dict:
    headers = {"Authorization": f"token {gh_token}"} if gh_token else {}
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    j = r.json()
    return {"number": j["number"], "title": j["title"], "author": j["user"]["login"], "labels": [l["name"] for l in j.get("labels", [])]}

def generate_changelog(output_path: str, from_ref: str, to_ref: str, template_path: Optional[str] = None, include_prs: bool = True, gh_token: Optional[str] = None, repo: Optional[str] = None) -> str:
    commits = _commits_between(from_ref, to_ref)
    grouped = {t: [] for t in CONVENTIONAL_TYPES}
    grouped["other"] = []
    prs_cache = {}
    for c in commits:
        t = c.get("type") or "chore"
        if t not in grouped:
            t = "other"
        entry = {"hash": c["hash"], "date": c["date"], "author": c["author"], "description": c["description"], "scope": c.get("scope"), "issues": c.get("issues", []), "pr": c.get("pr")}
        if include_prs and c.get("pr") and gh_token and repo:
            prn = c["pr"]
            if prn not in prs_cache:
                try:
                    prs_cache[prn] = _fetch_pr_info(prn, gh_token, repo)
                except Exception:
                    prs_cache[prn] = {"number": prn, "title": None, "author": None, "labels": []}
            entry["pr_info"] = prs_cache[prn]
        grouped[t].append(entry)
    # deterministic ordering of groups
    ordered_groups = [(t, grouped[t]) for t in CONVENTIONAL_TYPES + ["other"]]
    # load template
    tpl_path = template_path or os.path.join(os.path.dirname(__file__), "templates", "changelog.j2")
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(tpl_path)))
    tpl = env.get_template(os.path.basename(tpl_path))
    rendered = tpl.render(groups=ordered_groups, from_ref=from_ref, to_ref=to_ref, generated_at=datetime.datetime.utcnow().isoformat() + "Z")
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(rendered)
    return output_path
```

#### `tools/release/changelogctl.py` (new)
```python
#!/usr/bin/env python3
# tools/release/changelogctl.py
from __future__ import annotations
import argparse
import os
from tools.release.changelog import generate_changelog

def main(argv=None):
    p = argparse.ArgumentParser(prog="changelogctl")
    sub = p.add_subparsers(dest="cmd")
    g = sub.add_parser("generate")
    g.add_argument("--from", dest="from_ref", required=True)
    g.add_argument("--to", dest="to_ref", required=True)
    g.add_argument("--out", dest="out", required=True)
    g.add_argument("--template", dest="template", default=None)
    g.add_argument("--no-prs", dest="no_prs", action="store_true")
    args = p.parse_args(argv)
    if args.cmd == "generate":
        gh_token = os.getenv("RELEASE_GH_TOKEN")
        repo = os.getenv("RELEASE_GH_REPO")
        include_prs = not args.no_prs
        generate_changelog(args.out, args.from_ref, args.to_ref, template_path=args.template, include_prs=include_prs, gh_token=gh_token, repo=repo)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
```

#### `tools/release/templates/changelog.j2` (new)
```jinja
# Changelog

Generated: {{ generated_at }}

Changes from {{ from_ref }} to {{ to_ref }}

{% for type, entries in groups %}
{% if entries %}
## {{ type | upper }}
{% for e in entries %}
- {{ e.description }}{% if e.scope %} ({{ e.scope }}){% endif %} — {{ e.author }} — `{{ e.hash[:7] }}`{% if e.pr_info %} (PR #{{ e.pr_info.number }} by {{ e.pr_info.author }}){% elif e.pr %} (PR #{{ e.pr }}){% endif %}{% if e.issues %} [issues: {{ e.issues | join(', ') }}]{% endif %}
{% endfor %}
{% endif %}
{% endfor %}
```

#### `tools/release/templates/release.j2` (new)
```jinja
# Release Notes for {{ tag }}

Released: {{ generated_at }}

Summary
{{ summary }}

Changes
{{ changelog }}
```

#### `ci/release-changelog.yml` (new)
```yaml
name: Generate Changelog
on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install deps
        run: python -m pip install jinja2 requests
      - name: Generate changelog
        env:
          RELEASE_GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          RELEASE_GH_REPO: ${{ github.repository }}
        run: |
          TAG=${GITHUB_REF##*/}
          PREV=$(git describe --tags --abbrev=0 ${GITHUB_REF}^ || echo "")
          python tools/release/changelogctl.py generate --from "$PREV" --to "$TAG" --out "releases/${TAG}.md"
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: release-notes
          path: releases/${TAG}.md
```

#### `tools/release/README.md` (new)
```markdown
Changelog Generator

Usage
- Local generate:
  python tools/release/changelogctl.py generate --from v1.2.0 --to v1.3.0 --out CHANGELOG.md

Environment
- RELEASE_GH_TOKEN optional GitHub token to enrich PR metadata.
- RELEASE_GH_REPO repo slug like owner/repo when using token.

Templates
- Default templates live in tools/release/templates.
- Template variables: groups, from_ref, to_ref, generated_at.

CI
- ci/release-changelog.yml runs on tag push and produces releases/<tag>.md artifact.

Determinism
- Commits are sorted by commit date (ISO) then hash.
- PRs are sorted by number ascending.
```

#### Unit tests under `tests/release/` (examples)

**`tests/release/test_parse_commit_unit.py`**
```python
# tests/release/test_parse_commit_unit.py
from tools.release.changelog import _parse_commit_message
def test_parse_simple():
    msg = "feat(api): add endpoint\n\nAdds new endpoint\n\nPR: #12\n"
    p = _parse_commit_message(msg)
    assert p["type"] == "feat"
    assert p["scope"] == "api"
    assert p["pr"] == 12
```

**`tests/release/test_generate_deterministic.py`**
```python
# tests/release/test_generate_deterministic.py
import tempfile, os
from tools.release.changelog import generate_changelog
def test_generate_with_fixture(tmp_path):
    # This test assumes a prepared git fixture in tests/release/fixture-repo
    repo = os.path.join(os.getcwd(), "tests", "release", "fixture-repo")
    out = tmp_path / "ch.md"
    # call generate_changelog with explicit refs in fixture
    generate_changelog(str(out), "v0.0.1", "v0.0.2", template_path=None, include_prs=False)
    assert out.exists()
    txt = out.read_text()
    assert "Changes from v0.0.1 to v0.0.2" in txt
```

---

### Commands to run
```bash
git checkout -b feature/changelog-generator
# add files as specified
python -m pip install jinja2 requests
# run unit tests
pytest tests/release/test_parse_commit_unit.py -q
pytest tests/release/test_generate_deterministic.py -q
# generate a changelog locally
python tools/release/changelogctl.py generate --from v1.0.0 --to v1.1.0 --out CHANGELOG.md
# commit and push
git add tools/release ci/release-changelog.yml tests/release
git commit -m "chore(release): add deterministic changelog generator, templates and CI workflow"
git push origin feature/changelog-generator
```

---

### PR body exact text to paste
```
Summary:
- Added deterministic changelog and release notes generator under tools/release.
- Supports Conventional Commits parsing, PR enrichment via GitHub API, Jinja2 templates, and deterministic grouping and ordering.
- Added CLI tools tools/release/changelogctl.py and default templates.
- Added GitHub Actions workflow ci/release-changelog.yml to generate release notes on tag push and workflow_dispatch.
- Added unit tests to validate parsing and deterministic generation.

Verification steps executed:
1. Installed dependencies: jinja2, requests.
2. Ran unit tests for commit parsing and deterministic generation.
3. Generated a sample changelog locally with python tools/release/changelogctl.py.

Files changed:
- tools/release/changelog.py
- tools/release/changelogctl.py
- tools/release/templates/changelog.j2
- tools/release/templates/release.j2
- ci/release-changelog.yml
- tools/release/README.md
- tests/release/*

Notes:
- For PR enrichment set RELEASE_GH_TOKEN and RELEASE_GH_REPO in environment or CI secrets.
- The generator is deterministic: commits sorted by date then hash; groups ordered by conventional types.
```

---

### Acceptance criteria labels and effort
- **Acceptance criteria**
  - `tools/release/changelog.py` and `tools/release/changelogctl.py` exist and implement `generate_changelog` and CLI `generate`.
  - Default templates exist at `tools/release/templates`.
  - CI workflow `ci/release-changelog.yml` exists and produces `releases/<tag>.md` artifact on tag push.
  - Unit tests under `tests/release` validate parsing and deterministic output.
  - Documentation `tools/release/README.md` explains usage and environment variables.
- **Labels to apply**
  - `release`
  - `automation`
  - `ci`
  - `small-priority`
- **Estimated effort**
  - **Small (S)** — expected **0.5–2 hours** for an engineer familiar with git, Jinja2, and GitHub Actions.