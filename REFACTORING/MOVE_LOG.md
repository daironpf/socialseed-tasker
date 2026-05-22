# Module Migration Log

## Layer mapping: `socialseed_tasker.{domain,application,infrastructure,cli}`

### Domain layer (pure entities, value objects, rules)

| Original path | New path | Reason |
|---|---|---|
| `core/task_management/entities.py` | `domain/entities.py` | Domain entities (Issue, Component, Epic, etc.) |
| `core/task_management/value_objects.py` | `domain/value_objects.py` | Value objects |
| `core/validation/exceptions.py` | `domain/exceptions.py` | Domain exceptions |
| `core/validation/validators.py` | `domain/validators.py` | Domain validation rules |
| `core/validation/input_sanitizer.py` | `domain/input_sanitizer.py` | Input sanitization |
| `core/code_analysis/entities.py` | `domain/code_analysis_entities.py` | Code analysis entities |
| `core/system_init/entities.py` | `domain/system_init_entities.py` | System init entities |
| `core/project_analysis/rules.py` | `domain/architectural_rules.py` | Architectural rules |
| `core/task_management/__init__.py` | _(removed)_ | Split into domain + application |
| `core/code_analysis/__init__.py` | _(removed)_ | Split into domain + infrastructure |
| `core/project_analysis/__init__.py` | _(removed)_ | Split into domain + application |
| `core/system_init/__init__.py` | _(removed)_ | Merged into domain + application |
| `core/validation/__init__.py` | _(removed)_ | Merged into domain |

### Application layer (use cases, services, ports, policies)

| Original path | New path | Reason |
|---|---|---|
| `core/task_management/actions.py` | `application/actions.py` | Use cases |
| `core/task_management/constraints.py` | `application/constraints.py` | Constraint engine |
| `core/project_analysis/analyzer.py` | `application/analyzer.py` | Project/impact analyzer |
| `core/project_analysis/policy.py` | `application/policy.py` | Policy engine |
| `core/code_analysis/integrity.py` | `application/integrity.py` | Integrity analysis |
| `core/system_init/scaffolder.py` | `application/scaffolder.py` | Scaffolding use case |
| `core/services/markdown_transformer.py` | `application/markdown_transformer.py` | Markdown service |
| `core/services/secret_manager.py` | `application/secret_manager.py` | Secret management service |
| `bootstrap/container.py` | `application/container.py` | DI container |
| `bootstrap/wiring.py` | `application/wiring.py` | Dependency wiring |

### Infrastructure layer (adapters, drivers, external services)

| Original path | New path | Reason |
|---|---|---|
| `storage/graph_database/driver.py` | `infrastructure/neo4j_driver.py` | Neo4j driver |
| `storage/graph_database/queries.py` | `infrastructure/neo4j_queries.py` | Neo4j queries |
| `storage/graph_database/repositories.py` | `infrastructure/neo4j_repository.py` | Neo4j repository |
| `storage/graph_database/code_graph_repository.py` | `infrastructure/neo4j_code_graph_repository.py` | Neo4j code graph |
| `storage/graph_database/commit_repository.py` | `infrastructure/neo4j_commit_repository.py` | Neo4j commits |
| `storage/graph_database/policy_repository.py` | `infrastructure/neo4j_policy_repository.py` | Neo4j policies |
| `storage/graph_database/rag_repository.py` | `infrastructure/neo4j_rag_repository.py` | Neo4j RAG |
| `storage/graph_database/reasoning_repository.py` | `infrastructure/neo4j_reasoning_repository.py` | Neo4j reasoning |
| `storage/graph_database/user_repository.py` | `infrastructure/neo4j_user_repository.py` | Neo4j users |
| `storage/graph_database/impl/__init__.py` | `infrastructure/neo4j_impl/__init__.py` | Neo4j impl package |
| `storage/graph_database/impl/shared.py` | `infrastructure/neo4j_impl/shared.py` | Shared neo4j helpers |
| `storage/graph_database/impl/issue_mixin.py` | `infrastructure/neo4j_impl/issue_mixin.py` | Issue repository mixin |
| `storage/graph_database/impl/component_mixin.py` | `infrastructure/neo4j_impl/component_mixin.py` | Component repository mixin |
| `storage/graph_database/impl/constraint_mixin.py` | `infrastructure/neo4j_impl/constraint_mixin.py` | Constraint repository mixin |
| `storage/graph_database/impl/epic_mixin.py` | `infrastructure/neo4j_impl/epic_mixin.py` | Epic repository mixin |
| `storage/graph_database/impl/label_mixin.py` | `infrastructure/neo4j_impl/label_mixin.py` | Label repository mixin |
| `storage/graph_database/impl/cost_mixin.py` | `infrastructure/neo4j_impl/cost_mixin.py` | Cost analytics mixin |
| `storage/graph_database/impl/deployment_mixin.py` | `infrastructure/neo4j_impl/deployment_mixin.py` | Deployment mixin |
| `storage/graph_database/impl/vector_mixin.py` | `infrastructure/neo4j_impl/vector_mixin.py` | Vector search mixin |
| `storage/graph_database/migrations/v090.py` | `infrastructure/neo4j_migrations/v090.py` | DB migration |
| `storage/adapters/github/__init__.py` | `infrastructure/github_adapter.py` | GitHub adapter |
| `core/code_analysis/parser.py` | `infrastructure/code_parser.py` | Tree-sitter parser |
| `core/services/embedding_service.py` | `infrastructure/embedding_service.py` | Embedding service |
| `core/services/connectivity_manager.py` | `infrastructure/connectivity_manager.py` | Network connectivity |
| `core/services/github_issue_mapper.py` | `infrastructure/github_issue_mapper.py` | GitHub issue mapping |
| `core/services/github_mirror.py` | `infrastructure/github_mirror.py` | GitHub mirror |
| `core/services/sync_engine.py` | `infrastructure/sync_engine.py` | Sync engine |
| `core/services/webhook_validator.py` | `infrastructure/webhook_validator.py` | Webhook validation |
| `entrypoints/web_api/__init__.py` | `infrastructure/web_api/__init__.py` | Web API package |
| `entrypoints/web_api/__main__.py` | `infrastructure/web_api/__main__.py` | Web API main |
| `entrypoints/web_api/api.py` | `infrastructure/web_api/api.py` | Web API config |
| `entrypoints/web_api/api_neo4j.py` | `infrastructure/web_api/api_neo4j.py` | Web API neo4j setup |
| `entrypoints/web_api/app.py` | `infrastructure/web_api/app.py` | FastAPI app |
| `entrypoints/web_api/routes.py` | `infrastructure/web_api/routes.py` | Web API routes |
| `entrypoints/web_api/schemas.py` | `infrastructure/web_api/schemas.py` | API schemas |
| `entrypoints/web_api/routers/` | `infrastructure/web_api/routers/` | API routers |

