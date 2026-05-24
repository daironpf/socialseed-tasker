from __future__ import annotations

import datetime
import os
import re
import subprocess

import jinja2
import requests

CONVENTIONAL_TYPES = ["feat", "fix", "docs", "perf", "refactor", "chore"]

COMMIT_RE = re.compile(r"^(?P<type>\w+)(\((?P<scope>[^)]+)\))?:(?P<desc>.+)$")


def _run_git(args: list[str], cwd: str | None = None) -> str:
    cmd = ["git"] + args
    p = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=True
    )
    return p.stdout


def _parse_commit_message(msg: str) -> dict:
    lines = msg.strip().splitlines()
    header = lines[0] if lines else ""
    m = COMMIT_RE.match(header)
    typ = m.group("type") if m else "chore"
    scope = m.group("scope") if m else None
    desc = m.group("desc").strip() if m else header.strip()
    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    issues = re.findall(r"(?:#|GH-)(\d+)", msg)
    pr = None
    pr_match = re.search(r"Merge pull request #(?P<num>\d+)", msg)
    if pr_match:
        pr = int(pr_match.group("num"))
    footer_pr = re.search(r"PR:\s*#(?P<num>\d+)", msg)
    if footer_pr:
        pr = int(footer_pr.group("num"))
    return {
        "type": typ,
        "scope": scope,
        "description": desc,
        "body": body,
        "issues": [int(i) for i in issues],
        "pr": pr,
    }


def _commits_between(from_ref: str, to_ref: str, cwd: str | None = None) -> list[dict]:
    fmt = "%H|%cI|%an|%s%n%b<<END>>"
    out = _run_git(["log", f"{from_ref}..{to_ref}", f"--pretty=format:{fmt}"], cwd=cwd)
    parts = out.split("<<END>>")
    commits: list[dict] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        first_line, *rest = p.splitlines()
        try:
            h, date_iso, author, subject = first_line.split("|", 3)
        except ValueError:
            continue
        body = "\n".join(rest).strip()
        msg = subject + ("\n" + body if body else "")
        parsed = _parse_commit_message(msg)
        commits.append(
            {"hash": h, "date": date_iso, "author": author, "message": msg, **parsed}
        )
    commits.sort(key=lambda c: (c["date"], c["hash"]))
    return commits


def _fetch_pr_info(pr_number: int, gh_token: str, repo: str) -> dict:
    headers = {"Authorization": f"token {gh_token}"} if gh_token else {}
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    j = r.json()
    return {
        "number": j["number"],
        "title": j["title"],
        "author": j["user"]["login"],
        "labels": [label["name"] for label in j.get("labels", [])],
    }


def generate_changelog(
    output_path: str,
    from_ref: str,
    to_ref: str,
    template_path: str | None = None,
    include_prs: bool = True,
    gh_token: str | None = None,
    repo: str | None = None,
    cwd: str | None = None,
) -> str:
    commits = _commits_between(from_ref, to_ref, cwd=cwd)
    grouped: dict[str, list] = {t: [] for t in CONVENTIONAL_TYPES}
    grouped["other"] = []
    prs_cache: dict[int, dict] = {}
    for c in commits:
        t = c.get("type") or "chore"
        if t not in grouped:
            t = "other"
        entry: dict = {
            "hash": c["hash"],
            "date": c["date"],
            "author": c["author"],
            "description": c["description"],
            "scope": c.get("scope"),
            "issues": c.get("issues", []),
            "pr": c.get("pr"),
        }
        if include_prs and c.get("pr") and gh_token and repo:
            prn = c["pr"]
            if prn not in prs_cache:
                try:
                    prs_cache[prn] = _fetch_pr_info(prn, gh_token, repo)
                except Exception:
                    prs_cache[prn] = {
                        "number": prn,
                        "title": None,
                        "author": None,
                        "labels": [],
                    }
            entry["pr_info"] = prs_cache[prn]
        grouped[t].append(entry)
    ordered_groups = [(t, grouped[t]) for t in CONVENTIONAL_TYPES + ["other"]]
    tpl_path = template_path or os.path.join(
        os.path.dirname(__file__), "templates", "changelog.j2"
    )
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(tpl_path)))
    tpl = env.get_template(os.path.basename(tpl_path))
    rendered = tpl.render(
        groups=ordered_groups,
        from_ref=from_ref,
        to_ref=to_ref,
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(rendered)
    return output_path
