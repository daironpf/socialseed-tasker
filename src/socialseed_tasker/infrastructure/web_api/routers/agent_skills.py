"""API router for the agent skills catalog (issue #577).

Agents have their own skill tables next to the human ``skills`` catalog:
``agent_skills`` holds a name plus a large ``behavior`` text describing how an
agent must act to adopt the skill, and ``agent_user_skills`` links agents to
their selected skills. This router exposes the catalog the floating picker in
the user modals reads from (``GET``), creates new entries from the same window
(``POST``), and maintains them (``PUT``/``DELETE``).
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from socialseed_tasker.auth.user_store import PostgresUserStore
from socialseed_tasker.config.storage import get_database_url
from socialseed_tasker.infrastructure.web_api.schemas import (
    AgentSkillCreateRequest,
    AgentSkillResponse,
    AgentSkillUpdateRequest,
    APIResponse,
    Meta,
)

agent_skills_router = APIRouter()


def _pg_store() -> PostgresUserStore:
    """PostgreSQL store for the agent skills catalog (issue #577)."""
    database_url = get_database_url()
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL not configured: TASKER_DATABASE_URL is not set",
        )
    return PostgresUserStore(database_url)


def _to_response(item: dict[str, str]) -> AgentSkillResponse:
    return AgentSkillResponse(id=item["id"], name=item["name"], behavior=item.get("behavior", ""))


@agent_skills_router.get(
    "/agent-skills",
    response_model=APIResponse[list[AgentSkillResponse]],
    summary="List agent skills catalog",
    description="List agent skills (name + behavior) ordered by name (issue #577).",
)
def list_agent_skills() -> APIResponse[list[AgentSkillResponse]]:
    """Read the agent skills catalog (PostgreSQL, issue #577)."""
    items = _pg_store().list_agent_skills()
    return APIResponse(data=[_to_response(item) for item in items], meta=Meta(request_id=None))


@agent_skills_router.post(
    "/agent-skills",
    response_model=APIResponse[AgentSkillResponse],
    status_code=201,
    summary="Create an agent skill",
    description="Insert one agent skill with its behavior text; 409 when taken (issue #577).",
)
def create_agent_skill(body: AgentSkillCreateRequest) -> APIResponse[AgentSkillResponse]:
    """Create a catalog entry; 409 on duplicate slug/name, 422 on empty name (#577)."""
    try:
        item = _pg_store().create_agent_skill(body.name, body.behavior)
    except ValueError as exc:
        if str(exc) == "skill":
            raise HTTPException(status_code=409, detail="agent skill already exists") from exc
        raise HTTPException(status_code=422, detail=f"invalid agent skill name: {body.name!r}") from exc
    return APIResponse(data=_to_response(item), meta=Meta(request_id=None))


@agent_skills_router.put(
    "/agent-skills/{skill_id}",
    response_model=APIResponse[AgentSkillResponse],
    summary="Update an agent skill",
    description="Rename or rewrite the behavior of one agent skill (issue #577).",
)
def update_agent_skill(skill_id: str, body: AgentSkillUpdateRequest) -> APIResponse[AgentSkillResponse]:
    """Partial update; 404 unknown id, 409 name collision, 422 empty name (#577)."""
    try:
        item = _pg_store().update_agent_skill(skill_id, name=body.name, behavior=body.behavior)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="agent skill not found") from exc
    except ValueError as exc:
        if str(exc) == "skill":
            raise HTTPException(status_code=409, detail="agent skill already exists") from exc
        raise HTTPException(status_code=422, detail="invalid agent skill name") from exc
    return APIResponse(data=_to_response(item), meta=Meta(request_id=None))


@agent_skills_router.delete(
    "/agent-skills/{skill_id}",
    response_model=APIResponse[bool],
    summary="Delete an agent skill",
    description="Delete one catalog row; assignments cascade (issue #577).",
)
def delete_agent_skill(skill_id: str) -> APIResponse[bool]:
    """Delete a skill; 404 when the id is unknown (#577)."""
    if not _pg_store().delete_agent_skill(skill_id):
        raise HTTPException(status_code=404, detail="agent skill not found")
    return APIResponse(data=True, meta=Meta(request_id=None))


_MD_HEADING = re.compile(r"^#[ \t]+(.+)$", re.MULTILINE)
_MD_SUFFIXES = {".md", ".markdown"}


def _name_from_markdown(text: str, filename: str) -> str:
    """Skill name from a .md: first ``# heading`` wins, else the file stem."""
    match = _MD_HEADING.search(text)
    if match:
        return match.group(1).strip()
    return Path(filename).stem.replace("-", " ").replace("_", " ").strip()


@agent_skills_router.post(
    "/agent-skills/import",
    response_model=APIResponse[AgentSkillResponse],
    status_code=201,
    summary="Import an agent skill from a .md file",
    description=(
        "Upload one markdown file; the skill name comes from the first '# heading' "
        "(or the file stem) and the whole file becomes the behavior text (issue #610)."
    ),
)
async def import_agent_skill(file: UploadFile = File(...)) -> APIResponse[AgentSkillResponse]:  # noqa: B008
    """Create a catalog entry from an uploaded .md; 409 duplicate, 422 bad input."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _MD_SUFFIXES:
        raise HTTPException(status_code=422, detail="file must be a .md or .markdown document")
    raw = await file.read()
    try:
        text = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="file must be UTF-8 markdown") from exc
    if not text:
        raise HTTPException(status_code=422, detail="markdown file is empty")
    name = _name_from_markdown(text, file.filename or "skill")
    if not name:
        raise HTTPException(status_code=422, detail="could not derive a skill name from the file")
    if len(name) > 80:
        raise HTTPException(status_code=422, detail="derived skill name exceeds 80 characters")
    if len(text) > 20000:
        raise HTTPException(status_code=422, detail="markdown exceeds the 20000 char behavior limit")
    try:
        item = _pg_store().create_agent_skill(name, text)
    except ValueError as exc:
        if str(exc) == "skill":
            raise HTTPException(status_code=409, detail="agent skill already exists") from exc
        raise HTTPException(status_code=422, detail=f"invalid agent skill name: {name!r}") from exc
    return APIResponse(data=_to_response(item), meta=Meta(request_id=None))
