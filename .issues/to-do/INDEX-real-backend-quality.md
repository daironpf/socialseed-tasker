# Real Backend & Quality Backlog — Issue Index

**Source:** `notas.md` (v2 — Known Gaps: integración real, tests/CI, seguridad, accesibilidad)
**Created:** 2026-09-26
**Status:** TODO

> `notas.md` (v2) define las issues como [ISSUE-01]…[ISSUE-08]; el siguiente número
> libre en `.issues/done` era **#516**, por lo que se numeraron **#517–#524**
> conservando el orden y contenido del plan original.

---

## Issue Index

| # | Issue | Priority | Type | Status | notas.md |
|---|---|---|---|---|---|
| #517 | Backend Integration & Live WebSocket/SSE Architecture | CRITICAL | feat / architecture | DONE (→ `.issues/done/`) | [ISSUE-01] |
| #518 | Test Suite & CI/CD Pipeline (Frontend) | HIGH | infra / quality | DONE (→ `.issues/done/`) | [ISSUE-02] |
| #519 | OAuth2 / SSO Authentication & Role-Based Route Protection | HIGH | feat / security | DONE (→ `.issues/done/`) | [ISSUE-03] |
| #520 | Real Persistence & Auto-Healing Pipeline Engine | MEDIUM | feat / core | DONE (→ `.issues/done/`) | [ISSUE-04] |
| #521 | Policy Sandbox Rules Engine | MEDIUM | feat / governance | DONE (→ `.issues/done/`) | [ISSUE-05] |
| #522 | Bidirectional Real Sync with GitHub | MEDIUM | feat / integration | TODO | [ISSUE-06] |
| #523 | Keyboard Navigation & Accessibility (WCAG 2.1) | LOW | accessibility / ux | TODO | [ISSUE-07] |
| #524 | RAG Explorer & MCP Server Integration | MEDIUM | feat / ai infrastructure | TODO | [ISSUE-08] |

---

## Feature Summary

### Foundation
- **#517 Live Backend (DONE):** flag mock/real configurable (UserMenu), API real `/api/v1`, SSE con backoff+jitter+watchdog, estado en `SyncStatusBadge`; backend `realtime.py` (agent-logs + presence)

### Quality
- **#518 Tests & CI (DONE):** Vitest + Vue Test Utils (81 unit tests), Playwright E2E (8 tests), ESLint flat config, job `frontend-ci.yml` en GitHub Actions

### Security
- **#519 Auth & RBAC (DONE):** login JWT + OAuth2 GitHub/Google (PKCE), rotación de refresh tokens con reuse detection, guards de rutas/sidebar/acciones por rol (`can()`), logout que revoca en backend, i18n EN/ES

### Core
- **#520 Auto-Healing Real (DONE):** ejecutor real de pipelines, cancel/restart de etapas en vivo, descarga de `.patch` aplicados

### Governance
- **#521 Rules Engine (DONE):** motor de evaluación de reglas sobre el grafo real, editor avanzado, promoción real a `/policies`

### Integration
- **#522 GitHub Sync:** estados reales, webhooks bidireccionales, resolución de conflictos GitHub↔Tasker

### UX
- **#523 A11y:** atajos `J`/`K`/`Enter` suscritos, focus trap, contraste WCAG 2.1 AA

### AI Infrastructure
- **#524 RAG & MCP:** Neo4j vector real en RAG Explorer, tool calls MCP en vivo con métricas de latencia

---

## Dependencies (suggested order)

1. **#517** (CRITICAL) — flag mock/real y stream son la base de #520, #522, #524
2. **#518, #519** (HIGH) — tests/CI blindan el resto; #519 roles alimentan RBAC de #510/#521
3. **#520, #521, #522, #524** (MEDIUM)
4. **#523** (LOW) — paralelizable en cualquier momento

---

## Related Done Issues

| Done | Relevant to |
|---|---|
| #472, #504, #499, #515, #173 | Realtime/API → #517 |
| #111, #120, #124, #196, #297, #298 | Tests/CI → #518 |
| #69, #107, #122, #155, #162, #437, #303, #310, #509, #510 | Auth/RBAC → #519 |
| #86, #494, #514, #516 | Auto-Healing → #520 |
| #84, #82, #85, #490, #501, #511 | Sandbox/Governance → #521 |
| #88, #89, #93, #95, #307, #500, #515 | GitHub Sync → #522 |
| #467, #468, #508 | Keyboard/A11y → #523 |
| #491, #209, #301, #488 | RAG/MCP → #524 |

---

## Release Checklist (backlog)

- [x] **#517** implemented — DONE 2026-09-26 (moved to `.issues/done/`, `features.md` §62)
- [x] **#518** implemented — DONE 2026-09-27 (moved to `.issues/done/`, `features.md` §63)
- [x] **#519** implemented — DONE 2026-09-27 (moved to `.issues/done/`, `features.md` §64)
- [x] **#520** implemented — DONE 2026-09-27 (moved to `.issues/done/`, `features.md` §65)
- [x] **#521** implemented — DONE 2026-09-28 (moved to `.issues/done/`, `features.md` §66)
- [ ] Remaining 3 issues implemented in `.issues/to-do` order (or by priority)
- [ ] Each issue: `npm run build` green, i18n EN+ES, `features.md` updated
- [ ] Move issue file to `.issues/done/` with `Status: DONE` when complete
- [ ] Commit message references `#NNN`
