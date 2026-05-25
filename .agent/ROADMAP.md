# Project Roadmap

**Last updated**: 2026-05-24

## Phase 1: Foundations
- [x] Environment Setup
- [x] Core Entities Definition
- [x] Basic API/CLI implementation

## Phase 2: Knowledge & Discovery
- [x] Code Graph Integration (Tree-sitter)
- [x] Semantic Search (RAG with Neo4j vector index)

## Phase 3: Autonomous Testing
- [x] Agent Reasoning Implementation (ReasoningNode)
- [x] Automated Test Suites (500+ unit tests)

## Phase 4: High-Level Autonomy (v1.0.0+)
- [x] Bidirectional Traceability (AFFECTS relationship)
- [x] Phantom Dependency Detection (RAG semantic similarity)
- [x] ARCHITECT Agent (constraint validation)
- [x] Agent Registration & Specialization
- [x] Epic & Objective Tracking

## Phase 5: Hexagonal Refactoring & CI
- [x] Protocol Ports with conformance tests (#290)
- [x] Neo4jGraphAdapter with retries (#291)
- [x] TreeSitterParser adapter (#292)
- [x] Repository interfaces + Neo4j implementations (#293)
- [x] Thin CLI refactor (#294)
- [x] Application use cases (#295)
- [x] Domain test suite (#296)
- [x] GitHub Actions CI workflow (#297)

## Phase 6: Developer Tooling & Observability
- [x] Pre-commit hooks and linters configuration (#298)
- [x] Structured logging, metrics, and Prometheus exporter (#299)

## Phase 7: Infrastructure & Integrations
- [x] Docker Compose dev environment (#300)
- [x] FAISS local vector store / Embedding adapter (#301)
- [x] CHANGELOG and semantic versioning (#302)
- [x] Authentication and RBAC (#303)
- [x] Redis adapter with in-memory fallback (#304)
- [x] Celery background worker (#305)
- [x] FastAPI server + Vue.js board (#306)
- [x] Webhook receiver and event bus (#307)
- [x] GraphQL API with subscriptions (#308)
- [x] Grafana dashboards (#309)
- [x] SSO / OAuth2 with Keycloak (#310)
- [x] Rate limiting and abuse protection (#311)
- [x] Chaos testing harness (#312)
- [x] Data export and backup (#313)
- [x] Multi-tenant support (#314)
- [x] OpenTelemetry / Jaeger tracing (#315)
- [x] Feature flags (#316)
- [x] GDPR compliance / data retention (#317)
- [x] ML model serving and feature store (#318)
- [x] Data catalog and schema registry (#319)
- [x] Data quality framework (#320)
- [x] Graph visualization and impact analysis (#321)
- [x] Deterministic changelog generator (#322)
- [x] API contract testing and mock server (#323)
- [x] Secrets management and rotation (#324)
- [x] Hardened CI/CD pipelines and release automation (#325)

---

## Known Issues
| # | Description | Severity | Location | Status |
|---|-------------|----------|----------|--------|
| 1 | Initial setup pending | Low | Root | COMPLETED |
