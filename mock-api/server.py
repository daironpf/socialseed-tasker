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
