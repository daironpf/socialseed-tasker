"""Mock API server that persists data to JSON files."""
import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Optional

app = FastAPI(title="Mock Data API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/dataset-de-pruebas"))


def read_json(filename: str) -> dict:
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(filename: str, data: dict):
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    model: Optional[str] = None
    specialization: Optional[str] = None
    skills: Optional[list[str]] = None
    avatar: Optional[str] = None


class IssueCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "OPEN"
    priority: str = "MEDIUM"
    component_id: str = ""
    assignee: Optional[str] = None
    created_by: Optional[str] = None
    labels: list[str] = []
    dependencies: list[str] = []


@app.get("/mock/users")
def get_users():
    data = read_json("users.json")
    return {"data": data.get("users", [])}


@app.get("/mock/users/{user_id}")
def get_user(user_id: str):
    data = read_json("users.json")
    users = data.get("users", [])
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"data": user}


@app.put("/mock/users/{user_id}")
def update_user(user_id: str, body: UserUpdate):
    data = read_json("users.json")
    users = data.get("users", [])
    idx = next((i for i, u in enumerate(users) if u["id"] == user_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = body.model_dump(exclude_unset=True)
    users[idx].update(update_data)
    data["users"] = users
    write_json("users.json", data)
    return {"data": users[idx]}


@app.get("/mock/issues")
def get_issues(page: int = 1, limit: int = 200, status: str = None):
    data = read_json("issues.json")
    issues = data.get("issues", [])
    if status:
        issues = [i for i in issues if i.get("status") == status]
    return {"data": issues, "meta": {"total": len(issues)}}


@app.post("/mock/issues")
def create_issue(body: IssueCreate):
    data = read_json("issues.json")
    issues = data.get("issues", [])

    new_id = f"ISS-{len(issues) + 1:03d}"
    new_issue = {
        "id": new_id,
        "title": body.title,
        "description": body.description,
        "status": body.status,
        "priority": body.priority,
        "component_id": body.component_id,
        "assignee": body.assignee,
        "created_by": body.created_by,
        "labels": body.labels,
        "dependencies": body.dependencies,
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "closed_at": None,
    }

    issues.append(new_issue)
    data["issues"] = issues
    write_json("issues.json", data)
    return {"data": new_issue}


@app.get("/mock/components")
def get_components():
    data = read_json("components.json")
    return {"data": data.get("components", [])}


@app.get("/mock/policies")
def get_policies():
    data = read_json("policies.json")
    return {"data": data.get("policies", [])}


@app.get("/mock/dashboard-stats")
def get_dashboard_stats():
    issues_data = read_json("issues.json")
    components_data = read_json("components.json")
    policies_data = read_json("policies.json")

    issues = issues_data.get("issues", [])
    components = components_data.get("components", [])
    policies = policies_data.get("policies", [])

    return {
        "data": {
            "total_issues": len(issues),
            "open_issues": len([i for i in issues if i.get("status") == "OPEN"]),
            "in_progress_issues": len([i for i in issues if i.get("status") == "IN_PROGRESS"]),
            "blocked_issues": len([i for i in issues if i.get("status") == "BLOCKED"]),
            "closed_issues": len([i for i in issues if i.get("status") == "CLOSED"]),
            "total_components": len(components),
            "total_policies": len(policies),
            "active_policies": len([p for p in policies if p.get("is_active")]),
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ==================== ANALYSIS ENDPOINTS ====================


class RootCauseRequest(BaseModel):
    test_name: str
    error_message: str
    component: Optional[str] = None
    labels: Optional[list[str]] = None


def _build_dependency_graph():
    deps_data = read_json("dependencies.json")
    issues_data = read_json("issues.json")
    deps = deps_data.get("dependencies", {})
    nodes = {n["id"]: n for n in deps.get("nodes", [])}
    edges = deps.get("edges", [])

    for issue in issues_data.get("issues", []):
        if issue["id"] not in nodes:
            nodes[issue["id"]] = {
                "id": issue["id"],
                "label": issue["title"],
                "status": issue["status"],
                "priority": issue["priority"],
                "component": issue.get("component_id", ""),
            }
    return list(nodes.values()), edges


def _bfs(start_id, edges):
    visited = {start_id: 0}
    queue = [start_id]
    direct = []
    transitive = []
    child_map = {}

    while queue:
        current = queue.pop(0)
        for edge in edges:
            target = None
            if edge["from"] == current and edge["to"] not in visited:
                target = edge["to"]
            elif edge["type"] == "depends_on" and edge["to"] == current and edge["from"] not in visited:
                target = edge["from"]

            if target:
                visited[target] = visited[current] + 1
                queue.append(target)
                child_map.setdefault(current, []).append(target)
                if visited[target] == 1:
                    direct.append(target)
                else:
                    transitive.append({"id": target, "level": visited[target]})

    return direct, transitive, visited, child_map


def _calc_risk(direct, transitive, nodes_map, visited):
    total_affected = len(direct) + len(transitive)
    critical_count = sum(1 for d in direct if nodes_map.get(d) and nodes_map[d].get("priority") == "CRITICAL")
    high_count = sum(1 for d in direct if nodes_map.get(d) and nodes_map[d].get("priority") == "HIGH")
    blocked_count = sum(1 for d in direct if nodes_map.get(d) and nodes_map[d].get("status") == "BLOCKED")

    score = 0
    score += critical_count * 40
    score += high_count * 20
    score += blocked_count * 15
    score += total_affected * 3
    max_depth = max(visited.values()) if visited else 0
    score += max_depth * 5

    if score >= 80:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    return "LOW"


def _find_cascade_blocked(start_id, visited, edges, nodes_map):
    blocked = []
    for node_id, depth in visited.items():
        if node_id == start_id:
            continue
        node = nodes_map.get(node_id)
        if not node:
            continue
        for edge in edges:
            if edge["from"] == node_id and edge["to"] not in visited:
                target_node = nodes_map.get(edge["to"])
                if target_node and target_node.get("status") not in ("CLOSED",):
                    blocked.append({
                        "id": edge["to"],
                        "title": target_node.get("label", edge["to"]),
                        "status": target_node.get("status", "OPEN"),
                    })
                    break
    return blocked


@app.get("/mock/analysis/impact/{issue_id}")
def analyze_impact(issue_id: str):
    nodes, edges = _build_dependency_graph()
    nodes_map = {n["id"]: n for n in nodes}

    if issue_id not in nodes_map:
        raise HTTPException(status_code=404, detail="Issue not found in dependency graph")

    direct_ids, transitive, visited, child_map = _bfs(issue_id, edges)

    direct_affected = []
    for d_id in direct_ids:
        n = nodes_map.get(d_id)
        if n:
            direct_affected.append({"id": d_id, "title": n["label"], "status": n["status"]})

    transitive_affected = []
    for t in transitive:
        n = nodes_map.get(t["id"])
        if n:
            transitive_affected.append({"id": t["id"], "title": n["label"], "status": n["status"], "level": t["level"]})

    risk_level = _calc_risk(direct_ids, transitive, nodes_map, visited)

    affected_components = list({nodes_map[n]["component"] for n in visited if n in nodes_map and nodes_map[n].get("component")})

    blocked_issues = _find_cascade_blocked(issue_id, visited, edges, nodes_map)

    root_node = nodes_map.get(issue_id, {})
    return {
        "data": {
            "issue_id": issue_id,
            "issue_title": root_node.get("label", issue_id),
            "issue_status": root_node.get("status", "UNKNOWN"),
            "risk_level": risk_level,
            "directly_affected": direct_affected,
            "transitively_affected": transitive_affected,
            "blocked_issues": blocked_issues,
            "affected_components": affected_components,
            "graph_depth": max(visited.values()) if visited else 0,
            "total_affected": len(direct_affected) + len(transitive_affected),
        }
    }


@app.post("/mock/analysis/root-cause")
def analyze_root_cause(body: RootCauseRequest):
    issues_data = read_json("issues.json")
    issues = issues_data.get("issues", [])
    nodes, edges = _build_dependency_graph()
    nodes_map = {n["id"]: n for n in nodes}

    closed_issues = [i for i in issues if i.get("status") == "CLOSED"]
    results = []

    error_words = set(body.error_message.lower().split())
    test_words = set(body.test_name.lower().replace("_", " ").replace("-", " ").split())
    query_words = error_words | test_words
    query_words -= {"error", "exception", "assertion", "expected", "got", "the", "a", "an", "in", "for", "with", "after", "before", "and", "or", "not"}

    for issue in closed_issues:
        score = 0.0
        reasons = []

        issue_words = set((issue.get("title", "") + " " + issue.get("description", "")).lower().split())
        issue_words -= {"the", "a", "an", "in", "for", "with", "and", "or", "not", "is", "are", "was", "were"}
        overlap = query_words & issue_words
        if overlap:
            keyword_score = min(len(overlap) * 15, 40)
            score += keyword_score
            reasons.append(f"Keyword match ({', '.join(list(overlap)[:3])})")

        issue_labels = set(l.lower() for l in issue.get("labels", []))
        query_labels = set(l.lower() for l in (body.labels or []))
        label_overlap = issue_labels & query_labels
        if label_overlap:
            label_score = min(len(label_overlap) * 12, 30)
            score += label_score
            reasons.append(f"Label match ({', '.join(label_overlap)})")

        if body.component:
            issue_node = nodes_map.get(issue["id"], {})
            issue_component = issue_node.get("component", "")
            if body.component.lower() in issue_component.lower() or issue_component.lower() in body.component.lower():
                score += 15
                reasons.append("Same component")

        if issue.get("closed_at"):
            from datetime import datetime
            closed_dt = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
            days_ago = (datetime.now().astimezone() - closed_dt).days
            if days_ago <= 7:
                score += 10
                reasons.append(f"Recently closed ({days_ago}d ago)")
            elif days_ago <= 30:
                score += 5
                reasons.append(f"Closed within 30d ({days_ago}d ago)")

        graph_distance = 999
        if issue["id"] in {n["id"] for n in nodes}:
            _, _, source_vis, _ = _bfs(issue["id"], edges)
            other_closed = [i for i in closed_issues if i["id"] != issue["id"] and i["id"] in source_vis]
            if other_closed:
                graph_distance = min(source_vis[i["id"]] for i in other_closed)
                if graph_distance <= 3:
                    score += max(0, 15 - graph_distance * 4)
                    reasons.append(f"Graph proximity (distance {graph_distance})")

        if score > 0:
            results.append({
                "issue_id": issue["id"],
                "issue_title": issue["title"],
                "issue_status": issue["status"],
                "confidence": min(round(score, 1), 100),
                "reasons": reasons,
                "graph_distance": graph_distance,
            })

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return {"data": results[:10]}


@app.get("/mock/test-failures")
def get_test_failures():
    data = read_json("root-cause.json")
    return {"data": data.get("test_failures", [])}
