"""GraphQL server — FastAPI app wired with Ariadne and the default container."""

from __future__ import annotations

import os

from ariadne import load_schema_from_path, make_executable_schema
from ariadne.asgi import GraphQL
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from socialseed_tasker.graphql import SDL_PATH
from socialseed_tasker.graphql.resolvers import mutation, query, subscription
from socialseed_tasker.cli.wiring import build_default_container

SDL_EXPORT = os.path.join(os.path.dirname(SDL_PATH), "schema_export.graphql")

type_defs = load_schema_from_path(SDL_PATH)
schema = make_executable_schema(type_defs, [query, mutation, subscription])


def get_user_from_header(auth_header: str, container):
    if not auth_header:
        return None
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        return container.auth.verify_token(token)
    return None


def create_app():
    container = build_default_container()
    app = FastAPI(title="Tasker GraphQL", version="0.1.0")
    allow_origins_env = os.getenv("TASKER_API_ALLOW_ORIGINS", "http://localhost:8080")
    allow_origins = [o.strip() for o in allow_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if os.getenv("TASKER_EXPORT_GRAPHQL") == "1":
        with open(SDL_EXPORT, "w", encoding="utf-8") as fh:
            fh.write(type_defs)
    graphql_app = GraphQL(schema, debug=os.getenv("TASKER_DEBUG", "0") == "1")

    async def asgi_app(scope, receive, send):
        request = Request(scope, receive=receive)
        auth = request.headers.get("authorization")
        user_id = get_user_from_header(auth, container)
        scope["container"] = container
        scope["user_id"] = user_id
        await graphql_app(scope, receive, send)

    app.add_route("/graphql", graphql_app)
    app.add_websocket_route("/graphql/ws", graphql_app)

    @app.middleware("http")
    async def attach_container(request, call_next):
        request.state.container = container
        return await call_next(request)

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("TASKER_GRAPHQL_PORT", "8081")))