### CLI layer (entry points, terminal commands)

| Original path | New path | Reason |
|---|---|---|
| `entrypoints/terminal_cli/__init__.py` | `cli/__init__.py` | CLI package |
| `entrypoints/terminal_cli/app.py` | `cli/app.py` | CLI app |
| `entrypoints/terminal_cli/commands/` | `cli/commands/` | CLI commands package |
| `entrypoints/terminal_cli/formatters/__init__.py` | `cli/formatters.py` | CLI formatters |
| `entrypoints/terminal_cli/utils/__init__.py` | `cli/utils.py` | CLI utilities |
| `entrypoints/terminal_cli/utils/resolver.py` | `cli/resolver.py` | CLI resolvers |
| `entrypoints/terminal_cli/cmd/storage.py` | `cli/cmd_storage.py` | Storage commands |
| `entrypoints/cli/__init__.py` | `cli/init_cli.py` | Init CLI |
| `entrypoints/cli/init_command.py` | `cli/init_command.py` | Init command |
| `entrypoints/__init__.py` | _(removed)_ | Merged into cli |
| `assets/templates/skills/task_skill.py` | `cli/task_skill_template.py` | Template for skills |

## Status: COMPLETED (2026-05-22)

### Old directories removed
- `core/` ✅ Removed (all contents moved to domain/, application/, infrastructure/)
- `storage/` ✅ Removed (all contents moved to infrastructure/)
- `bootstrap/` ✅ Removed (all contents moved to application/)
- `entrypoints/` ✅ Removed (CLI → cli/, Web API → infrastructure/web_api/)

### New package structure
```
src/socialseed_tasker/
├── application/   # Use cases, services, ports, orchestration
├── assets/        # Frontend builds, templates
├── cli/           # Typer CLI (commands/, app.py, resolver.py, utils.py, formatters.py, init_command.py)
├── domain/        # Pure entities, value objects, business rules
└── infrastructure/# Adapters, drivers, external services
    ├── neo4j_driver.py
    ├── neo4j_queries.py
    ├── neo4j_repository.py
    ├── neo4j_code_graph_repository.py
    ├── neo4j_commit_repository.py
    ├── neo4j_policy_repository.py
    ├── neo4j_rag_repository.py
    ├── neo4j_reasoning_repository.py
    ├── neo4j_user_repository.py
    ├── neo4j_impl/       # Repository mixins (issue, component, epic, etc.)
    ├── neo4j_migrations/ # DB migrations
    ├── web_api/          # FastAPI app, routers, schemas
    ├── code_parser.py
    ├── embedding_service.py
    ├── github_adapter.py
    ├── sync_engine.py
    └── ... (adapters)
```

### Verification
- **Tests**: 745 passed, 1 skipped, 0 failed
- **Imports**: All 88+ source files and 39 test files updated automatically via fix_imports.py
- **pyproject.toml**: Entry points updated (socialseed-tasker → cli.app), ruff per-file-ignores updated
- **Templates path**: Fixed `_get_template_dir()` in cli/init_command.py (removed extra `.parent`)

### Files moved: 100+ across infrastructure + CLI layers
| Layer | Files moved |
|-------|-------------|
| infrastructure/ | `driver→neo4j_driver`, `queries→neo4j_queries`, `repositories→neo4j_repository`, all repos renamed, all impl/ mixins, migrations, web_api/, code_parser, embedding_service, all services, github_adapter |
| cli/ | `app`, `commands/`, `formatters`, `utils`, `resolver`, `cmd_storage`, `init_command`, `init_cli`, `task_skill_template` |
