"""Mock API server that persists data to JSON files."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body
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
def get_issues(page: int = 1, limit: int = 200, status: str = None, priority: str = None):
    data = read_json("issues.json")
    issues = data.get("issues", [])
    if status:
        allowed = [s.strip() for s in status.split(",")]
        issues = [i for i in issues if i.get("status") in allowed]
    if priority:
        allowed = [p.strip() for p in priority.split(",")]
        issues = [i for i in issues if i.get("priority") in allowed]
    return {"data": issues, "meta": {"total": len(issues)}}


@app.post("/mock/issues")
def create_issue(body: IssueCreate):
    data = read_json("issues.json")
    issues = data.get("issues", [])

    max_id = max((int(i["id"].split("-")[1]) for i in issues if i["id"].startswith("ISS-")), default=0)
    new_id = f"ISS-{max_id + 1:03d}"
    now = __import__("datetime").datetime.utcnow().isoformat() + "Z"
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
        "blocks": [],
        "affects": [],
        "architectural_constraints": [],
        "created_at": now,
        "updated_at": now,
        "closed_at": None,
        "agent_working": False,
    }

    issues.append(new_issue)
    data["issues"] = issues
    write_json("issues.json", data)
    return {"data": new_issue}


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    component_id: Optional[str] = None
    assignee: Optional[str] = None
    labels: Optional[list[str]] = None
    dependencies: Optional[list[str]] = None
    blocks: Optional[list[str]] = None
    affects: Optional[list[str]] = None
    architectural_constraints: Optional[list[str]] = None
    closed_at: Optional[str] = None
    agent_working: Optional[bool] = None


@app.patch("/mock/issues/{issue_id}")
def update_issue(issue_id: str, body: IssueUpdate):
    data = read_json("issues.json")
    issues = data.get("issues", [])
    idx = next((i for i, iss in enumerate(issues) if iss["id"] == issue_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    update_data = body.model_dump(exclude_unset=True)
    now = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    update_data["updated_at"] = now
    issues[idx].update(update_data)
    data["issues"] = issues
    write_json("issues.json", data)
    return {"data": issues[idx]}


@app.delete("/mock/issues/{issue_id}")
def delete_issue(issue_id: str):
    data = read_json("issues.json")
    issues = data.get("issues", [])
    idx = next((i for i, iss in enumerate(issues) if iss["id"] == issue_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    issues.pop(idx)
    data["issues"] = issues
    write_json("issues.json", data)
    return {"data": None}


@app.get("/mock/issues/{issue_id}/agent-logs")
def get_agent_logs(issue_id: str):
    data = read_json("agent-logs.json")
    logs = data.get("agent_logs", {}).get(issue_id, None)
    if not logs:
        return {"data": {"issue_id": issue_id, "logs": []}}
    return {"data": logs}


@app.get("/mock/components")
def get_components():
    data = read_json("components.json")
    return {"data": data.get("components", [])}


class ComponentCreate(BaseModel):
    name: str
    alias: Optional[str] = None
    description: Optional[str] = None
    project: str = "socialseed-tasker"


class ComponentUpdate(BaseModel):
    name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    project: Optional[str] = None


@app.post("/mock/components")
def create_component(body: ComponentCreate):
    data = read_json("components.json")
    components = data.get("components", [])
    new_id = str(__import__("uuid").uuid4())
    now = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    new_comp = {
        "id": new_id,
        "name": body.name,
        "alias": body.alias or body.name[:2].upper(),
        "description": body.description,
        "project": body.project,
        "created_at": now,
        "updated_at": now,
    }
    components.append(new_comp)
    data["components"] = components
    write_json("components.json", data)
    return {"data": new_comp}


@app.patch("/mock/components/{component_id}")
def update_component(component_id: str, body: ComponentUpdate):
    data = read_json("components.json")
    components = data.get("components", [])
    idx = next((i for i, c in enumerate(components) if c["id"] == component_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Component not found")
    update_data = body.model_dump(exclude_unset=True)
    update_data["updated_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    components[idx].update(update_data)
    data["components"] = components
    write_json("components.json", data)
    return {"data": components[idx]}


@app.delete("/mock/components/{component_id}")
def delete_component(component_id: str):
    data = read_json("components.json")
    components = data.get("components", [])
    idx = next((i for i, c in enumerate(components) if c["id"] == component_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Component not found")
    components.pop(idx)
    data["components"] = components
    write_json("components.json", data)
    return {"data": None}


@app.get("/mock/policies")
def get_policies():
    data = read_json("policies.json")
    return {"data": data.get("policies", [])}


class PolicyCreate(BaseModel):
    name: str
    description: str = ""
    rule: str = ""
    level: str = "SOFT"
    target_scope: str = "project"


@app.post("/mock/policies")
def create_policy(body: PolicyCreate):
    data = read_json("policies.json")
    policies = data.get("policies", [])
    now = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    new_policy = {
        "id": str(__import__("uuid").uuid4()),
        "name": body.name,
        "description": body.description,
        "rules": [{"type": body.rule}] if body.rule else [],
        "target_scope": body.target_scope,
        "logic_definition": "",
        "remediation_strategy": "",
        "autofix_template": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    policies.append(new_policy)
    data["policies"] = policies
    write_json("policies.json", data)
    return {"data": new_policy}


@app.delete("/mock/policies/{policy_id}")
def delete_policy(policy_id: str):
    data = read_json("policies.json")
    policies = data.get("policies", [])
    policies = [p for p in policies if p["id"] != policy_id]
    data["policies"] = policies
    write_json("policies.json", data)
    return {"data": None}


@app.patch("/mock/policies/{policy_id}")
def update_policy(policy_id: str, body: dict = Body(...)):
    data = read_json("policies.json")
    policies = data.get("policies", [])
    for p in policies:
        if p["id"] == policy_id:
            for key, value in body.items():
                if key != "id":
                    p[key] = value
            p["updated_at"] = datetime.now(timezone.utc).isoformat()
            write_json("policies.json", data)
            return {"data": p}
    raise HTTPException(status_code=404, detail="Policy not found")


@app.get("/mock/constraints")
def get_constraints():
    data = read_json("constraints.json")
    return {"data": data.get("constraints", [])}


class ConstraintCreate(BaseModel):
    name: str
    description: str = ""
    category: str = "ARCHITECTURE"
    severity: str = "SOFT"
    scope: str = "project"
    rule: dict = {}
    logic: str = ""
    remediation: str = ""
    auto_fix: bool = False


@app.post("/mock/constraints")
def create_constraint(body: ConstraintCreate):
    data = read_json("constraints.json")
    constraints = data.get("constraints", [])
    max_id = max((int(c["id"].split("-")[1]) for c in constraints if c["id"].startswith("CONST-")), default=0)
    new_id = f"CONST-{max_id + 1:03d}"
    now = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    new_constraint = {
        "id": new_id,
        "name": body.name,
        "description": body.description,
        "category": body.category,
        "severity": body.severity,
        "scope": body.scope,
        "rule": body.rule,
        "logic": body.logic,
        "remediation": body.remediation,
        "auto_fix": body.auto_fix,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    constraints.append(new_constraint)
    data["constraints"] = constraints
    write_json("constraints.json", data)
    return {"data": new_constraint}


@app.patch("/mock/constraints/{constraint_id}")
def update_constraint(constraint_id: str, body: ConstraintCreate):
    data = read_json("constraints.json")
    constraints = data.get("constraints", [])
    for i, c in enumerate(constraints):
        if c["id"] == constraint_id:
            now = __import__("datetime").datetime.utcnow().isoformat() + "Z"
            constraints[i] = {
                **c,
                "name": body.name,
                "description": body.description,
                "category": body.category,
                "severity": body.severity,
                "scope": body.scope,
                "rule": body.rule,
                "logic": body.logic,
                "remediation": body.remediation,
                "auto_fix": body.auto_fix,
                "updated_at": now,
            }
            data["constraints"] = constraints
            write_json("constraints.json", data)
            return {"data": constraints[i]}
    raise HTTPException(status_code=404, detail="Constraint not found")


class ValidateRequest(BaseModel):
    entity_type: str = "issue"
    entity_data: dict = {}


@app.post("/mock/constraints/validate")
def validate_constraints(body: ValidateRequest):
    data = read_json("constraints.json")
    constraints = data.get("constraints", [])
    issues_data = read_json("issues.json")
    issues = issues_data.get("issues", [])
    deps_data = read_json("dependencies.json")
    deps = deps_data.get("dependencies", {})
    components_data = read_json("components.json")
    components = components_data.get("components", [])

    violations = []
    active_constraints = [c for c in constraints if c.get("is_active")]

    entity = body.entity_data
    entity_type = body.entity_type

    for c in active_constraints:
        if c["category"] == "DEPENDENCIES" and c["rule"].get("type") == "no_cycles":
            edges = deps.get("edges", [])
            nodes = {n["id"]: n for n in deps.get("nodes", [])}
            for issue in issues:
                if issue["id"] not in nodes:
                    nodes[issue["id"]] = {"id": issue["id"], "label": issue["title"]}
            visited = set()
            path = set()

            def _has_cycle(node_id, all_edges):
                visited.add(node_id)
                path.add(node_id)
                for edge in all_edges:
                    if edge["from"] == node_id and edge["to"] not in visited:
                        if _has_cycle(edge["to"], all_edges):
                            return True
                    elif edge["from"] == node_id and edge["to"] in path:
                        return True
                path.discard(node_id)
                return False

            cycle_found = False
            for node_id in list(nodes.keys()):
                if node_id not in visited:
                    if _has_cycle(node_id, edges):
                        cycle_found = True
                        break

            if cycle_found:
                violations.append({
                    "constraint_id": c["id"],
                    "constraint_name": c["name"],
                    "severity": c["severity"],
                    "category": c["category"],
                    "message": "Circular dependency detected in the dependency graph",
                    "remediation": c["remediation"],
                })

        if c["category"] == "DEPENDENCIES" and c["rule"].get("type") == "max_depth":
            max_depth_val = deps.get("summary", {}).get("critical_path_length", 0)
            max_allowed = c["rule"].get("max_value", 8)
            if max_depth_val > max_allowed:
                violations.append({
                    "constraint_id": c["id"],
                    "constraint_name": c["name"],
                    "severity": c["severity"],
                    "category": c["category"],
                    "message": f"Dependency depth ({max_depth_val}) exceeds maximum ({max_allowed})",
                    "remediation": c["remediation"],
                })

        if entity_type == "issue" and c["rule"].get("type") == "required_field":
            field = c["rule"].get("target_field", "")
            min_count = c["rule"].get("min_count", 1)
            val = entity.get(field)
            if val is None or (isinstance(val, list) and len(val) < min_count):
                violations.append({
                    "constraint_id": c["id"],
                    "constraint_name": c["name"],
                    "severity": c["severity"],
                    "category": c["category"],
                    "message": c["rule"].get("message", f"Field '{field}' is required"),
                    "remediation": c["remediation"],
                })

        if entity_type == "issue" and c["rule"].get("type") == "max_count":
            field = c["rule"].get("target_field", "")
            max_val = c["rule"].get("max_value", 5)
            val = entity.get(field, [])
            if isinstance(val, list) and len(val) > max_val:
                violations.append({
                    "constraint_id": c["id"],
                    "constraint_name": c["name"],
                    "severity": c["severity"],
                    "category": c["category"],
                    "message": f"Field '{field}' has {len(val)} items, max allowed is {max_val}",
                    "remediation": c["remediation"],
                })

        if entity_type == "component" and c["rule"].get("type") == "regex_pattern":
            import re
            field = c["rule"].get("target_field", "")
            pattern = c["rule"].get("pattern", "")
            val = entity.get(field, "")
            if val and not re.match(pattern, val):
                violations.append({
                    "constraint_id": c["id"],
                    "constraint_name": c["name"],
                    "severity": c["severity"],
                    "category": c["category"],
                    "message": c["rule"].get("message", f"Field '{field}' does not match pattern"),
                    "remediation": c["remediation"],
                })

        if entity_type == "component" and c["rule"].get("type") == "forbidden_tech":
            field = c["rule"].get("target_field", "")
            blocked = [v.lower() for v in c["rule"].get("blocked_values", [])]
            deps_list = entity.get(field, [])
            if isinstance(deps_list, list):
                for dep in deps_list:
                    if dep.lower() in blocked:
                        violations.append({
                            "constraint_id": c["id"],
                            "constraint_name": c["name"],
                            "severity": c["severity"],
                            "category": c["category"],
                            "message": c["rule"].get("message", f"Technology '{dep}' is prohibited"),
                            "remediation": c["remediation"],
                        })

    hard_count = len([v for v in violations if v["severity"] == "HARD"])
    soft_count = len([v for v in violations if v["severity"] == "SOFT"])

    return {
        "data": {
            "valid": len(violations) == 0,
            "hard_violations": hard_count,
            "soft_violations": soft_count,
            "total_violations": len(violations),
            "violations": violations,
            "checked_constraints": len(active_constraints),
        }
    }


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


# ==================== SYSTEM ENDPOINTS ====================


@app.get("/mock/health")
def get_health():
    issues_data = read_json("issues.json")
    components_data = read_json("components.json")
    users_data = read_json("users.json")
    constraints_data = read_json("constraints.json")

    issues = issues_data.get("issues", [])
    components = components_data.get("components", [])
    users = users_data.get("users", [])
    constraints = constraints_data.get("constraints", [])

    agents_working = [u for u in users if u.get("type") == "agent" and u.get("is_active")]
    blocked_issues = [i for i in issues if i.get("status") == "BLOCKED"]

    return {
        "data": {
            "status": "healthy",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "services": {
                "neo4j": {
                    "status": "connected",
                    "latency_ms": 12,
                    "last_check": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                },
                "api": {
                    "status": "running",
                    "uptime_seconds": 864000,
                    "version": "1.0.0",
                },
                "workers": {
                    "status": "running",
                    "active_count": 2,
                    "queue_size": 5,
                },
            },
            "metrics": {
                "total_issues": len(issues),
                "blocked_issues": len(blocked_issues),
                "total_components": len(components),
                "agents_working": len(agents_working),
                "total_users": len(users),
                "total_constraints": len(constraints),
                "active_constraints": len([c for c in constraints if c.get("is_active")]),
            },
        }
    }


@app.get("/mock/sync-queue")
def get_sync_queue():
    return {
        "data": {
            "pending": 3,
            "queue": [
                {
                    "id": "SYNC-001",
                    "action": "push",
                    "resource": "issues",
                    "resource_id": "ISS-042",
                    "created_at": "2026-09-11T08:30:00Z",
                    "status": "pending",
                    "retry_count": 0,
                },
                {
                    "id": "SYNC-002",
                    "action": "push",
                    "resource": "components",
                    "resource_id": "550e8400-e29b-41d4-a716-446655440105",
                    "created_at": "2026-09-11T08:45:00Z",
                    "status": "pending",
                    "retry_count": 0,
                },
                {
                    "id": "SYNC-003",
                    "action": "pull",
                    "resource": "issues",
                    "resource_id": "ISS-100",
                    "created_at": "2026-09-11T09:00:00Z",
                    "status": "retrying",
                    "retry_count": 2,
                },
            ],
            "last_sync_at": "2026-09-11T08:15:00Z",
            "github_connected": True,
        }
    }


class SeedRequest(BaseModel):
    seed_type: str = "full"
    reset_first: bool = False


@app.post("/mock/admin/seed")
def admin_seed(body: SeedRequest):
    seed_type = body.seed_type

    if body.reset_first:
        for filename in ["issues.json", "components.json", "users.json", "policies.json", "constraints.json", "agent-logs.json", "dependencies.json"]:
            write_json(filename, {})

    return {
        "data": {
            "status": "success",
            "message": f"Seed data loaded ({seed_type})",
            "seed_type": seed_type,
            "reset_first": body.reset_first,
            "loaded": {
                "issues": 100,
                "components": 5,
                "users": 8,
                "policies": 5,
                "constraints": 25,
            },
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        }
    }


@app.post("/mock/admin/reset")
def admin_reset():
    for filename in ["issues.json", "components.json", "users.json", "policies.json", "constraints.json", "agent-logs.json", "dependencies.json"]:
        write_json(filename, {})

    return {
        "data": {
            "status": "success",
            "message": "All data reset to empty",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        }
    }
