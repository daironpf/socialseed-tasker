# SocialSeed Tasker - Frontend Feature Inventory

> Complete catalog of all UI features, interactions, and capabilities currently implemented.
> Use this document to identify gaps, plan new features, and track what is missing.
> Last updated: 2026-10-04

---

## Table of Contents

1. [Global Infrastructure](#1-global-infrastructure)
2. [Authentication](#2-authentication)
3. [Layout & Navigation](#3-layout--navigation)
4. [Dashboard (BoardView)](#4-dashboard-boardview)
5. [Issues List (ListView)](#5-issues-list-listview)
6. [Kanban Board (KanbanView)](#6-kanban-board-kanbanview)
7. [Issue Detail Panel (IssueDetailView)](#7-issue-detail-panel-issuedetailview)
8. [Components Management (ComponentsView)](#8-components-management-componentsview)
9. [Policies Management (PoliciesView)](#9-policies-management-policiesview)
10. [Constraints Management (ConstraintsView)](#10-constraints-management-constraintsview)
11. [Users Management (UsersView)](#11-users-management-usersview)
12. [Dependency Graph (GraphView)](#12-dependency-graph-graphview)
13. [Impact & Root Cause Analysis (AnalysisView)](#13-impact--root-cause-analysis-analysisview)
14. [System Dashboard (DashboardSystemView)](#14-system-dashboard-dashboardsystemview)
15. [User Profile (ProfileView)](#15-user-profile-profileview)
16. [Authentication Screen (LoginScreen)](#16-authentication-screen-loginscreen)
17. [Shared UI Components](#17-shared-ui-components)
18. [Real-Time & Presence Features](#18-real-time--presence-features)
19. [Export & Data Features](#19-export--data-features)
20. [Keyboard Shortcuts & Command Palette](#20-keyboard-shortcuts--command-palette)
21. [Notifications System](#21-notifications-system)
22. [Data Layer (Stores)](#22-data-layer-stores)
23. [API Layer](#23-api-layer)
24. [Type System](#24-type-system)
25. [CRUD Matrix](#25-crud-matrix)
26. [Interactions Matrix](#26-interactions-matrix)
27. [i18n Coverage](#27-i18n-coverage)
28. [Chat System (ChatView)](#28-chat-system-chatview)
29. [Floating Chat Widget (FloatingChat)](#29-floating-chat-widget-floatingchat)
30. [MCP Inspector (MCPInspectorView)](#30-mcp-inspector-mcpinspectorview)
31. [HITL Command Center (HITLCommandCenter)](#31-hitl-command-center-hitlcommandcenter)
32. [Policy Sandbox (PolicySandboxView)](#32-policy-sandbox-policysandboxview)
33. [Graph RAG Explorer (GraphRAGExplorerView)](#33-graph-rag-explorer-graphragexplorerview)
34. [Agent FinOps Dashboard (AgentFinOpsView)](#34-agent-finops-dashboard-agentfinopsview)
35. [Auto-Healing Pipeline Monitor (AutoHealingMonitorView)](#35-auto-healing-pipeline-monitor-autohealingmonitorview)
36. [Agent Replay Player (AgentReplayView)](#36-agent-replay-player-agentreplayview)
37. [Executive Dashboard (ExecutiveDashboardView)](#37-executive-dashboard-executivedashboardview)
38. [PII & Secrets Guardrail](#38-pii--secrets-guardrail)
39. [Code Graph Overlay](#39-code-graph-overlay)
40. [GitHub Sync Widget](#40-github-sync-widget)
41. [Governance Validation Modal](#41-governance-validation-modal)
42. [Network Status & Sync Indicator](#42-network-status--sync-indicator)
43. [Agent Timer & Kill Switch](#43-agent-timer--kill-switch)
44. [Tech Debt & Affected Files](#44-tech-debt--affected-files)
45. [Project Filtering](#45-project-filtering)
46. [Advanced Multi-Criteria Filters](#46-advanced-multi-criteria-filters)
47. [Mock Event Stream (SSE Simulation)](#47-mock-event-stream-sse-simulation)
48. [Mobile Responsive Design](#48-mobile-responsive-design)
49. [Route & View Inventory](#49-route--view-inventory)
50. [Known Gaps & Missing Features](#50-known-gaps--missing-features)
51. [Organization Multi-Tenancy & Enterprise Settings](#51-organization-multi-tenancy--enterprise-settings)
52. [Governance Matrix, RBAC & Approval Queue](#52-governance-matrix-rbac--approval-queue)
53. [Audit Log, Compliance & PII Redaction Suite](#53-audit-log-compliance--pii-redaction-suite)
54. [Agent Studio (Mock Agent Simulator & Custom Agent Builder)](#54-agent-studio-mock-agent-simulator--custom-agent-builder)
55. [Custom Dashboards, Reporting Engine & SLA Metrics](#55-custom-dashboards-reporting-engine--sla-metrics)
56. [Offline First & Mock Sync Queue](#56-offline-first--mock-sync-queue)
57. [Sound Effects, Notification Center Groups & Toast Themes](#57-sound-effects-notification-center-groups--toast-themes)
58. [Under-Construction Indicators (pending features, mock and real)](#58-under-construction-indicators-pending-features-mock-and-real)
59. [Agent-Working Indicator in Kanban & Issue List](#59-agent-working-indicator-in-kanban--issue-list)
60. [Dashboard Information Modules (Board)](#60-dashboard-information-modules-board)
61. [Dashboard Section Layout & Advanced Analytics Modules (Board)](#61-dashboard-section-layout--advanced-analytics-modules-board)
62. [Backend Integration & Live SSE Architecture (mock/real toggle)](#62-backend-integration--live-sse-architecture-mockreal-toggle)
63. [Test Suite, Linting & Frontend CI/CD](#63-test-suite-linting--frontend-cicd)
64. [OAuth2/SSO Authentication & Role-Based Route Protection](#64-oauth2sso-authentication--role-based-route-protection)
65. [Real Persistence & Auto-Healing Pipeline Engine](#65-real-persistence--auto-healing-pipeline-engine)
66. [Policy Sandbox Rules Engine](#66-policy-sandbox-rules-engine)
67. [Bidirectional Real Sync with GitHub](#67-bidirectional-real-sync-with-github)
68. [RAG Explorer & MCP Server Integration](#68-rag-explorer--mcp-server-integration)
69. [Setup Wizard & First-Run Installation (Onboarding)](#69-setup-wizard--first-run-installation-onboarding)

---

## 1. Global Infrastructure

| Feature | Status | Details |
|---|---|---|
| Vue 3.5 + TypeScript | Implemented | Composition API, `<script setup>`, vue-tsc type checking |
| Vite 6 build tool | Implemented | HMR, optimized production builds, lazy-loaded routes |
| Tailwind CSS 3 | Implemented | Dark mode via `class` strategy; Inter font |
| Pinia state management | Implemented | 24 stores under `src/stores/` |
| Vue Router | Implemented | 27 page routes + `/` redirect + catch-all NotFound; lazy-loaded; scroll-to-top on navigate; setup guard chained before auth/RBAC (`router/setupGuard.ts`, §69) |
| i18n (EN/ES) | Implemented | `vue-i18n` with `legacy:false`, 78 top-level sections, 1680 leaf keys per language (both languages balanced), localStorage persistence |
| Dark mode | Implemented | Toggle via UserMenu / `D` shortcut / CommandPalette; localStorage; system preference detection |
| Data-source mode (mock/real) | Implemented | Reactive `apiMode` ref in `client.ts` (resolution: `localStorage['socialseed-api-mode']` > `VITE_USE_MOCK` > default `mock`); reactive proxy dispatches to the mock client or the axios real client; toggle in UserMenu (§62) |
| Real API mode | Implemented | Axios client, base `window.__API_URL__ \|\| '/api/v1'`, auth via `Bearer` JWT (auto-refresh) or `X-API-Key`, 401 → refresh retry → `auth:unauthorized` (§64) |
| Docker deployment | Implemented | Frontend `127.0.0.1:19001→80`, mock-api `127.0.0.1:8001`, real API `127.0.0.1:8888`, Neo4j `7474`/`7687`, PostgreSQL `127.0.0.1:15432→5432`, Redis `127.0.0.1:6379`, MongoDB `127.0.0.1:27017` |
| Hybrid storage backends | Implemented | `TASKER_REDIS_URL`/`TASKER_DATABASE_URL` (convención `TASKER_*`) vía `config/storage.py`: Redis con fallback in-memory cuando no hay URL o Redis inaccesible; consumido por la capa web (events/session store) y `cli/wiring.py`; `TASKER_JWT_SECRET` → `auth/tokens.py` (#525) |
| Mock data volume | Implemented | `frontend/dataset-de-pruebas/` mounted into mock-api container (`DATA_DIR`) |
| Toast notification system | Implemented | Singleton `useToast()`: success/error/warning/info, auto-dismiss, max 5 concurrent |
| html2canvas + jspdf | Implemented | PDF/PNG export for executive dashboard |
| Mermaid diagrams | Implemented | MarkdownRenderer renders Mermaid syntax in agent reasoning logs |
| vis-network | Implemented | Dependency graph visualization (issues + components + optional code nodes) |
| utils | Implemented | `modelPricing.ts`, `piiDetector.ts`, `graphUtils.ts` (BFS, cycle detection, blast radius, transitive deps), `ruleEngine.ts` (§66), `offlineQueue.ts` (§56), `pendingFeatures.ts` (§58), `studioAgents.ts` (§54) |
| Build / typecheck | Implemented | `npm run build` → `vue-tsc -b && vite build` |

### Mock dataset files (`frontend/dataset-de-pruebas/`)

`issues.json` (100), `components.json`, `users.json`, `policies.json`, `constraints.json`, `agent-logs.json`, `dependencies.json`, `dashboard-stats.json`, `projects.json`, `root-cause.json`, `index.json`, `organizations.json` (3 orgs / 6 workspaces / 9 accounts)

### Container topology

| Service | Container | Host port | Role |
|---|---|---|---|
| tasker-db | neo4j:5.26.15 | 7474 / 7687 | Graph DB (APOC) |
| tasker-db-pg | postgres:15-alpine | 127.0.0.1:15432→5432 | PostgreSQL 15 — usuarios/credenciales (#525) |
| tasker-redis | redis:7-alpine | 127.0.0.1:6379 | Redis 7 — sesiones/caché/rate limiting (#525) |
| tasker-db-mongo | mongo:7.0-alpine | 127.0.0.1:27017 | MongoDB 7 — persistencia del chat (`TASKER_MONGO_URL`, #536) |
| tasker-api | tasker-api:local | 127.0.0.1:8888→8000 | Real FastAPI backend |
| tasker-board | tasker-board:local | 127.0.0.1:19001→80 | Vue SPA + nginx (proxies `/api/`, `/mock-api/`, `/mcp/`; `index.html` served `Cache-Control: no-cache`) |
| mock-api | mock-api:local | 127.0.0.1:8001 | FastAPI mock serving dataset JSON under `/mock/*` |

> Note: Hyper-V reserves host ports 8001–8900 on some Windows machines. Local workaround uses `19000`/`19001`/`19002`; committed compose uses `19001`/`8001`/`8888` as above. PostgreSQL se publica en `15432` porque el anfitrión ya tiene un Postgres nativo en el `5432`.

---

## 2. Authentication

| Feature | Status | Details |
|---|---|---|
| Login screen | Implemented | **Standalone clean view** (`App.vue` renders it *instead of* the shell when `!isAuthenticated` — no sidebar/header/`RouterView` behind, no background fetches; solid `bg-white dark:bg-gray-900` backdrop), credentials form (busy/error) + GitHub/Google OAuth2 buttons (`data-testid="oauth-github|google"`), #519/#557 — §64 |
| Session storage | Implemented | Mock: demo ADMIN user in memory; Real: JWT access in RAM + refresh token + user profile in `localStorage` (`authSession.ts`), auto-refresh 60s before expiry — §64 |
| Mock mode bypass | Implemented | `isAuthenticated` true in mock mode (auto-authenticated, `authStore.can()` always grants); real mode requires `initSession()` — §64 |
| 401 handling | Implemented | Response 401 → single-flight refresh + 1 retry; refresh fails → `auth:unauthorized` → the shell unmounts and the clean login view takes over (#557) |
| Logout | Implemented | Real mode revokes the refresh token in the backend, clears session + reload (UserMenu) |
| RBAC | Implemented | Route guards (`meta.roles` → redirect + toast), action gating (`authStore.can()`), role range ADMIN ≥ DEVELOPER ≥ VIEWER — §64 |
| Sign-in flow | Implemented | `App.vue` shows `LoginScreen` when unauthenticated; OAuth callback route `/auth/oauth-callback` |
| Username normalization | Implemented | `normalize_username` (lowercase + trim + restringido a `a-z`/`0-9`/`.`) en `auth/user_store.py`; p.ej. `agent-architect` → `agentarchitect` - #526 |
| PostgreSQL credential store | Implemented | Tabla `users` en PG15 con hashes bcrypt (= username normalizado); seeding idempotente de `dataset-de-pruebas/users.json` gated por `TASKER_AUTH_SEED` al arrancar la API, o `python -m socialseed_tasker.auth.user_store` - #526 |
| Password login + Redis sessions | Implemented | `POST /api/v1/auth/login` valida `username`+`password` contra PG (normalize + bcrypt) ademas de la API key; cada JWT lleva el claim `sid` y la sesion vive en Redis bajo `session:{user_id}:{session_id}` (TTL = refresh 604800s); logout borra la clave, refresh la renueva y middleware/`me` rechazan tokens con sesion revocada; fallback in-memory sin Redis - #527 |

---

## 3. Layout & Navigation

### Sidebar (desktop only, `md+`)

| Feature | Status | Details |
|---|---|---|
| Collapsible sidebar | Implemented | 20px collapsed → 64px on hover (`w-20` → `w-64`), smooth transition |
| Logo + branding | Implemented | "SocialSeed" text when expanded |
| Navigation groups | Implemented | Principal (4), Management (17), Analysis (3) = **24 nav items** |
| Active route highlighting | Implemented | Color change on current route |
| Nav icons | Implemented | SVG icons per nav item |
| i18n labels | Implemented | All nav labels use `t()` |
| Stable across data-source modes | Implemented | No RBAC/feature filtering of nav items: the same 3 groups / 24 items render in mock and real modes (route-level RBAC stays in the router guard, §64) |
| Pending badges | Implemented | Amber construction badge on pending routes, visible in **both** mock and real modes (§58) |
| Mobile behavior | Implemented | Hidden below `md` (`hidden md:flex`); hamburger opens MobileDrawer |

**Nav groups**

| Group | Routes |
|---|---|
| Principal | `/board`, `/system`, `/kanban`, `/list` |
| Management | `/components`, `/policies`, `/constraints`, `/sandbox`, `/rag`, `/finops`, `/auto-healing`, `/replay`, `/executive`, `/users`, `/chat`, `/mcp`, `/hitl`, `/organization`, `/governance-matrix`, `/audit-log`, `/agents/studio` |
| Analysis | `/graph`, `/analysis`, `/analytics` |

### Header (AppHeader)

| Feature | Status | Details |
|---|---|---|
| Dynamic page title | Implemented | Maps route path → translated title (23 paths; `/profile` falls back to dashboard title) |
| Pending badge | Implemented | `PendingDevBadge` after the title when the route is pending (mock and real modes, §58) |
| Under-construction chip | Implemented | Amber text chip "Under construction / En construccion" (`common.underConstruction`, `role="status"`) next to the title when the route is pending **and** the app consumes the real API (`isRealPendingFeature`); mock mode shows only the icon badge (§58) |
| Organization switcher | Implemented | `OrganizationSwitcher` (`hidden lg:flex`, before ProjectSelector): hierarchical Organization → Workspace dropdown, localStorage, link to `/organization` settings |
| Global HITL banner | Implemented | Shown when `urgentPendingCount > 0` (CRITICAL/HIGH pending); click → HITLCommandCenter; Review button → HITLQuickActionModal |
| Hamburger menu | Implemented | 44×44 button (`md:hidden`), emits `open-mobile-menu` |
| Project selector | Implemented | `ProjectSelector`, 4 projects, localStorage, filters issues |
| Sync status badge | Implemented | `SyncStatusBadge` (`hidden sm:flex`): SYNCED / OFFLINE_QUEUED / SYNCING / DEGRADED / Offline; clickable → `SyncQueueDrawer` (#515) |
| Notification bell | Implemented | `NotificationCenter` with unread badge |
| HITL quick action modal | Implemented | Mounted in header when `hitlStore.quickActionRequestId` set |
| UserMenu | Implemented | Top-right corner |

### MobileDrawer

| Feature | Status | Details |
|---|---|---|
| Overlay slide-in | Implemented | From left, 300ms transition, full-screen dark overlay |
| Close gestures | Implemented | Tap overlay or swipe-left |
| Navigation content | Implemented | Same 3 groups / 24 items as desktop Sidebar |
| i18n | Implemented | `mobileNav.openMenu`, `mobileNav.menu`, `mobileNav.swipeHint` |

### UserMenu

| Feature | Status | Details |
|---|---|---|
| Avatar with initials | Implemented | Auto-generated from username |
| Dropdown menu | Implemented | Click to toggle, click-outside to close |
| Dark/Light mode toggle | Implemented | Sun/Moon icons |
| Language selector | Implemented | EN/ES flag buttons, reactive switching |
| Data source (Mock/Real) | Implemented | Segmented control (`data-testid="api-mode-mock|real"`) switching `apiMode` → `localStorage['socialseed-api-mode']`; drives all API calls, badges and RBAC bypass (#517/#519, §62) |
| Signed-in identity | Implemented | Real username + role (`profile.roles.*`); OAuth-aware logout revokes the refresh token (#519) |
| Sign out | Implemented | Clears auth + reloads |
| Profile link | Implemented | Navigates to `/profile` |

### TeamTicker

| Feature | Status | Details |
|---|---|---|
| Bottom marquee bar | Implemented | Fixed bottom, infinite CSS animation |
| User avatars + names | Implemented | All users from store |
| Active status indicator | Implemented | Green dot with ping if active within 24h |
| Hover pause | Implemented | Animation pauses on hover |
| Auto-refresh | Implemented | Polls every 10 seconds |

### App shell (App.vue)

Global mounts: `Sidebar`, `AppHeader`, `MobileDrawer`, `TeamTicker`, `CommandPalette`, `KeyboardShortcutsHelp`, `ToastContainer`, `FloatingChat`, optional `LoginScreen`. Content offset `md:ml-20`.

---

## 4. Dashboard (BoardView)

25 information modules grouped in 6 labeled sections with hairline headers. See §60 and §61 for the full per-module breakdown and evolution.

| Section | Modules |
|---|---|
| **Overview** | DashboardStats (4 stat cards), DashboardPulse (4 ops cards), Project info bar |
| **Analytics** | TrendChart, AvgResolutionTime, DailyActivityChart, StatusDistribution, ActivityHeatmap, IssueAging |
| **Issue Insights** | PriorityBreakdown, ComponentWorkload, NotificationsFeed, PriorityMatrix, LabelCloud |
| **Team & Quality** | TeamWorkload, DependencyRisk, GovernanceCompliance |
| **Ecosystem** | GitHubSyncHealth, AuditFeed |
| **Operations** | AutoHealingMini, SyncStatusCard, BudgetMini |

| Feature | Status | Details |
|---|---|---|
| **Section headers** | Implemented | `SectionHeader`: uppercase tracking-wide label + hairline rule (`boardSections.*` EN/ES) |
| **Stats cards** | Implemented | 4 cards: Total Issues, Resolved This Month, In Progress, Blocked |
| **Operational pulse** | Implemented | 4 cards: Agents Working, HITL Approvals, SLA At Risk, Notifications (§60) |
| **Trend chart** | Implemented | Custom SVG line chart, 8-week rolling, 3 lines (Open/Closed/In Progress), legend |
| **Avg Resolution Time** | Implemented | Circular SVG gauge, color-coded (green ≤3d, blue ≤7d, orange ≤14d, red >14d) |
| **Daily Activity Chart** | Implemented | Custom SVG bar chart, month selector, created vs resolved bars |
| **Status Distribution** | Implemented | Horizontal bar chart, 5 statuses incl. Waiting Approval, percentage breakdown |
| **Analytics modules** | Implemented | ActivityHeatmap (13-week day grid), IssueAging (age buckets), PriorityMatrix (priority x status), LabelCloud (§61) |
| **Team & quality modules** | Implemented | TeamWorkload (assignee leaderboard), DependencyRisk (fan-in ranking), GovernanceCompliance ring (§61) |
| **Ecosystem modules** | Implemented | GitHubSyncHealth (stacked SYNCED/PENDING/ERROR), AuditFeed (last 6 events + `/audit-log` link) (§61) |
| **Insight & ops modules** | Implemented | PriorityBreakdown, ComponentWorkload, NotificationsFeed, AutoHealingMini, SyncStatusCard, BudgetMini (§60) |
| **Data sources** | Implemented | issuesStore, componentsStore, usersStore, hitlStore, notificationsStore, finopsStore, autoHealingStore, uiStore, auditLogStore |
| **Project info bar** | Implemented | Project name, description, active policies count |
| **Loading/Error states** | Implemented | Spinner + error message with refresh |
| i18n | Implemented | `boardModules.*` (54 keys), `boardSections.*` (6 keys), chart sections translated |

---

## 5. Issues List (ListView)

| Feature | Status | Details |
|---|---|---|
| **Data table** | Implemented | Columns: Checkbox, Title, Status, Priority, Component, Labels, Created, Actions |
| **Responsive columns** | Implemented | Component hidden below `md`, Labels below `lg`, Created below `sm` |
| **Select all** | Implemented | Header checkbox selects/deselects all visible issues |
| **Bulk actions bar** | Implemented | Status change, assignee (humans + agents with AI badge), delete |
| **Search** | Implemented | Text filter on title, ID, description (client-side) |
| **Status filter** | Implemented | All, OPEN, IN_PROGRESS, BLOCKED, CLOSED |
| **Priority filter** | Implemented | All, CRITICAL, HIGH, MEDIUM, LOW |
| **Component filter** | Implemented | Dynamic dropdown from store |
| **Advanced FilterBuilder** | Implemented | Multi-criteria chips, AND/OR operator, date range, saved searches (localStorage) |
| **Project filter** | Implemented | Filters by `project_id` matching ProjectSelector |
| **New Issue button** | Implemented | Opens CreateIssueModal |
| **Export button** | Implemented | CSV/JSON export dropdown |
| **Click row → detail** | Implemented | Opens IssueDetailView slide-in panel |
| **Empty state** | Implemented | "No issues in this project" with hint |
| **Sync simulation** | Implemented | `simulateSync()` on create/update/delete/close |
| **Touch targets** | Implemented | Row action buttons min 44×44 |
| i18n | Implemented | All labels translated |

---

## 6. Kanban Board (KanbanView)

| Feature | Status | Details |
|---|---|---|
| **4 status columns** | Implemented | OPEN, IN_PROGRESS, BLOCKED, CLOSED |
| **Drag-and-drop** | Implemented | IssueCard draggable, KanbanColumn drop zones |
| **Priority sorting** | Implemented | CRITICAL > HIGH > MEDIUM > LOW within columns |
| **Status change on drop** | Implemented | Auto-sets `closed_at` when dropping to CLOSED |
| **Governance check on drop** | Implemented | Blocks CLOSED if governance unmet → GovernanceValidationModal |
| **New Issue button** | Implemented | Opens CreateIssueModal |
| **Click card → detail** | Implemented | Opens IssueDetailView slide-in panel |
| **AI agent indicator** | Implemented | Pulsing cyan circle on agent_working issues |
| **Agent timer** | Implemented | Live elapsed-time badge on agent_working cards |
| **Agent kill switch** | Implemented | Hover kill button stops agent (`agent_working=false`) |
| **Advanced FilterBuilder** | Implemented | Same multi-criteria filter UI as ListView |
| **Project filter** | Implemented | Filters by `project_id` |
| **Empty state** | Implemented | "No issues in this project" |
| **Sync simulation** | Implemented | `simulateSync()` on drop/update/delete/close/create |
| **Mobile snap scroll** | Implemented | `snap-x snap-mandatory`, `85vw` columns, edge gradient indicators |
| i18n | Implemented | All labels translated |

---

## 7. Issue Detail Panel (IssueDetailView)

| Feature | Status | Details |
|---|---|---|
| **Slide-in panel** | Implemented | Right-side overlay (`w-full max-w-lg`), click-outside to close |
| **Embedding** | Implemented | No dedicated route; embedded in ListView, KanbanView, GraphView |
| **4 tabs** | Implemented | Details, AI Reasoning, Progress, Audit |
| **Details tab** | Implemented | Title, Assignee, Creator, Description (RichTextEditor), Status, Priority, Labels, Dependencies, Timestamps |
| **Assignee management** | Implemented | Interactive select with all users, i18n "Unassigned" |
| **Assignee history** | Implemented | Timeline with avatars, dates, reassignment tracking |
| **Dependency management** | Implemented | Add/remove via RelationshipModal |
| **GitHub Sync card** | Implemented | GitHubSyncCard: issue # link, sync badge, last synced, Force Re-sync; in real mode also CONFLICT badge, sync error panel and per-field Keep local / Keep remote / Merge resolution (#522, §67) |
| **Governance validation** | Implemented | Blocks CLOSED when requirements unmet → GovernanceValidationModal (Fix/Override) |
| **AI Reasoning tab** | Implemented | Loading state, reasoning logs with MarkdownRenderer, timestamps |
| **Progress tab** | Implemented | Affected Files (NEW/EDITED/DELETED badges + per-file DiffViewer via `diff_hunk`), Tech Debt Notes (amber Markdown), Task Checklist, Files Changed, agent-log diffs |
| **Interactive task checklist** | Implemented | Progress tab checkboxes enabled (`TaskChecklist` + `MarkdownRenderer` `interactive`), per-item keys normalized, state persisted per issue in `task_checklist` (server + mock), optimistic toggle with rollback toast, live updates via `issue-updated` SSE, counter `issues.checklistProgress`, i18n EN/ES (#531) |
| **Diff preview** | Implemented | DiffViewer expand/collapse per affected file; also on agent log content |
| **Audit trail** | Implemented | 9 mock entries, action-type icons/colors, actor avatars, type filters |
| **Agent log stream** | Implemented | SSE via `useAgentStream`, status indicators, auto-scroll, kill switch |
| **HITL approval** | Implemented | HITLApprovalBanner when status is WAITING_HUMAN_APPROVAL |
| **Global HITL quick actions** | Implemented | AppHeader banner + HITLQuickActionModal from any view |
| **Presence indicators** | Implemented | PresenceAvatars, TypingIndicator, ConflictWarning |
| **Token metrics** | Implemented | TokenMetrics: consumption, cost, model pricing, budget |
| **Responsive layout** | Implemented | Field grids 1-col on mobile (`sm:grid-cols-2`); tab bar horizontal scroll |
| i18n | Implemented | All labels translated |

---

## 8. Components Management (ComponentsView)

| Feature | Status | Details |
|---|---|---|
| **Table/Grid views** | Implemented | Toggle between table and card grid |
| **Search** | Implemented | Filter by name, alias, ID |
| **Detail panel** | Implemented | Slide-in: alias, name, UUID, description, status breakdown, issue list |
| **Create/Edit** | Implemented | Modal: Alias (4 chars), Name*, Description, Project |
| **Delete** | Implemented | Confirm dialog |
| **Responsive table** | Implemented | `overflow-x-auto` + `min-w-[640px]` |
| i18n | Implemented | All labels translated |

---

## 9. Policies Management (PoliciesView)

| Feature | Status | Details |
|---|---|---|
| **Card grid** | Implemented | Responsive 1–3 columns |
| **Policy cards** | Implemented | Name, active/inactive badge, description, target scope, rules count |
| **Create/Edit** | Implemented | Modal: Name*, Description, Rule select (4 types), Level (SOFT/HARD), Target Scope |
| **Delete** | Implemented | Confirm dialog |
| i18n | Implemented | All labels translated |

---

## 10. Constraints Management (ConstraintsView)

| Feature | Status | Details |
|---|---|---|
| **Stats row** | Implemented | 4 cards: Total, Hard (red), Soft (amber), Active (green) |
| **Data table** | Implemented | Columns: ID, Name, Category, Severity, Scope, Active, Auto-fix, Actions |
| **Search + filters** | Implemented | Search by name/ID; filter by category and severity |
| **Detail panel** | Implemented | Slide-in with all constraint details |
| **Create/Edit** | Implemented | Modal with all fields |
| **Delete** | Implemented | Confirm dialog |
| **Run Validation** | Implemented | Button → results banner with violation cards |
| **Write-time max_depth** | Implemented | #532: `POST /issues/{id}/dependencies` (+ bulk) aborts con 409 `POLICY_VIOLATION` si la nueva arista excede una constraint activa HARD `max_depth`; `details` = policy_name, constraint, rule_type, severity, message, suggestion |
| **Responsive table** | Implemented | `overflow-x-auto` + `min-w-[720px]` |
| i18n | Implemented | All labels translated |

---

## 11. Users Management (UsersView)

| Feature | Status | Details |
|---|---|---|
| **Stats row** | Implemented | 3 cards: Total Users, Humans (blue), AI Agents (purple) |
| **User cards grid** | Implemented | Avatar, username, email, type badge, role, model, skills, stats; in **real mode** the backend profile payload is normalized in `usersApi.fetchUsers` (`type`→`human`, `avatar`→👤, `skills`→`[]`, `email` null→`''`, `last_active`←`last_login`/`created_at`, `is_active`→true) so cards render edit/delete buttons, the Human badge, a valid date and count in the Humans stat — without it the admin card showed as locked with an AI badge (#556) |
| **Create user** | Implemented | Modal: Username*, Email*, Role, Skills, Avatar picker (11 emojis); in real mode it posts `POST /users` which inserts `users` + `human_user` + `user_skills` in one transaction (PG-generated uid) and answers 201 with the composed profile normalized by `createUser` (human badge, avatar, skills — no post-create regression) plus the one-time `temporary_password` (#563); the role `<select>` switches vocabulary by mode (mock dataset roles vs `ADMIN/DEVELOPER/VIEWER`, seeded labels from #556); duplicates answer **409** → toast `users.usernameTaken`/`users.emailTaken`, invalid role **422** → `common.error` + backend detail (#559) |
| **Create agent** | Implemented | Modal: Username*, Email*, Model select (5 models), Specialization, Skills, Avatar (8 robot emojis) |
| **Edit user/agent** | Implemented | Dedicated modals with pre-filled fields; the role `<select>` appends the current role when it is outside the base options so `ADMIN`/`VIEWER` (real mode) never renders blank (#556); in real mode the edit modal offers the seeded `ADMIN/DEVELOPER/VIEWER` vocabulary (mock keeps the dataset roles) and `PUT /users/{id}` persists `username`/`username_normalized` in `users`, profile + `role_id` in `human_user` and a full `user_skills` replacement in one transaction (**404** unknown uid, **409** duplicate username/email against *other* users — re-sending your own values never collides —, **422** invalid role or non-human type, `password_hash` untouched), the response is the composed PG profile normalized by `updateUser` so the card keeps badge/avatar/skills/buttons, and the view toasts `users.updated` on success or the backend detail on 422/404 (#560); an effective role change additionally revokes the target's sessions so the next refresh 401s and re-login carries the new role (#561) |
| **Delete** | Implemented | Human cards disable the delete button while they are the **last human** (`humans.length <= 1`, tooltip `users.lastUserGuard`) — agents are always deletable, so the guard measures humans, not the list total; server-side the API answers **409 `Cannot delete the last user`** on `DELETE /users/{id}` when PG holds a single human (guard source moved from Neo4j to the PG root in #562; agents are exempt), and failures raise a toast with the backend `detail` (`common.error` as fallback) keeping the agent modal open on error (#562) |
| **PostgreSQL root schema** | Implemented | #558: normalized **8-table schema** (`roles`/`skills`/`tools` catalogs with seeds, root `users` with `DEFAULT gen_random_uuid()::text`, `human_user`/`agents_user` split, `user_skills` N:M, `session_logs` + 4 indexes) with idempotent legacy migration (backup `users_legacy`, ids preserved for JWT `sub`, `_verify_migration` aborts on mismatch); `GET /users`, `/users/{id}` and `/users/email/{email}` read PG via `PgUserRepository` JOINs (full profile, `id` = PG uid, `role` from `roles.id` or `'ai-agent'` for agents, `last_login` derived from `session_logs`), **503** without `TASKER_DATABASE_URL`, Neo4j `(:User)` re-keyed to the PG uid by username at startup; `usersApi` preserves the full backend payload and maps `role: null` → `'ai-agent'` |
| i18n | Implemented | All labels translated; `users.adminRole`/`users.viewerRole`/`users.lastUserGuard` added for real-mode roles and the delete guard (#556) |

---

## 12. Dependency Graph (GraphView)

| Feature | Status | Details |
|---|---|---|
| **vis-network graph** | Implemented | Nodes = components + issues, Edges = labeled relations (`DEPENDS_ON`, `BLOCKS`, `BELONGS_TO`, `AFFECTS`, `CODE_REFERENCE`, `ASSIGNED_TO`, `LINKED_TO_PR`) |
| **Color legend** | Implemented | Component, Open, In Progress, Blocked, Closed + Code Overlay legend + relation chips (same tokens as edge labels) |
| **Edge labels** | Implemented | Per-relation compact font (size 10) colored by type; `BLOCKS` = inverse edge derived from `issue.blocks` (skipped when blocker or target is CLOSED) (#528) |
| **Edge label toggle** | Implemented | `GraphToolbar` button shows/hides labels live via `DataSet.update()` (no graph rebuild) (#528) |
| **Status filter** | Implemented | Dropdown to filter issues by status |
| **Search** | Implemented | Text filter |
| **Component filter** | Implemented | GraphFilters with checkbox-based selection |
| **Max hops filter** | Implemented | Slider to limit traversal depth |
| **Layout toggle** | Implemented | Hierarchical (top-down) vs Force Directed (Barnes-Hut) |
| **Graph interactions** | Implemented | Hover, tooltip, zoom, drag, navigation, keyboard |
| **Click node → detail** | Implemented | Opens IssueDetailView for issue nodes |
| **Connect mode** | Implemented | Create relationships via click-to-connect |
| **Cycle detection** | Implemented | Prevents circular dependencies |
| **Dependency creation wired** | Implemented | #532: `onCreateRelationship` llama a `POST /issues/{id}/dependencies` y refresca el grafo al tener éxito |
| **HARD violation inline panel** | Implemented | #532: `RelationshipModal` muestra panel inline traducido (título, badge HARD/SOFT, mensaje, política/constraint, sugerencia) en vez de toast genérico; `client.ts` propaga `code`/`details` con `suppressErrorToast` |
| **Code Overlay toggle** | Implemented | Show/hide AST nodes (File/Class/Function) |
| **Code node rendering** | Implemented | Files (cyan/database), Classes (teal/diamond), Functions (emerald/triangle) |
| **Code node detail** | Implemented | Click shows file path, language, lines, type |
| **PNG export** | Implemented | Export graph as PNG via `useExport().exportSVG`/`exportPNG` |
| **Sync simulation** | Implemented | `simulateSync()` on update/delete/close |
| **Exploration toolbar** | Implemented | `GraphToolbar`: zoom in/out, fit to screen, clustering toggle, path tracing |
| **Component clustering** | Implemented | `network.cluster()` groups issues by component (`cluster-<id>`); click cluster → `openCluster()` |
| **Impact path tracing** | Implemented | BFS (`graphUtils.findPath`, directed + reverse fallback) between two issues; path highlighted amber, rest dimmed; no-path/selection feedback |
| **Priority filter** | Implemented | CRITICAL/HIGH/MEDIUM/LOW pills in `GraphFilters` filter issue nodes |
| **Node type filters** | Implemented | Issue / Component / Agent / Policy / PR toggle pills (with legend swatches) |
| **Agent nodes** | Implemented | Orange diamonds from `usersStore` (type/role agent) with edges to assigned issues |
| **Policy nodes** | Implemented | Pink stars from `policiesStore` (standalone governance nodes) |
| **GitHub PR nodes** | Implemented | Gray squares `pr-<issueId>` from `issue.github_sync` with issue→PR edges (label `#<issue_number>`) |
| **Node inspector** | Implemented | `NodeInspector` side panel: metadata, blast radius (total/direct/depth/critical/high via `graphUtils.blastRadius`), quick links (open issue, routes, GitHub URL) |
| **Edge inspector** | Implemented | Relation type (same `graphExplorer.relations.*` tokens as edge labels), direction, weight, cycle detection (reverse `findPath` on remaining edges) |
| i18n | Implemented | All labels translated (`graphExplorer` section) |

---

## 13. Impact & Root Cause Analysis (AnalysisView)

### Impact Analysis (ImpactAnalysisPanel)

| Feature | Status | Details |
|---|---|---|
| **Issue selector** | Implemented | Dropdown of all issues |
| **SVG tree visualization** | Implemented | Custom `ImpactSvgTree`, level-grouped children, color-coded |
| **4 stats** | Implemented | Total Affected, Direct Dependencies, Transitive, Cascade Blocked |
| **Blast radius slider** | Implemented | `BlastRadiusSlider`, debounced, 1–5 hop range |
| **Click node → re-analyze** | Implemented | Click any node to analyze from that issue |

### Root Cause Analysis (RootCausePanel)

| Feature | Status | Details |
|---|---|---|
| **Test failure form** | Implemented | Test Name, Component (with "Any"), Error Message |
| **Label toggles** | Implemented | 13 labels: bug, auth, security, performance, database, ui, feature, webhook, graphql, dependencies, regression, timeout, concurrency |
| **Results list** | Implemented | Ranked candidates with confidence % and reason tags |
| **Load Sample** | Implemented | Cycles through `GET /api/v1/test-failures` (empty list = valid, no error) |

### Real API contract (#529)

| Feature | Status | Details |
|---|---|---|
| **Impact endpoint** | Implemented | Frontend calls `GET /api/v1/analyze/impact/{issue_id}` (was `/analysis/*` → 404 in real mode); response includes `issue_title`, `issue_status`, `risk_level` (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`), `graph_depth`, `total_affected`, `directly/transitively_affected`, `blocked_issues` |
| **Root-cause endpoint** | Implemented | Frontend calls `POST /api/v1/analyze/root-cause` with auto-generated `test_id`; body: `test_id`, `test_name`, `error_message`, `component?`, `labels[]`; response `confidence` is a percentage (0-100) plus `issue_status`, `issue_title`, `reasons`, `graph_distance` |
| **Test failures endpoint** | Implemented | `GET /api/v1/test-failures` returns failures derived from issues labeled `test-failure` (registered via `POST /webhooks/test-failure`); no failures → empty list |
| **Mock dispatch parity** | Implemented | `client.ts` mock matchers updated to `/analyze/*`; mock impact + root-cause verified in browser (0 pageerrors) |

---

## 14. System Dashboard (DashboardSystemView)

| Feature | Status | Details |
|---|---|---|
| **Main metrics** | Implemented | 4 cards: Total Issues, Blocked Issues, Total Components, Agents Working |
| **System health** | Implemented | Neo4j (connected, latency), API (FastAPI version), Workers |
| **Redis/PostgreSQL cards** | Implemented | #533: tarjetas con estado + latencia leídas de `GET /health` (`dependencies` + `dependency_latency_ms`); badge dinámico connected/disconnected/not configured en Neo4j/Redis/Postgres; Refresh re-fetch |
| **Health alias** | Implemented | #533: `GET /api/v1/health` alias sin auth del `/health` de raíz (el cliente real usa base `/api/v1`); `status: degraded` si un servicio configurado (`TASKER_REDIS_URL`/`TASKER_DATABASE_URL`) está caído |
| **Sync queue** | Implemented | GitHub connected/disconnected, pending items, last sync |
| **Constraints summary** | Implemented | Total rules, Active, Inactive |
| **Seed/Reset buttons** | Implemented | Admin operations with confirm dialogs |
| **Refresh button** | Implemented | Re-fetches health + sync queue |
| i18n | Implemented | All labels translated |

---

## 15. User Profile (ProfileView)

| Feature | Status | Details |
|---|---|---|
| **Avatar display** | Implemented | Large circular avatar with camera icon button |
| **Personal info form** | Implemented | First name, Last name, Email, Role, Timezone select (7 options) |
| **Change password** | Implemented | Current/new/confirm with validation (min 8 chars, match check, toast feedback) |
| **Notification preferences** | Implemented | Toggles for Email, Push, Agent alerts |
| **Save changes** | Implemented | Saves with success toast |
| i18n | Implemented | All labels translated |

---

## 16. Authentication Screen (LoginScreen)

| Feature | Status | Details |
|---|---|---|
| **Full-screen overlay** | Implemented | Centered card with branding |
| **API key input** | Implemented | Password field with busy/error states; translated backend errors (401 invalid key, 403 oauth not configured) |
| **OAuth2 buttons** | Implemented | GitHub + Google, `data-testid="oauth-github|google"`, "or continue with API key" divider (#519, §64) |
| **Sign in / Skip buttons** | Implemented | Both with dark mode variants |
| **Error message** | Implemented | Red alert for invalid credentials (`login-error` testid) |
| i18n | Implemented | All labels translated |

---

## 17. Shared UI Components

### Layout Components
| Component | Purpose | Details |
|---|---|---|
| `Sidebar` | Main navigation | Collapsible, 3 groups, 24 items, desktop-only; stable across data-source modes, pending badges (§58) |
| `MobileDrawer` | Mobile navigation | Overlay drawer, swipe-to-close, same 24 items |
| `AppHeader` | Top bar | Dynamic title + pending badge + under-construction chip (real mode), HITL banner, hamburger, org switcher (lg+), project selector, network mode toggle (xl+), sync badge (opens queue drawer), notifications, user menu |
| `OrganizationSwitcher` | Org/workspace selector | Hierarchical Organization → Workspace dropdown, localStorage persistence, link to `/organization` settings |
| `UserMenu` | User dropdown | Avatar, dark mode, language, logout, profile link |
| `NavItem` | Sidebar link | Icon + label, active state, badge, 44px touch target |

### Board Components
| Component | Purpose | Details |
|---|---|---|
| `IssueCard` | Kanban card | Draggable, badges, delete, AI indicator, live timer, kill switch |
| `KanbanColumn` | Drop zone | Status-specific, drag events, empty state |
| `CreateIssueModal` | Issue creation | Title, component, description (RichTextEditor), priority, labels |

### Issue Components
| Component | Purpose | Details |
|---|---|---|
| `GitHubSyncCard` | GitHub sync widget | Issue # link, sync badge, last synced, Force Re-sync |
| `GovernanceValidationModal` | Closure blocker | Violated policies, missing requirements, Fix/Override |

### Dashboard Components
| Component | Purpose | Details |
|---|---|---|
| `DashboardStats` | Stats row | 4 top stat cards (Total, Resolved, In Progress, Blocked) |
| `DashboardPulse` | Ops pulse row | Agents Working, HITL Approvals, SLA At Risk, Notifications cards |
| `ModuleCard` | Module shell | Shared card: title + action slot + default slot (all 21 card modules) |
| `SectionHeader` | Section divider | Uppercase label + hairline rule for the 6 dashboard sections |
| `StatsCard` | Metric display | Title, value, subtitle, trend, color theme |
| `TrendChart` | Line chart | 8-week SVG, 3 series, legend |
| `DailyActivityChart` | Bar chart | Month selector, created/resolved bars |
| `AvgResolutionTime` | Gauge chart | Circular SVG, color-coded |
| `StatusDistribution` | Horizontal bars | 5 statuses, percentages |
| `PriorityBreakdown` | Priority bars | Open issues per priority, color-coded |
| `ComponentWorkload` | Workload bars | Top 5 components by open issues |
| `NotificationsFeed` | Notification list | Latest 4 notifications + unread chip |
| `AutoHealingMini` | Pipeline counters | Runs summary + live running-stage row |
| `SyncStatusCard` | Sync card | Pending mutations + network mode chip |
| `BudgetMini` | FinOps card | Total cost + budget alert chip |
| `ActivityHeatmap` | GitHub-style heatmap | 13-week created/closed event grid, 5-level brand scale |
| `IssueAging` | Aging bars | Open issues by age bucket + avg/oldest stats |
| `PriorityMatrix` | Matrix grid | Priority x status counts with intensity fill |
| `LabelCloud` | Tag cloud | Top 18 labels scaled by frequency |
| `TeamWorkload` | Team leaderboard | Top assignees, Human/AI badges, open/total bars |
| `DependencyRisk` | Fan-in ranking | Most-depended-upon issues + edge/blocked totals |
| `GovernanceCompliance` | Compliance ring | SVG ring + violations/missing-summary/missing-files counters |
| `GitHubSyncHealth` | Sync health | Stacked SYNCED/PENDING/ERROR bar + % synced |
| `AuditFeed` | Audit list | Latest 6 audit events, 2-column, link to `/audit-log` |
| `TeamTicker` | Bottom marquee | User avatars, auto-refresh |

### Analysis Components
| Component | Purpose | Details |
|---|---|---|
| `ImpactAnalysisPanel` | Impact results | Stats, SVG tree, dependency cards |
| `ImpactSvgTree` | Tree visualization | Custom SVG, color-coded nodes |
| `RootCausePanel` | Root cause results | Test failure form, label toggles, ranked candidates |
| `BlastRadiusSlider` | Depth filter | Debounced, 1–5 hop range |
| `MarkdownRenderer` | Markdown parser | XSS-safe, Mermaid diagrams, dark mode |

### UI Components
| Component | Purpose | Details |
|---|---|---|
| `StatusBadge` | Status pill | Color-coded (incl. WAITING_HUMAN_APPROVAL) |
| `PriorityBadge` | Priority pill | Color-coded |
| `LabelTag` | Label pill | Gray rounded pill |
| `LoadingSpinner` | Loading indicator | Animated spinning circle |
| `RichTextEditor` | Text input | Slash commands (13 types), preview toggle, PII preview toggle (inline `PIIRedactionPreview`) |
| `DiffViewer` | Diff display | Unified/split view, copy, download `.patch` |
| `FilterBuilder` | Advanced filters | Multi-select chips, AND/OR, dates, saved searches |
| `AuditTrail` / `AuditEntry` | Activity log | Icons/colors, actor avatars, type filters |
| `AgentLogStream` | Real-time logs | SSE, auto-scroll, kill switch, Mask PII toggle (per-line detection badge + masked content) |
| `AgentCostChart` | Token costs | SVG chart of consumption by model (7D/30D/All) |
| `TokenMetrics` | Token stats | Prompt/completion, cost, budget % |
| `PresenceAvatars` | User presence | Who's viewing an issue |
| `TypingIndicator` | Typing status | Animated dots |
| `ConflictWarning` | Field conflicts | Multi-user same-field edit warning |
| `HITLApprovalBanner` | Approval UI | Severity badge, approve/reject/modify |
| `HITLQuickActionModal` | Global HITL actions | Approve/reject/modify + textarea, impact stats, View Full Context; syncs issue status |
| `RelationshipModal` | Dependency creation | Issue search, relationship type, cycle detection |
| `BulkActionsBar` | Multi-select actions | Status change, assign, delete |
| `NotificationCenter` / `NotificationItem` | Notification panel | Tabs (all/unread/action), severity groups (Emergency/Warning/Info), channel chips, bulk mark-read/clear; HITL click → quick action modal |
| `ToastContainer` / `ToastItem` | Toast display | Type-colored, auto-dismiss, animation; 3 visual themes: minimal/rich/enterprise (#516) |
| `ToastThemeSettings` | Toast theme picker | 3 mini previews, persists `uiStore.toastTheme` (#516) |
| `KeyboardShortcutsHelp` | Shortcuts modal | Grouped shortcut list, `?` to open |
| `CommandPalette` | Quick actions | Fuzzy search: pages, actions, issues, components; recent actions; Ctrl/Cmd+K |
| `GraphFilters` | Graph filtering | Component checkboxes, priority (CRITICAL/HIGH/MEDIUM/LOW) and node type pills, status filter, max hops |
| `ProjectSelector` | Project switcher | 4 projects, localStorage, filters all views |
| `SyncStatusBadge` | Sync indicator | Clickable button (opens `SyncQueueDrawer`), green/yellow/blue/amber, animated ping, pending count |
| `PendingDevBadge` | Pending indicator | Amber construction badge on pending nav items and page headers (§58) |
| `AgentWorkingIcon` | Agent indicator | Pulsing robot + live elapsed timer on cards/list rows (§59) |
| `AuditLogTable` | Audit table | Timestamp, actor avatar/type, event badge, severity pill, resource, action, IP |
| `PIIRedactionPreview` | PII suite | Live `detectPII` list, Mask PII toggle, before/after preview, Mask/Reveal actions |

### Sync / Offline Components
| Component | Purpose | Details |
|---|---|---|
| `NetworkModeToggle` | Network simulator | Segmented Online / Degraded / Offline with status dots, `xl+` in AppHeader, persists `uiStore.networkMode` |
| `SyncQueueDrawer` | Queue inspector | Right overlay panel: queued mutations list, retries, conflict resolution (Keep local / Keep remote / Merge textarea JSON), Force sync button (#515) |

### Graph Components
| Component | Purpose | Details |
|---|---|---|
| `GraphToolbar` | Exploration toolbar | Zoom in/out, fit, cluster toggle, impact path tracing (source/target selects + feedback) |
| `NodeInspector` | Node/edge inspector | Side panel: metadata, blast radius, quick links, relation/direction/weight/cycle |
| `OrganizationSwitcher` | Org/workspace switcher | Enterprise header dropdown (org → workspace), role-aware actions |

### Chat Components
| Component | Purpose | Details |
|---|---|---|
| `ChatSidebar` | Conversation list | Search, avatars, online status, unread badges, pin |
| `ChatMessage` | Message display | Markdown, code blocks, agent actions, reactions |
| `ChatInput` | Message input | PII detection, code block insertion, typing indicators |
| `PIIDetectionBanner` | PII warnings | Inline banner with severity colors |
| `PIIWarningModal` | PII blocking | Cancel / Mask & Send / Send Anyway |
| `FloatingChat` | Global chat widget | Messenger-style bubble, all views |

### Sandbox Components
| Component | Purpose | Details |
|---|---|---|
| `ImpactReport` | Simulation results | Pass/fail, violations with severity, promote button |

### User Components
| Component | Purpose | Details |
|---|---|---|
| `CreateUserModal` | User creation | Username, email, role, skills, avatar picker |
| `EditUserModal` | User editing | Same fields, pre-filled |
| `EditAgentModal` | Agent editing | Model, temperature, system prompt, tools, folder permissions |

### Auth Components
| Component | Purpose | Details |
|---|---|---|
| `LoginScreen` | Auth gate | Standalone clean view (replaces the shell when logged out, #557) |

### Setup Components
| Component | Purpose | Details |
|---|---|---|
| `McpSetupPanel` | Post-install credentials | API master key + copy feedback, editable MCP port, ready-to-paste `.cursor/mcp.json` snippet, Finish → `/board` (§69) |

**Total view components:** 29 files in `src/views/` (28 routed incl. NotFound + `IssueDetailView` embedded)

**Total shared components:** 101 `.vue` files under `src/components/`

---

## 18. Real-Time & Presence Features

| Feature | Status | Details |
|---|---|---|
| **Agent log streaming** | Implemented | SSE via `useAgentStream`, auto-reconnect with exponential backoff |
| **Connection status** | Implemented | 4 states: connecting, connected, disconnected, reconnecting |
| **Auto-scroll** | Implemented | Log stream auto-scrolls to bottom, toggleable |
| **Kill switch** | Implemented | Cancels agent execution |
| **User presence** | Implemented | `usePresence` composable, viewers per issue |
| **Field-level presence** | Implemented | Which field each user is viewing/editing |
| **Typing indicators** | Implemented | Agents/users typing |
| **Conflict detection** | Implemented | Warns on multi-user same-field edits |
| **Mock presence generation** | Implemented | Realistic mock presence data for demo |
| **Sync status simulation** | Implemented | `simulateSync()`: OFFLINE_QUEUED → 2s → SYNCING → 0.8s → SYNCED |
| **Mock event stream** | Implemented | `useMockStream` simulates SSE/WebSocket events (#504) |
| **GitHub sync stream** | Implemented | Real mode: `GET /issues/{id}/github-sync/stream` SSE (`connected`/`ping`/`sync`) → `IssueDetailView` refetches on events (#522, §67) |
| **MCP tool-call stream** | Implemented | Real mode: `GET /mcp/tool-calls/stream` SSE feeds the MCP Inspector live tool-call feed (#524, §68) |
| **Issue flag stream** | Implemented | Real mode: `GET /issues/stream` SSE (`connected`/`ping`/`issue-updated`) broadcasts `agent_working` changes to all clients; `issuesStore` subscribes and merges in place (#530) |
| **Chat realtime (Socket.IO)** | Implemented | Real mode: `chatSocket.ts` singleton over Socket.IO (`path: '/socket.io/'`, JWT auth) — `new_message`/`messages_read`/`typing_*` events, room join/leave, reconnect resync; never connects in mock mode (#538/#540, §28) |
| **Notification stream** | Implemented | Real mode: `GET /notifications/stream` SSE (`connected` + snapshot / `ping` / `notification_created`) with per-user fan-out from the JWT and `global`/`system` mirror for `channel=system` inserts; identity via header or `?access_token=` (EventSource cannot send headers) (#550/#551, §21) |

---

## 19. Export & Data Features

| Feature | Status | Details |
|---|---|---|
| **CSV export** | Implemented | `useExport().exportCSV()`, proper escaping (ListView) |
| **JSON export** | Implemented | `useExport().exportJSON()`, pretty-printed (ListView) |
| **SVG export** | Implemented | `exportSVG()` serializes SVG element |
| **PNG export** | Implemented | `exportPNG()`, 2× scale canvas (GraphView, Executive) |
| **Markdown export** | Implemented | `exportMarkdown()`, downloads text file |
| **PDF export** | Implemented | Executive dashboard via html2canvas + jspdf |
| **Graph PNG** | Implemented | Dependency graph export button |
| **Data persistence** | Implemented | Mock data from `dataset-de-pruebas/` volume-mounted into mock-api |
| **Assignee history** | Implemented | Backfilled for all 100 issues, shown in IssueDetailView |
| **Diff download** | Implemented | DiffViewer downloads `.patch` file |

---

## 20. Keyboard Shortcuts & Command Palette

### Keyboard Shortcuts (`useKeyboardShortcuts`)

| Feature | Status | Details |
|---|---|---|
| **Global listener** | Implemented | `initKeyboardShortcuts()` attaches keydown handler |
| **Sequence support** | Implemented | Multi-key sequences (`g` then `i`), 1000ms timeout; prefix keys no longer fire their single-key action immediately |
| **Modifier matching** | Implemented | Ctrl, Shift, Alt, Meta |
| **Input field detection** | Implemented | Skips shortcuts when focused in input/textarea/contenteditable (`Escape` is exempt so panels always close) |
| **Scope system** | Implemented | `global` and `local` scopes; local shortcuts dispatch while the view is mounted and sequences win over same-key locals |
| **Handled events** | Implemented | Already-handled events (`defaultPrevented`) are ignored |

### Registered global shortcuts (App.vue + helpers)

| Shortcut | Action | Source |
|---|---|---|
| `C` | Go to issues list (create flow) | App.vue |
| `D` | Toggle dark mode | App.vue |
| `G` `I` | Go to Issues list | App.vue |
| `G` `K` | Go to Kanban | App.vue |
| `G` `G` | Go to Graph | App.vue |
| `G` `B` | Go to Dashboard | App.vue |
| `G` `U` | Go to Users | App.vue |
| `G` `C` | Go to Components | App.vue |
| `Ctrl`/`Cmd`+`K` | Open command palette | CommandPalette |
| `?` | Show shortcuts help | KeyboardShortcutsHelp |
| `Esc` | Close palette/help | CommandPalette / KeyboardShortcutsHelp |

### Registered local shortcuts (ListView / KanbanView, scope `local`)

| Shortcut | Action | Source |
|---|---|---|
| `J` | Move cursor down (row / card) | ListView / KanbanView |
| `K` | Move cursor up (row / card) | ListView / KanbanView |
| `Enter` | Open the active issue detail | ListView / KanbanView |
| `Esc` | Close top layer (delete confirm, create modal, export menu, governance modal, detail panel) | ListView / KanbanView |

> List/board navigation highlights the active element (`aria-activedescendant` on the `role="grid"` table / `role="listbox"` board, `aria-selected` + visible `outline` on the row/card) and scrolls it into view; `Enter` opens the detail and the panel is labelled `role="dialog"` / `aria-modal`.

### Keyboard navigation state (List / Kanban)

| Feature | Status | Details |
|---|---|---|
| **List cursor** | Implemented | `ListView` cursor over `filteredList`, row ids `issue-row-{i}`, clamped on filter changes |
| **Board cursor** | Implemented | `KanbanView` flat cursor across columns in priority order, card ids `issue-card-{id}`, passed through `KanbanColumn` → `IssueCard` |
| **Detail close** | Implemented | `Esc` restores focus to the active row/card after closing |

### Command Palette (`CommandPalette`)

| Feature | Status | Details |
|---|---|---|
| **Search input** | Implemented | Fuzzy search across pages, actions, issues, components |
| **Recent actions** | Implemented | Shown when query is empty |
| **Page navigation** | Implemented | Jump to any page |
| **Actions** | Implemented | Create issue, toggle dark mode, toggle sidebar, clear filters |
| **Issue/Component search** | Implemented | Search by ID/title or name, opens detail panel |
| **Keyboard navigation** | Implemented | Arrow keys, Enter, Esc; footer hints |
| i18n | Implemented | `palette` section |

### Accessibility - WCAG 2.1 (#523)

| Feature | Status | Details |
|---|---|---|
| **Focus trap** | Implemented | New `composable/useFocusTrap.ts`: Tab/Shift+Tab cycle within the overlay (wraps at boundaries, prefers `[autofocus]`), Escape closes via capture-phase listener (stops propagation so only one handler runs), focus restores to the trigger on deactivate and the listener is removed on unmount |
| **Trapped overlays** | Implemented | `CreateIssueModal`, `GovernanceValidationModal`, `SyncQueueDrawer` (immediate on mount) and `CommandPalette` + `KeyboardShortcutsHelp` (manual activate on open); all expose `role="dialog"`, `aria-modal` and an accessible name (palette/help gained `palette.title` / existing titles) |
| **Side panel** | Implemented | The issue detail overlay is a labelled `role="dialog"` with `aria-modal`; `Esc` closes it (layer priority: delete confirm → create modal → export menu → governance modal → detail) and returns focus to the active row/card |
| **Skip link** | Implemented | First element of `App.vue` is a skip-to-content link (visible on focus) targeting `#main-content` (`main` gets `tabindex="-1"`); i18n key `a11y.skipToContent` |
| **Focus visibility** | Implemented | Global `:focus-visible` outline (brand green, 2px) in `assets/main.css`; interactive list/board surfaces use `focus:outline-none` + row/card highlight |
| **Contrast audit (AA)** | Implemented | Dark-mode secondary text pairs `text-gray-400 dark:text-gray-500` (3.6:1) swapped to `text-gray-500 dark:text-gray-400` (4.8:1 light / 6.6:1 dark), all remaining light-mode `text-gray-400` (2.5:1) raised to `text-gray-500`, standalone `dark:text-gray-500` dark variants raised to `dark:text-gray-400`, placeholders `gray-400` → `gray-500` (`dark:` → `gray-400`); spot-checked chips/badges (`red`/`amber`/`emerald` light+dark pairs ≥4.5:1) and skipped decorative graphics/always-dark code surfaces per WCAG 1.4.11/1.4.6 exemptions |
| **Help modal accuracy** | Implemented | Documents only shortcuts that fire (J/K/Enter/Esc now registered; `Ctrl+K`, `?`, `D`, `C`, `G+*` active); test asserts the exact rendered key set |
| **i18n** | Implemented | `a11y.skipToContent` and `palette.title` added in EN + ES (ASCII in ES) |
| **Tests** | Implemented | New `useFocusTrap.spec.ts` (5), `KeyboardShortcutsHelp.spec.ts` (3), `CreateIssueModal.spec.ts` (3), `ListView.spec.ts` (3), `KanbanView.spec.ts` (2) plus 5 new dispatch cases in `useKeyboardShortcuts.spec.ts` (16 new, 140 total) |
| **Verification** | Implemented | `npm run lint` 0 errors (2 pre-existing `vue/no-mutating-props` warnings), `npm test` 140/140, `npm run build` green (vue-tsc + vite); keyboard-only walk covered by tests (cursor move, open, Escape layer close, Tab traps, skip link) and the contrast sweep left zero `text-gray-400` occurrences unpaired with an AA-compliant dark variant |

---

## 21. Notifications System

| Feature | Status | Details |
|---|---|---|
| **Notification store** | Implemented | `notificationsStore` ramificado por `apiMode`: mock con 12 fixtures + localStorage; real con `GET /notifications` (hidratación), mutaciones optimistas a Mongo y stream #550 — `localStorage` solo en mock (#551) |
| **Backend persistence (MongoDB)** | Implemented | Typed `notifications` collection (`models/notification.py`) with `NotificationMongoRepository`, typed `NotificationStoreError` degradation and idempotent `{user_id, read}` + `{created_at}` indexes (#547) |
| **REST API** | Implemented | `/api/v1/notifications`: GET list with `read`/`category`/`limit`/`offset` filters + pagination meta, PATCH `{id}/read`, POST `mark-all-read`, DELETE `{id}`, POST `clear-all?onlyRead` — `user_id` always from the JWT (404 for foreign ids, 503 when Mongo is down) (#548) |
| **Welcome notification (post-install)** | Implemented | `POST /setup/initialize` seeds the created admin's **two onboarding notifications** — the literal notas.md welcome and the *"Define tus agentes en Usuarios"* pointer — both `WELCOME`/`INFO`/`channel=system` (`requiresAction`, `linkTo: "/users"`) through the #547 repository; Mongo wipe covers `notifications` so reinstalling starts from scratch; degrades to a log without Mongo and skips duplicates via a per-`(user_id, title)` idempotency guard (a rerun inserts only what is missing); both returned by `GET /api/v1/notifications` on first login (#549, #552) |
| **Realtime stream (SSE)** | Implemented | `GET /api/v1/notifications/stream` for the JWT caller: `connected` carries the 50 newest notifications as a snapshot (best-effort `[]` when the store is down), then `notification_created` (camelCase wire) on every insert and `ping` every 15s; per-user fan-out in `RealtimeHub` (system channel mirrored to `global`/`system` topics), subscriber cleanup on close, single publication point `emit_notification_created` fed by the #549 welcome insert; identity via `Authorization` header or `?access_token=` because browser `EventSource` cannot send headers (#550/#551, §18) |
| **Store integration (real mode)** | Implemented | `notificationsApi.ts` (`fetchNotifications`/`markAsRead`/`markAllAsRead`/`deleteNotification`/`clearAll` + `normalizeNotification`); store suscribe `connectSSE('/notifications/stream', { authenticate: true })`, hidrata desde el snapshot `connected`, inserta `notification_created` con dedupe por id + sonido por preferencias, y cierra la conexión al perder la sesión o volver a mock (ciclo de vida tipo `chatStore`); ids locales `notif-` (HITL en cliente) no tocan la API (#551) |
| **Mock data** | Implemented | 12 realistic notifications across 4 categories |
| **Categories** | Implemented | Mention, HITL, Constraint Violation, Agent Failure, SLA + Welcome (`welcome` added in #551 for the #549 system notification) |
| **Read/unread state** | Implemented | Per-notification, visual distinction |
| **Requires action** | Implemented | Amber ACTION badge on actionable notifications |
| **Mark as read** | Implemented | Click notification |
| **Mark all read** | Implemented | Button in header panel |
| **Dismiss** | Implemented | Remove individual notifications |
| **Filtering** | Implemented | Tabs: All, Unread, Requires Action (with counts) |
| **Unread count** | Implemented | Badge on notification bell |
| **Time-ago display** | Implemented | i18n-computed relative time |
| **Click-through** | Implemented | Navigate to linked issue (`linkTo`) |
| **HITL click-through** | Implemented | If `hitlRequestId` set, opens HITLQuickActionModal |
| **Auto HITL notifications** | Implemented | `ensureHitlNotifications()` creates `requiresAction` notifications for pending HITL requests |
| **Severity groups** | Implemented | Panel groups history by criticality: Emergency (violation/agent failure/SLA) → Warning (HITL) → Info (mentions + welcome), sticky group headers with counts (#516/#551) |
| **Channel filter** | Implemented | Chips: All / HITL / Governance / Agent / SLA / Mentions / System on top of tab filters (#516/#551) |
| **Bulk actions** | Implemented | Mark group read + Clear all (filtered) via `markManyRead`/`dismissMany` (#516) |
| **Alert preferences** | Implemented | `notificationsStore.preferences`: per-channel sound on/off persisted (`socialseed-alert-prefs`), mention channel off by default (#516) |
| **NotificationCenter** | Implemented | Teleported dropdown, click-outside close |

---

## 22. Data Layer (Stores)

| Store | State | Key Actions |
|---|---|---|
| `authStore` | user, sessionReady, busy, error, isAuthenticated, role, permissions | initSession, login, loginOAuth, completeOAuth, logout, clearSession, can, hasRole, rolesAllowed (#519, §64) |
| `uiStore` | darkMode, locale, sidebarOpen, viewMode, currentProject, availableProjects, filters, savedSearches, connectionState (SYNCED/OFFLINE_QUEUED/SYNCING/DEGRADED), pendingSyncCount, networkMode (online/degraded/offline), syncQueue[], toastTheme (minimal/rich/enterprise), apiMode/isMockApi | setFilter, clearFilters, saveSearch, applySearch, toggleDarkMode, setLocale, simulateSync (guarded), setNetworkMode, enqueueMutation, flushQueue, removeQueued, retryQueued, resolveConflict, setToastTheme, setApiMode |
| `issuesStore` | issues[], filteredIssues, pagination, loading, selectedIssue | fetchIssues, createIssue, updateIssue, deleteIssue, closeIssue (create/update enqueue + local-apply when offline, #515) |
| `componentsStore` | components[], projects, loading | fetchComponents, createComponent, updateComponent, deleteComponent |
| `usersStore` | users[], loading | fetchUsers, createUser, updateUser, deleteUser |
| `policiesStore` | policies[], loading | fetchPolicies, createPolicy, updatePolicy, deletePolicy (create/update enqueue + local-apply when offline, #515) |
| `constraintsStore` | constraints[], validationResult, hard/soft/active counts | fetchConstraints, createConstraint, updateConstraint, validateConstraints, deleteConstraint |
| `analysisStore` | impactResult, rootCauseResults[], testFailures[] | analyzeImpact, analyzeRootCause, fetchTestFailures, clearResults |
| `notificationsStore` | notifications[], preferences (per-channel sound), unreadCount, unreadByCategory (6 categories), streamConnected | fetchNotifications, startStream, stopStream (real mode: hydrate + #550 SSE with query-token auth, watchers on `authStore.user`/`apiMode`), markAsRead, markAllAsRead, markManyRead, dismiss, dismissMany (optimistic + API for server ids), setChannelSound, getFiltered, ensureHitlNotifications (addNotification triggers configured sound via `useSoundEffects`, #516/#551) |
| `chatStore` | conversations[], messages, activeConversationId, typingUsers[], searchQuery | selectConversation, sendMessage, togglePin, createConversation, simulateTyping |
| `sandboxStore` | rules[] (localStorage drafts), selectedRule, simulationResult, graph | loadGraph (real `/graph/dependencies`), simulateRule/simulatePreview (ruleEngine), createRule, updateRule, deleteRule, promoteRule (#521, §66) |
| `ragStore` | searchResults[], queryStats, error, metrics | Real mode: `searchRag`/`getRagStats` against `/rag/search` + `/rag/stats`; mock keeps 800ms fixtures (#524, §68) |
| `mcpStore` | sessions[], servers[], toolCalls[], selectedSession, isStreaming, error | Real mode: Promise.all of servers/sessions/tool-calls + SSE `connectSSE('/mcp/tool-calls/stream')`; mock keeps fixtures + 5s ticker (#524, §68) |
| `hitlStore` | requests[], selectedRequest, urgentPendingCount/Requests, quickActionRequestId, loadedOnce | fetchRequests, resolveAction, openQuickAction, closeQuickAction |
| `finopsStore` | models[], components[], tasks[], roi[], alerts[], caps[], metrics | updateCap, toggleCap |
| `executiveStore` | kpis[], cycleTime[], debt[], compliance[] | formatTrend, complianceColor |
| `autoHealingStore` | runs[], logs[], fixAttempts[], selectedRunId, running poll | Real mode: init/refresh + startRun/cancelRun/restartRun with 2s polling and patch artifacts; mock arrays + simulateCompletion untouched (#520, §65) |
| `agentReplayStore` | sessions[], currentTime, isPlaying, playSpeed | play, pause, stepForward, stepBackward, seekTo |
| `codeGraphStore` | nodes[], codeEdges[], enabled | fetchCodeStructure, toggle |
| `organizationsStore` | organizations[], currentOrgId, currentWorkspaceId, activeRole, quotaUsage, canEdit/canManage | fetchOrganizations, createOrganization, updateOrganization, setOrg, setWorkspace, setActiveRole, upsertAccount, removeAccount (persists `currentOrg`/`currentWorkspace`/`activeEnterpriseRole` in localStorage; syncs workspace → `uiStore.setProject`) |
| `governanceStore` | matrix (agent x risk x action permission cells), alerts[], activeAlerts, pausedCount | toggleCell, setCell, getCell, resetMatrix, simulateRestrictedAction, resolveAlert (matrix persisted in localStorage `governance-matrix-v1`; approval-level alerts pause/resume issue `agent_working` |
| `auditLogStore` | entries[] (84 deterministic seeded mock events), filters (dateFrom/dateTo/actor/agent/eventType/severity/search), filteredEntries, severityCounts, actors, agents, chain[] (mock hash blocks) | setFilter, clearFilters, exportRows (deterministic PRNG seed 20260924; no API — generated in store per issue spec) |
| `agentStudioStore` | profiles[] (`AgentProfile` library), enabledCount | saveProfile (create/update), cloneProfile, toggleEnabled, removeProfile, markUsed, syncUsers, blankProfile (persists localStorage `agent-studio-v1`; merges studio agents into `usersStore.users` so they survive `fetchUsers` refetch) |
| `analyticsReportStore` | dateRange (from/to), report (ExecutiveReport|null), slaNotified, rangeDays, mttrSeries, healingSeries, healingRate, budgetByProject, slaItems, slaCounts, slaCompliance, comparison (period-to-period), kpis | setPreset, setCustomRange, generateReport (weekly/monthly KPIs + exceptions), clearReport (derives MTTR/healing/budget/SLA from issuesStore + finopsStore + autoHealingStore with seeded FNV fallbacks) |

**24 Pinia stores total.**

---

## 23. API Layer

### Modules (`src/api/`)

| Module | Endpoints | Methods |
|---|---|---|
| `client.ts` | Dual client: mock (`USE_MOCK`/`isMockMode`) vs axios real; Bearer token + single-flight refresh retry on 401; API key header fallback (#519/#517) | — |
| `mockApi.ts` | `fetch` → `/mock-api/mock/*` | issues, components, policies, users, constraints, analysis, agent-logs, dashboard-stats, health, sync-queue, admin seed/reset |
| `authApi` | `/auth/login` (API key → JWT), `/auth/exchange` (OAuth code → session), `/auth/me`, `/auth/refresh`, `/auth/logout`, `/auth/oauth/{provider}/authorize` (github, google) | POST, GET (#519) |
| `authSession` | In-memory access token + refresh queue, `hasValidSession()` (#519) | — |
| `realtime` | `connectSSE` EventSource wrapper with `enabled` gate (mock mode never connects), `authenticate` option appends the in-memory JWT as `?access_token=` on every (re)connect for header-less EventSource clients, used by streams below (#517/#551) | SSE |
| `issuesApi` | `/issues`, `/issues/{id}`, `/issues/{id}/close`, `/blocked-issues` | GET, POST, PATCH, DELETE |
| `componentsApi` | `/components`, `/components/{id}` | GET, POST, PATCH, DELETE |
| `policiesApi` | `/policies`, `/policies/{id}` | GET, POST, PATCH, DELETE |
| `constraintsApi` | `/constraints`, `/constraints/{id}`, `/constraints/validate` | GET, POST, PATCH, DELETE |
| `usersApi` | `/users`, `/users/{id}` | GET, POST, PUT, DELETE |
| `analysisApi` | `/analyze/impact/{id}`, `/analyze/root-cause`, `/test-failures` | GET, POST |
| `systemApi` | `/health`, `/sync-queue` (missing on real backend → defaults), `/admin/seed`, `/admin/reset` | GET, POST |
| `agentLogsApi` | `/issues/{id}/agent-logs` | GET |
| `autoHealingApi` | `/auto-healing/*` runs/logs/start/cancel/restart (#520) | GET, POST |
| `graphApi` | `/graph/dependencies` (+ explore queries, #521/#524) | GET |
| `githubSyncApi` | `/issues/{id}/github-sync`, `/conflicts`, `/resolve`, `/stream` (#522) | GET, POST, SSE |
| `ragApi` | `/rag/search`, `/rag/stats`, `/rag/context` (#524) | GET, POST |
| `mcpApi` | `/mcp/servers`, `/mcp/sessions`, `/mcp/tool-calls`, `/mcp/tool-calls/stream` (#524) | GET, POST, SSE |
| `notificationsApi` | `/notifications`, `/notifications/{id}`, `/notifications/{id}/read`, `/notifications/mark-all-read`, `/notifications/clear-all` (+ `normalizeNotification` wire→UI, #551) | GET, PATCH, POST, DELETE |
| `organizationsApi` | Hardcoded base `/mock-api/mock/organizations` — **not on real backend yet** | GET, POST, PATCH, DELETE |
| `setupApi` | `/setup/status`, `/setup/initialize` (wizard payload: admin, project, policies, `api_key`, `mcp_port`, `confirm_wipe`) — returns installed flag, credentials and master key (#543–#546, §69) | GET, POST |
| `chatSocket` | Socket.IO singleton `io(origen, { path: '/socket.io/', auth: { token } })` for chat realtime; gated by `apiMode` (never connects in mock) (#538/#540, §28) | WS |
| `useAgentStream` | `/issues/{id}/agent-logs/stream` | SSE |

### Mock API server (`mock-api/server.py`)

FastAPI endpoints under `/mock/*`: users CRUD, issues CRUD + agent-logs, components CRUD, policies CRUD, constraints CRUD + validate, organizations CRUD, dashboard-stats, analysis impact/root-cause, test-failures, health, sync-queue, admin seed/reset. Serves JSON from `DATA_DIR` (`frontend/dataset-de-pruebas`). Supports `?project=` filtering on issues.

### nginx routing (frontend container)

- `/api/` → `tasker-api:8000`
- `/mock-api/` → `mock-api:8001`
- `/mcp/` → `tasker-api:8000/mcp` (streamable HTTP for external MCP clients, no buffering — #546, §69)
- `location = /index.html` → `Cache-Control: no-cache` (setup wizard always sees the fresh bundle — #546)

---

## 24. Type System

### Enums
- `IssueStatus`: OPEN, IN_PROGRESS, BLOCKED, CLOSED, WAITING_HUMAN_APPROVAL
- `IssuePriority`: LOW, MEDIUM, HIGH, CRITICAL

### Type Aliases
- `ConstraintCategory`: ARCHITECTURE, TECHNOLOGY, NAMING, PATTERNS, DEPENDENCIES
- `ConstraintSeverity`: HARD, SOFT

### Core Entities (`types/index.ts`)
- `Issue`, `IssueCreateRequest`, `IssueUpdateRequest`
- `Component`, `ComponentCreateRequest`
- `Policy`, `PolicyCreateRequest`
- `User`, `UserCreateRequest`
- `AgentLog`, `AgentLogsBundle`
- `Constraint`, `ConstraintCreateRequest`, `ValidationResult`
- `SystemHealth`, `SyncQueue`, `ServiceStatus`, `SyncQueueItem`
- `ImpactAnalysis`, `CausalLink`, `TestFailure`
- `APIResponse<T>`, `PaginatedResponse<T>`, `PaginationMeta`

### Extended Issue Fields
- `assignee_history?: AssigneeHistoryEntry[]` — reassignment history
- `github_sync?: GitHubSync` — issue_number, github_url, sync_status, last_synced_at
- `governance?: GovernanceValidation` — has_solution_summary, has_file_impact, policy_violations[]
- `affected_files?: AffectedFile[]` — path, change_type (CREATED|EDITED|DELETED), optional `diff_hunk`
- `technical_debt_notes?: string` — Markdown debt observations
- `agent_working_started_at?: string | null` — agent execution start

### Specialized Types (19 files under `types/`)
| File | Types |
|---|---|
| `index.ts` | Core entities above |
| `sandbox.ts` | `SandboxRule`, `SimulationViolation`, `SimulationResult` |
| `rag.ts` | `RAGSearchResult`, `RAGSubGraph`, `RAGContext`, `RAGQueryStats` |
| `notifications.ts` | `Notification`, `NotificationType`, `NotificationPriority` (+ `hitlRequestId?`) |
| `mcp.ts` | `MCPSession`, `MCPTool`, `MCPStatus` |
| `hitl.ts` | `HITLRequest`, `HITLStatus`, `HITLSeverity`, `CodeChange` |
| `finops.ts` | `ROIMetric`, `CostByModel`, `CostByComponent`, `CostByTask`, `BudgetAlert`, `CostCap`, `FinOpsMetrics` |
| `executive.ts` | `ExecutiveKPI`, `CycleTimeData`, `DebtReduction`, `ComplianceItem` |
| `codeGraph.ts` | `CodeNode`, `CodeEdge`, `CodeStructureData` |
| `chat.ts` | `Conversation`, `ChatMessage`, `ChatMessageType`, `Participant`, `ConversationType` |
| `autoHealing.ts` | `PipelineStage`, `PipelineRun`, `LogEntry`, `FixAttempt` (+ `diffPreview?`) |
| `agentReplay.ts` | `AgentSession`, `ReplayEvent`, `EventType`, `EventSeverity` |
| `audit.ts` | `AuditEntry`, `AuditAction`, `AuditMetadata` |
| `organizations.ts` | `Organization`, `Workspace`, `EnterpriseAccount`, `OrganizationQuota`, `DataRetentionPolicy`, `EnterpriseRole`, `OrganizationPlan`, `OrganizationCreateRequest` |
| `governance.ts` | `GovernanceAgentType`, `GovernanceRiskLevel`, `GovernanceActionId`, `PermissionState`, `PermissionMatrix`, `RestrictedActionAlert` |
| `auditLog.ts` | `AuditLogEntry`, `AuditLogEventType`, `AuditLogSeverity`, `AuditLogFilters`, `AuditChainBlock`, `AUDIT_EVENT_TYPES`, `AUDIT_SEVERITIES` |
| `graphExplorer.ts` | `ExplorerNodeType`, `EdgeRelation`, `InspectorPayload`, `InspectorField`, `InspectorLink`, `BlastRadiusStats`, `EdgeInspectorInfo`, `TraceSelectOption` |
| `agentStudio.ts` | `AgentProfile`, `AgentLimits`, `AGENT_MODELS`, `AGENT_TOOLS`, `PROMPT_VARIABLES`, `DEFAULT_LIMITS` |
| `analytics.ts` | `SLAStatus`, `SLA_HOURS`, `SLAIssueMetric`, `MTTRPoint`, `HealingPoint`, `ProjectBudget`, `PeriodComparison`, `ReportKPI`, `ReportException`, `ExecutiveReport` |

---

## 25. CRUD Matrix

| Entity | Create | Read | Update | Delete | Validate | Export |
|---|---|---|---|---|---|---|
| Issues | Modal | Table/Kanban/Graph/Board | Detail Panel | Confirm | — | CSV/JSON |
| Components | Modal | Table/Grid | Detail Panel | Confirm | — | — |
| Policies | Modal | Card Grid | Modal | Confirm | — | — |
| Constraints | Modal | Table | Modal | Confirm | Validate btn | — |
| Users (human) | Modal | Card Grid | Modal | Confirm | — | — |
| Users (agent) | Modal | Card Grid | Modal | Confirm | — | — |
| System | — | Dashboard | — | — | Seed/Reset | — |
| Notifications | Auto (HITL) | Panel | Mark read | Dismiss | — | — |
| Conversations | Modal | ChatView / FloatingChat | — | — | — | — |
| Messages | Input | Chat bubbles | — | — | — | — |
| Sandbox Rules | — | List | — | — | Simulate | Report |
| MCP Sessions | — | List | — | — | Execute | — |
| HITL Requests | — | List + global banner | Approve/Reject/Modify (modal or center) | — | — | — |
| FinOps Caps | — | Dashboard | Toggle / slider | — | — | — |
| Saved Searches | FilterBuilder | FilterBuilder dropdown | Apply | Remove | — | — |

---

## 26. Interactions Matrix

| Interaction | Location |
|---|---|
| Drag-and-drop | KanbanView |
| Text search | ListView, ComponentsView, ConstraintsView, GraphView, CommandPalette, ChatSidebar, RAG Explorer |
| Multi-criteria filters | ListView, KanbanView (`FilterBuilder`: chips, AND/OR, dates, saved searches) |
| Dropdown filters | ListView (status, priority, component), ConstraintsView (category, severity), GraphView (status, component, max hops) |
| View mode toggle | ComponentsView (table/grid) |
| Layout toggle | GraphView (hierarchical/force-directed) |
| Dark mode toggle | UserMenu, `D` shortcut, CommandPalette |
| Language switch | UserMenu (EN/ES) |
| Click-to-detail | List rows, Kanban cards, Graph nodes, Component cards, Constraint rows, Notification items |
| Slide-in panels | IssueDetailView, Component detail, Constraint detail, MCP session, Auto-healing run, Replay session, HITL request |
| Modal overlays | Create/Edit forms, Relationship modal, Command palette, Shortcuts help, Governance modal, HITL quick action, PII warning, New conversation |
| Confirm dialogs | Delete actions, admin reset/seed, Kanban card delete |
| SVG chart rendering | TrendChart, DailyActivity, AvgResolution, ImpactSvgTree, AgentCostChart |
| Graph visualization | GraphView (vis-network) |
| Markdown rendering | IssueDetailView (reasoning/progress/tech-debt), RichTextEditor preview, RootCausePanel, ChatMessage |
| Mermaid diagrams | MarkdownRenderer |
| Diff viewing | IssueDetailView ProgressTab, HITLCommandCenter CodeChange, agent logs (unified/split, copy, download) |
| Validation workflow | ConstraintsView → results banner |
| Admin operations | Seed/Reset with confirmation |
| Auto-refresh | TeamTicker (10s) |
| Click-outside close | UserMenu, modals, NotificationCenter, ProjectSelector, CommandPalette, FilterBuilder dropdowns |
| Slash commands | RichTextEditor (`/` prefix, 13 command types) |
| Keyboard shortcuts | Global hotkeys, `g` sequences, palette, help modal |
| Bulk operations | ListView multi-select + BulkActionsBar |
| Export dropdown | ListView CSV/JSON; Graph PNG; Executive PDF/PNG |
| Toast notifications | `useToast`, 4 types, auto-dismiss |
| Real-time streaming | Agent log SSE with auto-reconnect; mock event stream |
| Presence tracking | Per-issue viewers, field-level presence |
| Conflict detection | Multi-user edit detection |
| Relationship creation | GraphView connect mode with cycle detection |
| Real-time chat | ChatView exchange, agent auto-responses, typing indicators |
| Floating chat | Persistent Messenger-style widget |
| Chat search / pin | Filter conversations; pin to top |
| Code sharing | Triple-backtick code blocks in chat |
| PII detection | Live in ChatInput, modal on critical PII |
| Code overlay | Toggle AST nodes in GraphView |
| Pipeline monitoring | Auto-healing 5-stage progress + terminal logs + fix diffs |
| Agent replay | Scrubber timeline, play/pause/step, 1x/2x/4x |
| FinOps heatmap | Cost by model/component charts, caps toggles |
| Executive export | PDF/PNG via html2canvas + jspdf |
| Governance validation | Block closure when requirements unmet |
| GitHub sync | Sync status + Force Re-sync in issue detail |
| Agent timer / kill | Live timer + stop on Kanban cards |
| Sync status badge | Header connection indicator |
| Project filtering | Filter all issue views by selected project |
| Affected files / tech debt | ProgressTab badges, Markdown debt notes, per-file diffs |
| HITL everywhere | Header banner, quick action modal, notification click-through, issue status sync |
| Mobile navigation | Hamburger → MobileDrawer; snap-scroll Kanban; responsive tables/headers |

---

## 27. i18n Coverage

### Locale Files
- `en.json`: 1680 leaf keys, **78** top-level sections
- `es.json`: 1680 leaf keys, matching structure (both balanced)

### Sections (78)
`kanban`, `mobileNav`, `nav`, `header`, `menu`, `dashboard`, `issues`, `githubSync`, `governance`, `agent`, `components`, `policies`, `constraints`, `users`, `graph`, `codeOverlay`, `analysis`, `system`, `auth`, `common`, `dashboardStats`, `boardModules`, `boardSections`, `trendChart`, `statusDistribution`, `dailyActivity`, `avgResolution`, `statsCard`, `a11y`, `shortcuts`, `palette`, `editor`, `diff`, `hitl`, `audit`, `stream`, `tokens`, `notifications`, `agents`, `toast`, `chat`, `mcp`, `hitlCenter`, `floatingChat`, `presence`, `projects`, `sync`, `export`, `bulkActions`, `profile`, `commandPalette`, `sandbox`, `rag`, `finops`, `autoHealing`, `replay`, `pii`, `executive`, `mockStream`, `filterBuilder`, `diffPreview`, `hitlBanner`, `hitlQuickAction`, `organizations`, `governanceMatrix`, `graphExplorer`, `auditLog`, `piiSuite`, `agentStudio`, `analytics`, `sla`, `offline`, `syncQueue`, `soundEffects`, `toastTheme`, `notifPanel`, `apiMode`, `setup`

### Coverage
- All user-visible text uses `t()`
- Form labels, placeholders, error messages translated
- Button text and aria-labels translated
- Status/priority/type labels translated
- Time-ago strings computed with i18n
- Audit trail descriptions use parameterized i18n
- Slash commands, toasts, chat, floating chat, PII warnings translated
- Executive, FinOps, auto-healing, replay, GitHub sync, governance, agent timer, sync status translated
- Setup wizard credentials, policies and MCP panel translated (`setup.*`, §69)
- HITL center, banner, and quick-action labels translated
- FilterBuilder and diff-preview labels translated
- Mobile nav labels translated
- Language persisted in localStorage; switchable from UserMenu

---

## 28. Chat System (ChatView)

| Feature | Status | Details |
|---|---|---|
| **Full-page layout** | Implemented | Split view with sidebar (320px) and message area |
| **Conversation list** | Implemented | Search, avatars, online status, unread badges, pin toggle |
| **New conversation modal** | Implemented | Title, participants (from store), group/individual |
| **Message display** | Implemented | Markdown rendering, code blocks, agent action badges, reactions |
| **Message input** | Implemented | Auto-resize textarea, typing indicator, PII detection |
| **Code sharing** | Implemented | Triple-backtick code blocks |
| **Agent responses** | Implemented | Simulated AI agent auto-replies |
| **Typing indicators** | Implemented | Animated dots while typing |
| **Read status** | Implemented | Blue checkmarks (sent / delivered / read) |
| **Emoji reactions** | Implemented | Reaction bar on messages |
| **Search** | Implemented | Filter conversations by name or participant |
| **Pin/unpin** | Implemented | Pin conversations to top of list |
| i18n | Implemented | All labels in `chat` section |

### Real API contract (#539)

Backend REST + Socket.IO chat contract (MongoDB #537, servidor Socket.IO #538). Identity:
JWT `sub`, token API-key, cookie OAuth o header `X-User-ID` (solo con auth deshabilitada).

| Endpoint | Method | Details |
|---|---|---|
| `/api/v1/chat/conversations` | GET | Conversaciones del usuario con `lastMessage` (orden por `updatedAt`) |
| `/api/v1/chat/conversations` | POST | `participantIds` (direct=2 / group>=2, sin duplicados) |
| `/api/v1/chat/conversations/{id}/messages` | GET | Histórico paginado `limit` + cursor `before` (created_at ISO); 403 no participante |
| `/api/v1/chat/conversations/{id}/messages` | POST | Persiste con `senderId` = JWT `sub` y emite `new_message` a la sala (dispatcher `app.state.chat_emit`) |
| `/api/v1/chat/conversations/{id}/pin` | POST | Alterna `pinnedBy` del usuario |

Wire camelCase (envelope `APIResponse` + eventos Socket.IO, contrato de #540):

- **Conversación:** `id`, `title`, `type`, `participantIds`, `pinnedBy`, `createdAt`, `updatedAt`, `lastMessage?`
- **Mensaje:** `id`, `conversationId`, `senderId`, `content`, `type`, `readBy`, `reactions` (`{emoji: [user_ids]}`), `createdAt`
- **Eventos:** servidor → `new_message`/`messages_read` (`{conversationId,userId,matchedCount}`)/`typing_*` (`{conversationId,userId}`); acks `{conversationId, joined|left|typing}`. Entrada acepta `conversation_id` o `conversationId`.

### Realtime frontend (#540)

Cliente `socket.io-client` ^4.8 en `frontend/src/api/chatSocket.ts`: singleton `io(origen, { path: '/socket.io/', auth: { token } })` con el JWT activo (origen derivado de `window.__API_URL__`), gate por `apiMode` (en mock **nunca** conecta) y estados `connecting/connected/reconnecting/disconnected` con el backoff nativo de socket.io.

- **Ciclo de vida (`chatStore.ts`):** conecta al entrar en modo real y al aparecer la sesión; `join_room` + `mark_as_read` al abrir una conversación, `leave_room` al cambiar; re-join del activo en cada (re)conexión; desconecta al volver a mock o perder la sesión (logout recarga la página).
- **Listeners:** `new_message` → inserta con dedupe por `id`, actualiza `lastMessage`/no leídos y emite `mark_as_read` si está activa; `typing_start`/`typing_stop` → `typingUsers` (auto-limpieza a los 7s); `messages_read` → `readBy`.
- **Modo real:** hidrata la lista con `GET /chat/conversations`, carga mensajes al seleccionar (`limit=50`), envía por `POST .../messages` (fallback local si la API cae, sin simulación de agente) y tras `reconnect` resincroniza con merge de la última página (`limit=100`).
- **UI:** chip de estado en el header de ChatView + estado vacío y punto en el widget flotante (claves `chat.connectionConnected|Connecting|Reconnecting|Disconnected`); debounce de `typing_start` al escribir (2s inactivo → `typing_stop`). Modo mock intacto (fixtures con copias frescas al volver).

### Chat test suite (#541)

Batería que blinda #536–#540 sin servicios externos (repo fake/memoria, sin containers ni red):

- **Backend (`tests/api/`):** `test_chat_socketio.py` impulsa el `ChatSocketIOServer` real envuelto en `socketio.ASGIApp` mediante el transporte websocket ASGI en memoria de `TestClient` (framing EIO/SIO manual; `python-socketio` ≥5 ya no incluye `test_client`): handshake con JWT válido acepta y con token ausente/inválido/expirado rechaza (`44` CONNECT_ERROR), guards de sala (`FORBIDDEN`/`NOT_FOUND`/`VALIDATION_ERROR`), 2 clientes en la misma sala (`send_message` → `new_message` con el payload persistido), `typing_start`/`typing_stop` sin eco al emisor (`skip_sid`), `mark_as_read` → `messages_read` broadcast con `matchedCount` y `POST` REST → evento recibido por el cliente conectado (mismo proceso). `test_chat_endpoints.py` amplía autoría: `senderId` y creador salen siempre del JWT (ignora spoofing por body y `X-User-ID`).
- **Frontend (`vitest`):** `chatStore.spec.ts` (17 tests) cubre modo real con `socket.io-client` mockeado (conexión + hidratación, join/leave, re-join en `connect`, `new_message` con dedupe/unread/`mark_as_read`, typing con auto-limpieza a 7s, `messages_read`, reconexión con resync `limit=100`, envío por API con dedupe del eco y fallback offline, conmutación `apiMode`) y modo mock (fixtures sin abrir socket); `ChatView.spec.ts` (5 tests) verifica `notifyTyping` al escribir, envío con Enter (trim) y bloqueo de PII crítica con enmascarado `[REDACTED_SECRET]` previo al envío (máscara/cancelar/confirmar).
- **Gates:** pytest `1247 passed / 27 skipped / 3 failed` (3 preexistentes), ruff 1011 / mypy 1152-133 sin cambios; frontend `237 passed / 30 ficheros`, lint 0 errores y build verdes.

---

## 29. Floating Chat Widget

| Feature | Status | Details |
|---|---|---|
| **Persistent widget** | Implemented | Messenger-style bottom-right bubble, present in all views |
| **Expand/collapse** | Implemented | Toggle between compact icon and full 380px window |
| **Mini message list** | Implemented | Recent messages for active conversation |
| **Input** | Implemented | Mini input at bottom of expanded window |
| **Open full chat** | Implemented | Emits `openFullChat` → navigates to `/chat` |
| i18n | Implemented | `floatingChat` section |

---

## 30. MCP Inspector (MCPInspectorView)

| Feature | Status | Details |
|---|---|---|
| **Session list** | Implemented | Cards: session name, server, model, status badge |
| **Session detail** | Implemented | Slide-in panel with tools list, status, model info |
| **Mock data** | Implemented | Mock mode: 2 sessions (code-creator active, data-analyst idle) |
| **Live mode (#524)** | Implemented | Real mode: live registry (LIVE/MOCK badge), servers panel, latency table, payload modal, re-run, SSE tool-call feed — see §68 |
| **Store** | Implemented | `mcpStore.ts` (fixtures vs REST+SSE branch) |
| i18n | Implemented | `mcp` section |

---

## 31. HITL Command Center (HITLCommandCenter)

| Feature | Status | Details |
|---|---|---|
| **Request list** | Implemented | Cards: title, severity badge, status, agent info |
| **Request detail** | Implemented | Slide-in panel with description, approve/reject/modify |
| **Code change diffs** | Implemented | DiffViewer on request `CodeChange` payloads |
| **Severity levels** | Implemented | CRITICAL (red), HIGH (orange), MEDIUM (blue), LOW (gray) |
| **Status tracking** | Implemented | PENDING → APPROVED/REJECTED/MODIFIED |
| **Mock data** | Implemented | 3 requests across multiple statuses |
| **Store** | Implemented | `hitlStore.ts` with fetch guard (`loadedOnce`) |
| **Global HITL banner** | Implemented | Persistent AppHeader banner when CRITICAL/HIGH pending; count, click-through, Review button |
| **Quick action modal** | Implemented | HITLQuickActionModal: approve/reject/modify + textarea, impact stats, View Full Context → Command Center |
| **Issue status sync** | Implemented | Approve → IN_PROGRESS, Reject → OPEN, Modify → IN_PROGRESS on related issue |
| **Auto notifications** | Implemented | `ensureHitlNotifications` creates requiresAction notifications; click opens quick action modal |
| **Mock issue statuses** | Implemented | ISS-042, ISS-051, ISS-081 set to `WAITING_HUMAN_APPROVAL` |
| i18n | Implemented | `hitlCenter`, `hitlBanner`, `hitlQuickAction` |

---

## 32. Policy Sandbox (PolicySandboxView)

| Feature | Status | Details |
|---|---|---|
| **Rule list** | Implemented | Cards: rule name, status badge, severity, scope |
| **Simulation** | Implemented | Simulate → impact report |
| **Impact report** | Implemented | Pass/fail, violation details with severity |
| **Rule promotion** | Implemented | Promotes the simulated rule to a real backend policy (`POST /policies`, #521 — §66) |
| **Draft rules** | Implemented | Seeded drafts persisted in `localStorage`; simulated on the real dependency graph (`/graph/dependencies`) — §66 |
| **Store** | Implemented | `sandboxStore.ts` |
| i18n | Implemented | `sandbox` section |

---

## 33. Graph RAG Explorer (GraphRAGExplorerView)

| Feature | Status | Details |
|---|---|---|
| **Search input** | Implemented | Text field + search button, Enter key |
| **Results list** | Implemented | Cards: entity name, type, score, sub-graph preview |
| **Query stats** | Implemented | Tokens, nodes, edges, sub-graph count |
| **Mock data** | Implemented | Mock mode: 2 results (authentication-service, payment-service) |
| **Live mode (#524)** | Implemented | Real mode: `POST /rag/search` over real Neo4j vector index + `GET /rag/stats` metrics — see §68 |
| **Store** | Implemented | `ragStore.ts` |
| i18n | Implemented | `rag` section |

---

## 34. Agent FinOps Dashboard (AgentFinOpsView)

| Feature | Status | Details |
|---|---|---|
| **Summary cards** | Implemented | 5 cards: Total Cost, Avg/Task, Avg/Component, ROI, Active Models |
| **Cost by model** | Implemented | Horizontal bars: model, cost, token count |
| **Cost by component** | Implemented | Bars: component name, task count |
| **ROI table** | Implemented | 7 ROI periods: spend, savings, ROI %, time saved |
| **Budget alerts** | Implemented | Active alerts with model, message, threshold |
| **Cost caps** | Implemented | Toggle switches per model |
| **Cost cap sliders** | Implemented | Adjust monthly budget limit per model |
| **Mock data** | Implemented | 4 models, 7 components, 7 ROI periods, 3 alerts, 4 cost caps |
| **Store** | Implemented | `finopsStore.ts` |
| i18n | Implemented | `finops` section |

---

## 35. Auto-Healing Pipeline Monitor (AutoHealingMonitorView)

| Feature | Status | Details |
|---|---|---|
| **Summary cards** | Implemented | 5 cards: Total Runs, Healing Rate, Avg Duration, Active Fixes, Auto-Fix % |
| **Run list** | Implemented | Cards: pipeline name, status badge, duration, stage progress |
| **Run detail** | Implemented | Slide-in with 5-stage pipeline progress bar |
| **Live terminal** | Implemented | Scrollable logs with colored stage indicators |
| **Fix attempts** | Implemented | Description, test output, `diffPreview` code block |
| **Mock data** | Implemented | Mock mode: 3 runs, 12 log entries, 3 fix attempts |
| **Real pipeline (#520)** | Implemented | Real mode: Start/Cancel/Restart runs, patch artifacts, 2s log polling — see §65 |
| **Store** | Implemented | `autoHealingStore.ts` |
| i18n | Implemented | `autoHealing` section |

---

## 36. Agent Replay Player (AgentReplayView)

| Feature | Status | Details |
|---|---|---|
| **Session list** | Implemented | Cards: title, agent, date, duration, event count |
| **Session detail** | Implemented | Slide-in: event stream, files affected, Cypher queries |
| **Scrubber timeline** | Implemented | Horizontal bar, clickable seek |
| **Playback controls** | Implemented | Play/Pause, Step ±, speed 1x/2x/4x |
| **Event stream** | Implemented | Color-coded events by type |
| **Files affected panel** | Implemented | Files modified during replay |
| **Cypher queries** | Implemented | Neo4j queries executed in session |
| **Mock data** | Implemented | 2 sessions, 21 total replay events |
| **Store** | Implemented | `agentReplayStore.ts` |
| i18n | Implemented | `replay` section |

---

## 37. Executive Dashboard (ExecutiveDashboardView)

| Feature | Status | Details |
|---|---|---|
| **KPI cards** | Implemented | 4 cards: Velocity, Cycle Time, Agent ROI, Tech Debt Score |
| **Cycle time comparison** | Implemented | Table showing 7× speedup (human vs AI-assisted) |
| **Tech debt reduction** | Implemented | Bar chart, 6-month trend |
| **Architecture compliance** | Implemented | Ring gauges for 7 compliance areas |
| **PDF export** | Implemented | html2canvas + jspdf → `executive-report.pdf` |
| **PNG export** | Implemented | html2canvas → `executive-dashboard.png` |
| **Mock data** | Implemented | 4 KPIs, 6 cycle-time categories, 6 months debt, 7 compliance areas |
| **Store** | Implemented | `executiveStore.ts` |
| i18n | Implemented | `executive` section |

---

## 38. PII & Secrets Guardrail

| Feature | Status | Details |
|---|---|---|
| **PII detection engine** | Implemented | 10 regex patterns in `piiDetector.ts` |
| **Detection targets** | Implemented | API keys, JWT tokens, private keys, passwords, bearer tokens, emails, phones, SSN, credit cards, IP addresses |
| **Severity levels** | Implemented | Critical (API keys, private keys, passwords), High (tokens, SSN, credit cards), Medium (emails, phones), Low (IPs) |
| **Inline banner** | Implemented | `PIIDetectionBanner.vue` in ChatInput |
| **Warning modal** | Implemented | `PIIWarningModal.vue`: Cancel / Mask & Send / Send Anyway |
| **Live detection** | Implemented | On every keystroke in ChatInput; blocks critical PII |
| **Text masking** | Implemented | `redactText()` masks sensitive patterns |
| **Colors** | Implemented | `getSeverityColor()` / `getSeverityBg()` |
| i18n | Implemented | `pii` section |

---

## 39. Code Graph Overlay

| Feature | Status | Details |
|---|---|---|
| **AST node types** | Implemented | File, Class, Function |
| **Node rendering** | Implemented | Database (files), Diamond (classes), Triangle (functions) |
| **Color coding** | Implemented | Cyan (files), Teal (classes), Emerald (functions) |
| **Overlay toggle** | Implemented | Show/hide code nodes with issue nodes in GraphView |
| **Code node detail** | Implemented | File path, language, lines, type |
| **Types** | Implemented | `codeGraph.ts` |
| **Store** | Implemented | `codeGraphStore.ts` (13 mock nodes + 17 edges) |
| **Graph algorithms** | Implemented | `graphUtils.ts`: BFS, cycle detection, blast radius, transitive deps |
| i18n | Implemented | `codeOverlay` section |

---

## 40. GitHub Sync Widget

| Feature | Status | Details |
|---|---|---|
| **Sync data** | Implemented | All 100 mock issues have `github_sync` (alternating SYNCED/PENDING_PUSH/ERROR) |
| **Issue link** | Implemented | Clickable `#issue_number` → GitHub URL |
| **Status badge** | Implemented | Green SYNCED, yellow PENDING_PUSH, red ERROR |
| **Last synced** | Implemented | Timestamp of last sync |
| **Force Re-sync** | Implemented | Button with spinner; mock mode simulates a sync cycle |
| **Live sync & conflicts (#522)** | Implemented | Real mode: real webhook-driven sync, conflict panel with Keep local / Keep remote / Merge, SSE-driven updates — see §67 |
| **Component** | Implemented | `GitHubSyncCard.vue` |
| **Integration** | Implemented | IssueDetailView Details tab (conditional on `issue.github_sync`) |
| i18n | Implemented | `githubSync` section |

---

## 41. Governance Validation Modal

| Feature | Status | Details |
|---|---|---|
| **Governance data** | Implemented | All 100 mock issues have `governance` (alternating valid/invalid) |
| **Violation detection** | Implemented | Checks `has_solution_summary`, `has_file_impact`, `policy_violations[]` |
| **Modal display** | Implemented | Warning icon, issue title, violated policies, missing requirements checklist |
| **Fix Issues button** | Implemented | Closes modal, reverts status change |
| **Override button** | Implemented | Forces closure despite violations |
| **Kanban intercept** | Implemented | Blocks drop to CLOSED, shows modal |
| **Detail intercept** | Implemented | Blocks CLOSED in `save()`, shows modal |
| **Component** | Implemented | `GovernanceValidationModal.vue` |
| **Write-time violations** | Implemented | #532: violaciones en escritura devuelven 409 estructurado (`POLICY_VIOLATION`/`CIRCULAR_DEPENDENCY`) con policy/constraint + sugerencia, superficie en el flujo de creación de dependencias |
| i18n | Implemented | `governance` section |

---

## 42. Network Status & Sync Indicator

| Feature | Status | Details |
|---|---|---|
| **Connection state** | Implemented | `uiStore.connectionState`: SYNCED, OFFLINE_QUEUED, SYNCING, DEGRADED |
| **Pending count** | Implemented | `uiStore.pendingSyncCount` (mirrors offline queue length) |
| **Sync simulation** | Implemented | OFFLINE_QUEUED → 2s → SYNCING → 0.8s → SYNCED; guarded to not clobber offline queue |
| **Visual indicator** | Implemented | `SyncStatusBadge.vue` (clickable button → `SyncQueueDrawer`), color-coded, animated ping |
| **Colors** | Implemented | Green SYNCED, Yellow OFFLINE_QUEUED, Blue SYNCING, Amber DEGRADED/Offline |
| **Integration** | Implemented | AppHeader between ProjectSelector and NotificationCenter (hidden below `sm`) |
| **Trigger points** | Implemented | ListView, KanbanView, GraphView call `simulateSync()` after CRUD |
| i18n | Implemented | `sync` section |

---

## 43. Agent Timer & Kill Switch

| Feature | Status | Details |
|---|---|---|
| **Timer data** | Implemented | `agent_working_started_at` on Issue, set for agent_working issues; also exposed by the real API as `IssueResponse.agent_working_started_at` (#530) |
| **Live timer** | Implemented | Updates every second; "Xh Ym Zs" or "Ym Zs" |
| **Kill button** | Implemented | Red stop icon on hover; calls `POST /issues/{id}/stop-agent` (#530) |
| **Timer cleanup** | Implemented | Interval cleared on unmount |
| **Dedicated endpoints** | Implemented | `POST /issues/{id}/start-agent` / `stop-agent` aliases over `agent/start`/`agent/finish` with `agent_id` optional (default `manual`); 404/409 documented (#530) |
| **Store actions** | Implemented | `issuesStore.startAgent()` / `stopAgent()` replace the issue in place; used by the kill switch and governanceStore (#530) |
| **Cross-client sync** | Implemented | SSE `issue-updated` → `issuesStore.applyIssueUpdate()` updates icon/timer in every connected window (#530) |
| **Component** | Implemented | `IssueCard.vue` |
| i18n | Implemented | `agent` section (killSwitch, agentStopped) |

---

## 44. Tech Debt & Affected Files

| Feature | Status | Details |
|---|---|---|
| **Affected files data** | Implemented | All 100 mock issues have `affected_files[]` with realistic paths |
| **Change type badges** | Implemented | Green CREATED/NEW, blue EDITED, red DELETED |
| **File paths** | Implemented | Mono-font paths |
| **Per-file diff preview** | Implemented | Expand/collapse DiffViewer using `diff_hunk` |
| **Tech debt notes** | Implemented | Markdown strings (every 3rd issue), amber container |
| **Debt styling** | Implemented | Amber container with MarkdownRenderer |
| **Empty states** | Implemented | "No files affected" / "No tech debt recorded" |
| **ProgressTab integration** | Implemented | Affected Files + Tech Debt Notes sections |
| i18n | Implemented | `issues.affectedFiles`, `issues.noAffectedFiles`, `issues.techDebtNotes`, `issues.changeType.*`, `diffPreview.*` |

---

## 45. Project Filtering

| Feature | Status | Details |
|---|---|---|
| **Project selector** | Implemented | `ProjectSelector.vue`: socialseed-tasker, auth-service, api-gateway, data-pipeline |
| **localStorage persistence** | Implemented | `currentProject` key |
| **Issue filtering** | Implemented | `issuesStore.filteredIssues` filters by `project_id` |
| **Mock data distribution** | Implemented | 70 (socialseed-tasker), 15 (auth-service), 15 (api-gateway); data-pipeline has 0 issues today |
| **API filtering** | Implemented | Mock API `?project=` query parameter |
| **View integration** | Implemented | ListView, KanbanView, GraphView use `filteredIssues` |
| **Empty state** | Implemented | "No issues in this project" |
| i18n | Implemented | `issues.noProjectIssues`, `issues.noProjectIssuesHint` |

---

## 46. Advanced Multi-Criteria Filters

| Feature | Status | Details |
|---|---|---|
| **Component** | Implemented | `FilterBuilder.vue` (#505) |
| **Criteria** | Implemented | Status (multi), Priority (multi), Labels (multi), Assignee (multi), Component, Search, Has Tech Debt, Has Affected Files, Date From/To |
| **Boolean operator** | Implemented | AND / OR toggle applied to filter set |
| **Active chips** | Implemented | Color-coded removable chips per criterion + Clear All |
| **Saved searches** | Implemented | Named snapshots persisted in localStorage via `uiStore.savedSearches`; apply/delete from dropdown |
| **State ownership** | Implemented | `uiStore.filters` + `setFilter` / `clearFilters` / `saveSearch` / `applySearch` |
| **Integration** | Implemented | ListView and KanbanView toolbars |
| i18n | Implemented | `filterBuilder` section |

---

## 47. Mock Event Stream (SSE Simulation)

| Feature | Status | Details |
|---|---|---|
| **Composable** | Implemented | `useMockStream.ts` (#504) |
| **Purpose** | Implemented | Simulates server-sent events / WebSocket traffic without a live backend |
| **Consumers** | Implemented | Feeds presence, typing, notification-style UI updates in mock mode |
| **i18n** | Implemented | `mockStream` section |

---

## 48. Mobile Responsive Design

| Feature | Status | Details |
|---|---|---|
| **Adaptive sidebar** | Implemented | Hidden below `md` (768px); desktop hover-expand unchanged |
| **Hamburger menu** | Implemented | 44×44px in AppHeader (`md:hidden`), emits `open-mobile-menu` |
| **MobileDrawer** | Implemented | Overlay slide-in from left (300ms), tap overlay or swipe-left to close, full nav groups |
| **App layout offset** | Implemented | `md:ml-20` only on desktop; mobile full width |
| **IssueDetailView** | Implemented | Full-width up to `max-w-lg`; field grids 1-col on mobile; tab bar horizontal scroll |
| **Kanban snap scroll** | Implemented | `snap-x snap-mandatory`, `85vw` columns, edge gradient indicators |
| **ListView table** | Implemented | Component/Labels/Created columns hidden below md/lg/sm; action buttons 44×44 |
| **ComponentsView table** | Implemented | `overflow-x-auto` + `min-w-[640px]` |
| **ConstraintsView table** | Implemented | `overflow-x-auto` + `min-w-[720px]` |
| **Touch targets** | Implemented | Primary buttons, nav items, row actions ≥ 44px |
| **Responsive headers** | Implemented | Wrap on narrow screens; title scales `text-xl`/`sm:text-2xl` |
| **SyncStatusBadge** | Implemented | Hidden below `sm` to prevent header overflow |
| i18n | Implemented | `mobileNav.*` (EN/ES) |

---

## 49. Route & View Inventory

### Router (`src/router/index.ts`)

| Path | Name | View |
|---|---|---|
| `/` | — | Redirect → `/board` |
| `/board` | Board | BoardView.vue |
| `/system` | System | DashboardSystemView.vue |
| `/kanban` | Kanban | KanbanView.vue |
| `/list` | List | ListView.vue |
| `/graph` | Graph | GraphView.vue |
| `/components` | Components | ComponentsView.vue |
| `/policies` | Policies | PoliciesView.vue |
| `/constraints` | Constraints | ConstraintsView.vue |
| `/sandbox` | PolicySandbox | PolicySandboxView.vue |
| `/rag` | GraphRAGExplorer | GraphRAGExplorerView.vue |
| `/finops` | AgentFinOps | AgentFinOpsView.vue |
| `/auto-healing` | AutoHealing | AutoHealingMonitorView.vue |
| `/replay` | AgentReplay | AgentReplayView.vue |
| `/executive` | ExecutiveDashboard | ExecutiveDashboardView.vue |
| `/users` | Users | UsersView.vue |
| `/chat` | Chat | ChatView.vue |
| `/profile` | Profile | ProfileView.vue |
| `/analysis` | Analysis | AnalysisView.vue |
| `/mcp` | MCPInspector | MCPInspectorView.vue |
| `/hitl` | **HITLCommandCenter** | HITLCommandCenter.vue |
| `/organization` | **OrganizationSettings** | OrganizationSettingsView.vue |
| `/governance-matrix` | **GovernanceMatrix** | GovernanceMatrixView.vue |
| `/audit-log` | **AuditLog** | AuditLogView.vue |
| `/agents/studio` | **AgentStudio** | AgentStudioView.vue |
| `/analytics` | **Analytics** | AnalyticsDashboardView.vue |
| `/auth/oauth-callback` | **AuthCallback** | AuthCallbackView.vue (OAuth code exchange, error state, fallback) |
| `/setup` | **Setup** | SetupWizardView.vue (first-run wizard outside the app shell — no sidebar/header/ticker/chat; guarded by `router/setupGuard.ts`, §69) |
| `/:pathMatch(.*)*` | NotFound | NotFoundView.vue |

### Views without routes
| View | Usage |
|---|---|
| `IssueDetailView.vue` | Embedded slide-in in ListView, KanbanView, GraphView |

### Composables (`src/composables/`)
`useToast`, `usePresence`, `useMockStream`, `useKeyboardShortcuts`, `useExport`, `useAgentStream`, `useSoundEffects`, `useAuthGuard` (route RBAC, §64), `useFocusTrap` (modal a11y, §20)

### Scripts
| Script | Command |
|---|---|
| Dev server | `npm run dev` (frontend/) |
| Typecheck + build | `npm run build` → `vue-tsc -b && vite build` |
| Preview build | `npm run preview` |
| OpenAPI types | `npm run generate-types` (needs live API) |

---

## 50. Known Gaps & Missing Features

### Not Implemented
- Real backend integration is opt-in only (mock mode is the default; toggle via UserMenu → Data Source → Real switches REST calls to `/api/v1`, not all endpoints verified against the real API)
- Transport is mixed: chat uses a real WebSocket (Socket.IO, #538/#540) while everything else stays SSE over HTTP (agent-logs, presence, issues, github-sync, MCP tool-calls) or mock-driven; no generic WebSocket layer for the rest of the app
- OAuth2/SSO login requires `GITHUB_*`/`GOOGLE_*` client env vars on the server (API-key login works out of the box); refresh token lives in localStorage (not an httpOnly cookie)
- No real multi-user concurrent editing
- No actual PII remediation (masking UI only)
- No real code graph extraction (mock data only)
- No real FinOps billing data
- No real agent replay recording
- No real executive KPI calculations
- MCP tool re-run is limited to local executors (`rag_search`, `rag_stats`); other registered MCP servers are catalogued but their calls are not proxied (the built-in graph MCP server itself runs in-process at `/mcp` + stdio since #535)
- No HITL backend workflow
- No real audit trail persistence
- No Storybook / component documentation
- No performance monitoring / Lighthouse
- No service worker / offline support (offline queue is localStorage + flush, no SW)
- No internationalization for right-to-left languages
- No mobile bottom navigation bar (hamburger drawer only)
- No real governance rule engine backend
- No real sync queue persistence (server side)
- `organizationsApi` is hardcoded to `/mock-api` — organization data is not available on the real backend
- Solution embedding features (`/ai/search-similar-solutions`, `/ai/backfill-embeddings`, embed-on-close) require `OPENAI_API_KEY` — without it closes still succeed (logged skip) and search/backfill return empty results
- `GET /sync-queue` does not exist on the real backend (`systemApi` silently falls back to defaults)
- Header page title map omits `/profile` (falls back to dashboard title)
- `data-pipeline` project selectable but has zero mock issues

---

## 51. Organization Multi-Tenancy & Enterprise Settings

Issue #509 (`OrganizationSettingsView.vue`, `OrganizationSwitcher.vue`, `organizationsStore`, `organizationsApi`, `types/organizations.ts`).

| Feature | Status | Details |
|---|---|---|
| **Organization switcher** | Implemented | `OrganizationSwitcher.vue` in AppHeader (`hidden lg:flex`, before ProjectSelector); hierarchical dropdown Organization → Workspace; active org/workspace highlighted; "Manage organization settings" link |
| **Multilevel mock data** | Implemented | `dataset-de-pruebas/organizations.json`: SocialSeed Corp (ENTERPRISE, 3 workspaces, 4 accounts), Northwind Labs (BUSINESS, 2 workspaces), Acme Startup (STARTUP, 1 workspace); each workspace has department, description, members, activeIssues, projectIds |
| **Enterprise roles** | Implemented | `ENTERPRISE_ADMIN`, `SECURITY_MANAGER`, `DEVELOPER`, `AUDITOR`; role selector in settings view; roles stored per org default + `activeEnterpriseRole` in localStorage |
| **Role-based UI gating** | Implemented | `canEdit` false for AUDITOR (retention form disabled, read-only hint); `canManage` only for ENTERPRISE_ADMIN / SECURITY_MANAGER (add/remove member buttons disabled otherwise) |
| **Account CRUD** | Implemented | Table of members with name/email/role chips; inline add form; delete; persisted via `upsertAccount`/`removeAccount` (mock) |
| **Quota cards** | Implemented | Compute / Storage / Token usage vs limit with percentage and color-coded progress bar (green <70%, amber ≥70%, red ≥90%); `quotaUsage` computed in store |
| **Data retention policy** | Implemented | Editable retention days (7–3650), auto-delete and export-before-delete toggles; PATCH to mock API; toast on save |
| **Workspace grid** | Implemented | Selectable workspace cards showing department, members, active issues; active workspace highlighted |
| **Persistence** | Implemented | `currentOrg`, `currentWorkspace`, `activeEnterpriseRole` in localStorage; survives reloads |
| **Issue filtering integration** | Implemented | Workspace → `uiStore.setProject(workspace.projectIds[0])` when current project not in workspace, so `issuesStore.filteredIssues` follows org context |
| **Mock API** | Implemented | `GET/POST /mock/organizations`, `GET/PATCH/DELETE /mock/organizations/{id}` in `mock-api/server.py`; dataset persisted to `organizations.json` |
| **Nav integration** | Implemented | `/organization` in Sidebar + MobileDrawer (Management group); header title `header.organization` |
| **Empty/loading states** | Implemented | Loading spinner, "No organizations available", switcher falls back to first org |
| **i18n** | Implemented | `organizations.*` section + `nav.organization` + `header.organization` in EN/ES |

---

## 52. Governance Matrix, RBAC & Approval Queue

Issue #510 (`GovernanceMatrixView.vue`, `PendingApprovalsQueue.vue`, `governanceStore`, `types/governance.ts`).

| Feature | Status | Details |
|---|---|---|
| **Permission matrix** | Implemented | Actions (Write Code, Push to PR, Modify DB, Delete Resource, Deploy, Config Change, External API) x agent types (Coding, Deploy, Data, Ops) with risk-level tabs (Low/Medium/High/Critical); click cycles cell state Auto -> Approval -> Blocked; color-coded cells + legend |
| **Persistence** | Implemented | Matrix serialized to localStorage (`governance-matrix-v1`), survives reloads; "Reset to defaults" restores seeded policy (e.g. Push to PR requires approval, Delete Resource blocked at High/Critical) |
| **Restricted action simulator** | Implemented | Form (agent type, risk, action, optional linked issue); evaluates matrix: `approval` creates a live alert and pauses execution via `issuesStore.updateIssue({ agent_working:false })`; `blocked` auto-rejects; `auto` auto-approves |
| **Live alerts** | Implemented | Amber banner on GovernanceMatrixView with Approve & resume / Reject & keep halted; resume sets `agent_working:true`; toast + notification (`category: hitl`, `requiresAction: true`) via `notificationsStore` |
| **Pending Approvals Queue** | Implemented | `components/governance/PendingApprovalsQueue.vue`: `hitlStore.pendingRequests` list + detail (agent metadata, impact tiles totalAffected/directDeps/riskLevel, inline `DiffViewer` per diff) |
| **Approval actions** | Implemented | Approve / Request Changes / Reject with required feedback; `hitlStore.resolveAction` + issue status update (approve/modify -> IN_PROGRESS, reject -> OPEN), same contract as #507 `HITLQuickActionModal`; toast + `requiresAction:false` notification |
| **Nav & routing** | Implemented | `/governance-matrix` route (name `GovernanceMatrix`), Sidebar + MobileDrawer Management entries, header title `header.governanceMatrix` |
| **i18n** | Implemented | `governanceMatrix.*` section (states, risk, agents, actions, alert, queue) + `nav`/`header` keys in EN/ES |
| **GovernanceValidationModal** | Unchanged | Existing close-issue validation (#501) untouched; matrix is additive |

---

## 53. Audit Log, Compliance & PII Redaction Suite

Issue #512 (`AuditLogView.vue`, `AuditLogTable.vue`, `PIIRedactionPreview.vue`, `auditLogStore`, `types/auditLog.ts`).

| Feature | Status | Details |
|---|---|---|
| **Audit console** | Implemented | `/audit-log` route (name `AuditLog`), Sidebar + MobileDrawer Management entries; distinct from per-issue `AuditTrail` |
| **Mock entries** | Implemented | 84 deterministic seeded events (seed 20260924) over last 30 days: status change, HITL decision, policy violation, agent run, login, export, governance override, PII redaction; human/agent/system actors, resources, IPs |
| **Filters** | Implemented | Date range (from/to), user, agent, event type, severity + free-text search; combinable; severity counter chips double as quick filters |
| **Pagination** | Implemented | 15 rows/page, prev/next, page indicator, "showing X of Y" |
| **CSV / JSON export** | Implemented | `useExport().exportCSV/exportJSON` over filtered rows |
| **Corporate PDF** | Implemented | html2canvas + jspdf (dynamic import, same pattern as Executive Dashboard) over `#audit-log-report` |
| **Integrity chain** | Implemented | Mock hash-chain blocks (12 events/block) with FNV-style hashes, previous-hash links, "Verified" badge; last 6 blocks shown |
| **Severity counters** | Implemented | LOW/MEDIUM/HIGH/CRITICAL tiles with counts, click to toggle severity filter |
| **PII suite** | Implemented | `PIIRedactionPreview`: live `detectPII` detections (emails, credit cards, tokens, API keys, phones, JWT, passwords...), Mask PII toggle, before/after preview, Mask (applies masking) / Reveal (mock notice) actions |
| **Agent log integration** | Implemented | `AgentLogStream` Mask PII toggle: masked content per line + per-line detection count badge |
| **Issue description integration** | Implemented | `RichTextEditor` shield toggle renders compact `PIIRedactionPreview` under the editor (live masking of the draft) |
| **Nav & header** | Implemented | `nav.auditLog` (EN/ES) |
| **i18n** | Implemented | `auditLog.*` + `piiSuite.*` sections in EN/ES |

---

## 54. Agent Studio (Mock Agent Simulator & Custom Agent Builder)

Issue #513 (`AgentStudioView.vue`, `AgentPromptEditor.vue`, `AgentSandboxTester.vue`, `AgentLibrary.vue`, `agentStudioStore`, `types/agentStudio.ts`, `utils/studioAgents.ts`).

| Feature | Status | Details |
|---|---|---|
| **Agent Builder** | Implemented | `AgentStudioView` at `/agents/studio` (name, role, avatar, base model chips GPT-4o / Claude 3.5 Sonnet / Llama 3 / Gemini 1.5 Pro / Mistral Large, system prompt, 9 tool checkboxes, operative limits) |
| **Prompt editor** | Implemented | `AgentPromptEditor`: variable chips (`{{issue}}`, `{{component}}`, `{{project}}`, `{{constraints}}`), char counter, live validation (required, min 80 chars, >2000, tools not referenced, missing must/never/only rules) |
| **Operative limits** | Implemented | `AgentLimits`: maxTokensPerRun (2k–32k), timeoutSeconds (30–300), maxRisk (LOW/MEDIUM/HIGH) stored on profile |
| **Sandbox Tester** | Implemented | `AgentSandboxTester`: mock chat with deterministic replies seeded by message hash (analyze/plan/report variants), staggered action log (`plan` → `tool X() ok` → `reply via model`), guardrail: `maxRisk=LOW` refuses high-risk keywords (delete/deploy/drop/destroy/prod) |
| **Prompt validation feedback** | Implemented | Editor issues block/warn/info under the textarea; Save disabled until name + prompt non-empty |
| **Corporate library** | Implemented | `AgentLibrary`: cards with avatar, role, model, ACTIVE/INACTIVE badge + toggle switch, tool chips, tokens/timeout/risk tiles, last-used date, Edit / Clone / Delete; empty state |
| **Persistence** | Implemented | localStorage `agent-studio-v1` via `agentStudioStore` (mock persistence per AC); seed library with 2 example agents on first load; `users.json` and `server.py` untouched |
| **usersStore integration** | Implemented | `utils/studioAgents.ts` `mergeStudioAgents` injected in `usersApi.fetchUsers` so studio agents (id prefix `agent-studio-`) survive the full array replacement on refetch and appear in `UsersView` cards and issue assignee dropdowns; store also syncs on every persist |
| **UsersView access** | Implemented | "Agent Studio" secondary button next to "New user" → `router.push('/agents/studio')` |
| **Nav & routing** | Implemented | Route `/agents/studio` (name `AgentStudio`); Sidebar + MobileDrawer Management entries; header title `agentStudio.title` |
| **i18n** | Implemented | `agentStudio.*` section (builder, prompt, sandbox, library) + `nav.agentStudio` in EN/ES |
| **Build** | Implemented | `npm run build` passes (`vue-tsc -b && vite build`, ~42s) |

---

## 55. Custom Dashboards, Reporting Engine & SLA Metrics

Issue #514 (`AnalyticsDashboardView.vue`, `MTTRComparisonChart.vue`, `HealingSuccessChart.vue`, `BudgetByProjectChart.vue`, `SLAMetricsCard.vue`, `ReportExporter.vue`, `analyticsReportStore`, `types/analytics.ts`).

| Feature | Status | Details |
|---|---|---|
| **Analytics view** | Implemented | `/analytics` route (name `Analytics`), Sidebar + MobileDrawer Analysis group (3rd item), header title `analytics.title` |
| **MTTR before vs after agents** | Implemented | `MTTRComparisonChart`: SVG grouped bars per week (gray = pre-agents baseline seeded per period, blue = actual MTTR from closed issues or seeded agent factor), legend, hover tooltips, avg improvement footer; 6 weekly buckets ending at range `to` |
| **Auto-healing success rate** | Implemented | `HealingSuccessChart`: SVG line over 6 weeks with 85% target line; current data from `autoHealingStore.runs` (completed/failed), seeded improving history otherwise; overall badge uses real runs (1 completed / 1 failed = 50%) with seeded fallback |
| **USD budget by project** | Implemented | `BudgetByProjectChart`: horizontal progress bars per project (SocialSeed Tasker $150, Auth Service $90, API Gateway $120, Data Pipeline $80 budgets); spend = seeded base + `finopsStore.tasks` costs joined via `issuesStore` `project_id`, scaled by range days; green/amber/red thresholds 70/90% |
| **Date range + comparison** | Implemented | Presets 7d/30d/90d + custom from/to inputs; period-to-period strip: resolved count and MTTR current vs previous equal-length window with delta % |
| **KPI tiles** | Implemented | MTTR (+ improvement % vs pre-agents), healing rate, budget spent/limit, SLA compliance; color tones good/warn/bad |
| **SLA control panel** | Implemented | `SLAMetricsCard`: mock SLAs CRITICAL 4h / HIGH 24h / MEDIUM 72h / LOW 168h (`SLA_HOURS`); counters On track / At risk / Breached, per-issue time-gap bars (percentUsed), priority chips, hours-left/overdue labels, breach-risk banner |
| **Breach-risk notifications** | Implemented | Auto `notificationsStore.addNotification` once per session (category `constraint_violation`, `requiresAction`, linkTo Analytics) when breaches/risks exist; manual "Notify team" button re-sends + toast |
| **Report generator** | Implemented | `ReportExporter`: Weekly/Monthly buttons build `ExecutiveReport` (5 KPIs + exceptions: SLA breaches/risks, budget ≥85%, failed healing runs); interactive preview `#analytics-report` with KPI cards and exceptions table |
| **Report download** | Implemented | PDF (html2canvas + jspdf dynamic import, portrait A4), PNG (html2canvas), JSON (`useExport().exportJSON`) over the preview panel |
| **Store consistency** | Implemented | `analyticsReportStore` derives from `issuesStore` + `finopsStore` + `autoHealingStore` (no duplicated mock datasets); seeded FNV fallbacks only where source stores lack history; no backend calls |
| **i18n** | Implemented | `analytics.*` (43 keys) + `sla.*` (16 keys) + `nav.analytics` in EN/ES |
| **Build** | Implemented | `npm run build` passes (`vue-tsc -b && vite build`, ~41s) |


---

## 56. Offline First & Mock Sync Queue

Issue #515 (`utils/offlineQueue.ts`, `components/sync/NetworkModeToggle.vue`, `components/sync/SyncQueueDrawer.vue`).

| Feature | Status | Details |
|---|---|---|
| **Network mode simulator** | Implemented | `NetworkModeToggle` segmented Online / Degraded / Offline in AppHeader (`xl+`), status dots (green/amber/red); `uiStore.networkMode` persisted in localStorage `networkMode` |
| **Connection state** | Implemented | `ConnectionState` extended with `DEGRADED`; badge shows SYNCED / OFFLINE_QUEUED / SYNCING / DEGRADED / Offline with amber override when offline+empty |
| **Offline CRUD** | Implemented | Offline mode: `issuesStore.createIssue`/`updateIssue` and `policiesStore.createPolicy`/`updatePolicy` apply changes locally (optimistic, `local-*` ids) and enqueue instead of calling the API; online path unchanged |
| **Queue persistence** | Implemented | `utils/offlineQueue.ts`: `QueuedMutation` entries (entity, operation, entityId, payload, timestamp, retries, status) stored in localStorage `socialseed-offline-queue`; restored on reload, auto-flushed when mode is online |
| **Conflict simulation** | Implemented | Update entries created in Degraded mode (or duplicate updates for the same entity) get `status=conflict` plus a deterministic `remotePayload` (`simulateRemoteVersion` drifts priority/status/is_active/title/name/level) |
| **Reconnect flush** | Implemented | `setNetworkMode('online')` → `flushQueue()` drives badge OFFLINE_QUEUED → (400ms) → SYNCING → (900ms) → SYNCED, keeping conflicted entries queued; "Force sync" button runs the same flush |
| **SyncQueueDrawer** | Implemented | Right overlay opened from `SyncStatusBadge`: queue count chip, per-entry entity/operation/summary/timestamp/retries chips, Retry + Delete on pending, Keep local / Keep remote / Merge (JSON textarea) on conflicts, force sync toolbar, empty state |
| **Resolution application** | Implemented | Keep remote / Merge apply the payload through `updateIssue`/`updatePolicy` with `skipOfflineQueue` (no re-enqueue); Keep local just drops the entry |
| **simulateSync guard** | Implemented | `simulateSync()` no-ops when offline, queue non-empty, or already SYNCING so manual sync simulation never clobbers pending mutations |
| **Reload survival** | Implemented | Queue + network mode restored from localStorage at store init; pending queue flips badge to OFFLINE_QUEUED on load |
| **i18n** | Implemented | `offline.*` (7 keys) + `syncQueue.*` (20 keys) in EN/ES |
| **Build** | Implemented | `npm run build` passes (`vue-tsc -b && vite build`, ~43s) |


---

## 57. Sound Effects, Notification Center Groups & Toast Themes

Issue #516 (`composables/useSoundEffects.ts`, `components/ui/ToastThemeSettings.vue`, `NotificationCenter.vue` evolucionado).

| Feature | Status | Details |
|---|---|---|
| **Sound engine** | Implemented | `useSoundEffects`: Web Audio API oscillators (no binary assets), `playAlert` (descending square-wave buzzer), `playSuccess` (4-note ascending arpeggio), `playPing` (double sine chime); lazy `AudioContext` with resume-on-play |
| **No autoplay** | Implemented | Sounds only after first user gesture (`pointerdown`/`keydown` listener, removed on first interaction); silent if disabled, volume 0, or no audio device |
| **Sound preferences** | Implemented | On/off + volume 0-100 persisted (`sound-effects-enabled`, `sound-effects-volume`); toggle, slider, and test button in UserMenu → Alerts section |
| **Event triggers** | Implemented | Kill Switch (`IssueCard.killAgent` → alert), auto-healing success (`autoHealingStore.simulateCompletion` → success arpeggio + completion log; "Simulate pipeline success" button in AutoHealingMonitorView), notifications via `playForCategory` (violation/agent-failure/SLA → alert, HITL/mention → ping) |
| **Per-channel sound prefs** | Implemented | `notificationsStore.preferences.channels` persisted (`socialseed-alert-prefs`); `addNotification` plays sound only if channel enabled (mentions off by default); seeds/HITL bulk inserts bypass sound |
| **Criticality groups** | Implemented | NotificationCenter groups filtered history: Emergency (constraint_violation, agent_failure, sla) → Warning (hitl) → Info (mention) with sticky colored headers and counts (`SEVERITY_GROUPS` in `types/notifications.ts`) |
| **Channel filter** | Implemented | Chip row: All / HITL / Governance / Agent / SLA / Mentions stacked with existing all/unread/action tabs |
| **Bulk group actions** | Implemented | "Mark read" per group, "Clear all" (respects active filters) via `markManyRead` / `dismissMany` |
| **Inline detail on click (#553)** | Implemented | Clicking a non-HITL row toggles the full message inline (`truncate` → `whitespace-pre-wrap break-words`), marks it read and reveals a full timestamp + **Open** button (`notifItem.open` EN/ES) that navigates to `linkTo` — one expanded row per list, reset on panel close/dismiss; wired in `NotificationItem` (bell panel, now navigating only via the button) and in `NotificationsFeed` (board feed gains its first click handler); HITL rows keep opening `HITLQuickActionModal` |
| **SLA category** | Implemented | New `NotificationCategory = 'sla'` + `CATEGORY_CONFIG` (rose timer icon) + `unreadByCategory`; AnalyticsDashboardView breach notification migrated from `constraint_violation` to `sla` |
| **Toast themes** | Implemented | `uiStore.toastTheme` minimal / rich / enterprise persisted (`toast-theme`); ToastItem: minimal = flat gray border/icon, rich = current type-colored, enterprise = top color strip + left border + mono type label |
| **Theme picker** | Implemented | `ToastThemeSettings` with 3 mini previews, mounted in UserMenu under Alerts |
| **i18n** | Implemented | `soundEffects.*` (4 keys) + `toastTheme.*` (8 keys) + `notifPanel.*` (11 keys) + `autoHealing.simulateSuccess` in EN/ES |
| **Build** | Implemented | `npm run build` passes (`vue-tsc -b && vite build`, ~43s) |

---

## 58. Under-Construction Indicators (pending features, mock and real)

Visual indicator that a feature is still backed only by mock/local data. The badge renders in **both** data-source modes: in mock mode it marks the view as demo-only, and when the app consumes the real REST backend (§62) it warns that the view still does not talk to the API. On the real API the page header additionally renders a visible "Under construction" text chip.

| Feature | Status | Details |
|---|---|---|
| **Pending route registry** | Implemented | `utils/pendingFeatures.ts`: `PENDING_FEATURE_ROUTES` (21 routes) + `isPendingFeature(path)` (no data-source gate) + `isRealPendingFeature(path)` (pending **and** real mode, used by the header chip); covers the mock-backed sidebar routes; `/profile` (local-only) and NotFound excluded |
| **Badge component** | Implemented | `components/ui/PendingDevBadge.vue`: amber hourglass SVG in a tinted pill (dark-mode aware), sizes `xs` (16px) / `sm` (20px), `role="img"` with `title` + `aria-label` tooltip |
| **Sidebar nav** | Implemented | `NavItem.vue`: `pending` prop renders the badge overlaid at the icon's top-right corner (visible in both collapsed w-20 and expanded w-64 states) |
| **Mobile drawer** | Implemented | `MobileDrawer.vue` passes `:pending="isPendingFeature(item.path)"` (mobile parity with desktop sidebar) |
| **Page header badge** | Implemented | `AppHeader.vue`: badge rendered right after `pageTitle` when `isPendingFeature(route.path)` (mock and real modes) |
| **Under-construction chip (real mode)** | Implemented | `AppHeader.vue`: amber text chip `common.underConstruction` ("Under construction" / "En construccion") next to the title when `isRealPendingFeature(route.path)`; `role="status"`; hidden in mock mode where the icon badge already communicates the state |
| **Stable sidebar** | Implemented | Nav is not filtered by data source: the same 3 groups / 24 items render in mock and real modes (RBAC filtering removed from `Sidebar.vue`; route-level protection stays in the router guard, §64) — no items appear/disappear when toggling modes |
| **i18n** | Implemented | `common.pendingDev`: "Feature awaiting development" / "Funcionalidad pendiente de desarrollo"; `common.underConstruction`: "Under construction" / "En construccion" (ASCII); `nav.finops`/`nav.autoHealing`/`nav.replay`/`nav.executive`/`nav.graph` and `header.graph` were missing and are now translated in both locales |
| **Tests** | Implemented | `utils/pendingFeatures.spec.ts` (4 tests) + `components/layout/Sidebar.spec.ts` (5 tests, stable 24 items/3 groups + `nav.*` i18n); suite 167/167 (22 files) |
| **Build** | Implemented | `npm run build` passes (`vue-tsc -b && vite build`); `tasker-board` image rebuilt and verified serving the new strings |

---

## 59. Agent-Working Indicator in Kanban & Issue List

Shared `AgentWorkingIcon` showing which issues currently have an agent working on them.

| Feature | Status | Details |
|---|---|---|
| **Shared component** | Implemented | `components/ui/AgentWorkingIcon.vue`: pulsing cyan robot icon (same glyph as IssueDetailView header) + `role="status"`, tooltip/aria `issues.aiAgentActive` + live elapsed ("Agente IA Activo · 12m 30s") |
| **Live timer** | Implemented | Per-instance 1s interval started on mount and watched on `agent_working`/`agent_working_started_at` changes; cleared on unmount |
| **IssueCard (Kanban + Board)** | Implemented | Indicator block now renders `AgentWorkingIcon show-timer` + existing kill-switch button; timer logic removed from IssueCard (single source in the component) |
| **Issue List** | Implemented | `ListView` title cell: icon inline before the title (flex + truncate preserved), shown only when `issue.agent_working` |
| **Data source** | Existing | `Issue.agent_working` / `agent_working_started_at` (5 of 100 mock issues seeded active); toggled by governance alerts and the kill switch |
| **Build** | Implemented | `npm run build` passes (`vue-tsc -b && vite build`, ~63s) |

---

## 60. Dashboard Information Modules (Board)

Expanded `/board` (Dashboard) from 6 to 16 modules: added an operational pulse row and two insight/operations rows fed by existing stores.

| Module | Status | Details |
|---|---|---|
| **DashboardPulse** | Implemented | 4 `StatsCard`s: Agents Working (issues `agent_working` + `usersStore.activeAgents`, fetch-on-empty), HITL Approvals (`pendingCount` / urgent subtitle), SLA At Risk (open issues vs `SLA_HOURS`: breached >100%, at-risk >80%; subtitle = breached count), Notifications (`unreadCount` + emergency-group unread subtitle) |
| **PriorityBreakdown** | Implemented | Horizontal bars per priority (CRITICAL red / HIGH orange / MEDIUM blue / LOW gray, matching PriorityBadge) over open issues, count + relative width |
| **ComponentWorkload** | Implemented | Top 5 components by open-issue count (brand-colored bars, name via `componentsStore`, fetch-on-empty) |
| **NotificationsFeed** | Implemented | Latest 4 notifications sorted desc: category chip (CATEGORY_CONFIG glyph + tinted bg), title/message, HH:MM timestamp; unread count chip in card action slot |
| **AutoHealingMini** | Implemented | Running/completed/failed counters from `autoHealingStore.runs` + live running-stage row (i18n `autoHealing.stages.*`, pulsing dot, run id) |
| **SyncStatusCard** | Implemented | `uiStore.pendingSyncCount` + network mode chip (online green / degraded amber / offline red) + `connectionState` label |
| **BudgetMini** | Implemented | `finopsStore.metrics.totalCost` (red if critical alerts) + budget alert chip (critical+warning) or "Sin alertas" |
| **ModuleCard shell** | Implemented | Shared `components/dashboard/ModuleCard.vue` (title + action slot) for the 6 card modules |
| **i18n** | Implemented | `boardModules.*` (24 keys) EN/ES |
| **Build** | Implemented | `npm run build` passes (`vue-tsc -b && vite build`, ~79s) |

## 61. Dashboard Section Layout & Advanced Analytics Modules (Board)

Reorganized `/board` (Dashboard) into six labeled sections with hairline headers and expanded it from 16 to 25 modules.

| Module | Status | Details |
|---|---|---|
| **SectionHeader** | Implemented | Uppercase tracking-wide label + hairline rule; six sections: Overview, Analytics, Issue Insights, Team & Quality, Ecosystem, Operations (`boardSections.*` EN/ES) |
| **ActivityHeatmap** | Implemented | GitHub-style 13-week x 7-day heatmap of created+closed events per day, 5-level brand-green scale, month/weekday labels, localized per-day tooltip, Less/More legend, total-events chip |
| **IssueAging** | Implemented | Age buckets for open issues (0-3 green / 4-7 amber / 8-14 orange / 15+ red) + avg-age and oldest-open footer stats |
| **PriorityMatrix** | Implemented | Priority x Status grid (4 priorities x 5 statuses incl. new WAITING_HUMAN_APPROVAL column) with per-cell count and rgba intensity fill by priority color |
| **LabelCloud** | Implemented | Top 18 labels by frequency, font size scaled 11-24px, rotating color palette, count per label, unique-label footer |
| **TeamWorkload** | Implemented | Top 6 assignees by open issues: avatar, username, Human/AI badge, open/total counter, relative bar (green agents / blue humans), footer humans+agents counts and unassigned chip; fetches users on empty |
| **DependencyRisk** | Implemented | Top 5 most-depended-upon issues (mono id chip + title + xN dependents badge tinted by fan-in) + footer dependency-edge and blocked counts |
| **GovernanceCompliance** | Implemented | SVG compliance ring (compliant = no violations + solution summary + file impact) with 80/60 color thresholds + counters for violations, missing summaries, missing file impact |
| **GitHubSyncHealth** | Implemented | Stacked SYNCED/PENDING/ERROR bar with % synced, per-status legend rows (`githubSync.status.*`), last-synced footer |
| **AuditFeed** | Implemented | Latest 6 `auditLogStore` entries in a two-column list: severity dot + label, localized event type, actor/resource, relative timestamp; critical-count chip and "View all" RouterLink to `/audit-log` |
| **i18n** | Implemented | `boardSections.*` (6 keys), `boardModules.*` +30 keys, `statusDistribution.waitingApproval` EN/ES |
| **Build** | Implemented | `npm run build` passes (`vue-tsc -b && vite build`, ~59s); BoardView chunk 34.7 -> 57.1 kB; Docker `tasker-board` rebuilt and verified serving `index-PgBU1Crg.js` with the new i18n keys |

---

## 62. Backend Integration & Live SSE Architecture (mock/real toggle)

Issue #517. First real backend integration: an app-wide mock/real data-source toggle plus genuine SSE transport for agent logs and presence (replacing mock-only simulation from §47 when Real mode is active).

| Feature | Status | Details |
|---|---|---|
| **Data-source toggle (mock/real)** | Implemented | `apiMode` ref lives in `frontend/src/api/client.ts` (resolution order: `localStorage['socialseed-api-mode']` > `VITE_USE_MOCK` > default `mock`); `isMockMode()`/`setApiMode()` helpers; the exported axios wrapper `client` dispatches every call to `mockClient` (in-bundle `mockApi.ts`) or `realClient` (axios → `/api/v1`) via a reactive proxy; selector segmented Mock/Real in `UserMenu` (Data Source section, `data-testid="api-mode-mock|real"`); `uiStore.apiMode/isMockApi/setApiMode` facade; `authStore` and `LoginScreen` use `isMockMode()` |
| **First-entry mode probe** | Implemented | `api/modeBootstrap.ts` runs from `router.beforeEach` **before** `initSession()`: a fresh browser (no stored mode, still defaulting to mock) probes `GET {API_URL}/health` once (2.5s timeout, endpoint exempt from the API-key middleware) and persists `real` when it answers, so an installed deployment lands on real data instead of the mock 5-HITL demo; only success is stored (no backend → mock kept, retried next load) and an explicit stored choice or an already-real mode is never probed (#552) |
| **Realtime SSE client** | Implemented | `frontend/src/api/realtime.ts`: `connectSSE(path, handlers)` on native `EventSource` with exponential backoff + jitter (max 8 attempts), 45s watchdog (forced reconnect if no event/heartbeat), aggregated reactive `realtimeState` (`live/connecting/reconnecting/offline/idle`) exposed via `useRealtimeStatus()`; reads `API_URL` (same-origin `/api/v1` or `VITE_API_URL`) |
| **Agent-log stream** | Implemented | `useAgentStream` connects to `/api/v1/issues/{id}/agent-logs/stream` in Real mode (never in mock), maps stream state → `ConnectionStatus`, reconnects on `issue.id` change; `IssueDetailView` merges REST list + SSE events into `displayLogs` with dedupe by `id` (and `timestamp|content_markdown`) |
| **Presence (real)** | Implemented | `usePresence` in Real mode: `POST /presence` on join, 30s heartbeat, `POST /presence/leave` on unmount, `GET /presence/stream` for live viewer updates with `currentField` tracking; mock keeps the previous in-memory behavior; `watch(apiMode)` resets local state when switching back to mock |
| **Backend SSE hub** | Implemented | `src/.../web_api/routers/realtime.py`: `RealtimeHub` (per-issue log ring buffer of 200 entries, presence registry with 90s TTL, asyncio pub/sub); registered in `routers/__init__.py`, `routes.py` and `app.py` (`prefix=/api/v1`, `app.state.realtime_hub`); endpoints `GET/POST /issues/{id}/agent-logs`, `GET /issues/{id}/agent-logs/stream`, `GET/POST /issues/{id}/presence`, `POST /issues/{id}/presence/leave`, `GET /issues/{id}/presence/stream` |
| **SSE protocol** | Implemented | Streams send `event: connected` (+ replay payload) atomically before subscribing to live traffic, then `event: log` / `event: viewers`, with a named `event: ping` heartbeat every 15s (named event so the client watchdog never treats it as silence); `X-Accel-Buffering: no` header |
| **nginx streaming** | Implemented | `frontend/nginx.conf` `/api/` location: `proxy_buffering off`, `proxy_cache off`, `chunked_transfer_encoding on`, `proxy_read_timeout 3600s`, `X-Accel-Buffering no` — EventSource cannot send headers, so auth relies on the existing nginx-injected `X-API-Key` |
| **SyncStatusBadge states** | Implemented | Badge shows `sourceLabel` + `sourceLabelClass`: `Mock` (purple) / `Live` (green) / `Connecting` (blue) / `Reconnecting` (amber) / `Stream offline` (red); `data-testid="api-source-chip"`; pending-queue count chip renders whenever `pendingSyncCount > 0` (both modes, no data-source gate) |
| **i18n** | Implemented | `sync.{mock,live,connecting,reconnecting,streamOffline}` + `apiMode.{title,hint,mock,real}` EN/ES |
| **Env & docs** | Implemented | `frontend/.env.example` documents `VITE_USE_MOCK`, `VITE_API_URL` and the SSE endpoints |
| **Verification** | Implemented | `npm run build` green (`vue-tsc -b && vite build`); `ruff check realtime.py` clean (remaining `app.py` findings pre-exist at HEAD); Docker `tasker-api`+`tasker-board` rebuilt — smoke: SSE `connected`+replay (`replayed:1`), live delivery while subscribed, `ping` at 15s, presence join/list/stream-broadcast/leave all through nginx `:19001`, mock-api `:8001` intact, UI serving new bundle `index-BSCi2qGL.js` |


---

## 63. Test Suite, Linting & Frontend CI/CD

Issue #518. First quality gate for the frontend: unit tests, E2E tests, a linter and a dedicated GitHub Actions workflow (previously the only verification was `npm run build` and CI only covered the Python backend).

| Feature | Status | Details |
|---|---|---|
| **Vitest + Vue Test Utils** | Implemented | `frontend/vitest.config.ts` (merge de `vite.config.ts`, entorno jsdom, setup global, coverage v8); `src/test/setup.ts` (polyfills `matchMedia`/`ResizeObserver`/`scrollIntoView`, `localStorage.clear()` por test); `src/test/mount.ts` (`mountComponent` con Pinia + i18n singletons + stubs `RouterLink`/`Teleport`, montado en `document.body` con `enableAutoUnmount`); scripts `test`, `test:watch`, `test:coverage` |
| **Unit tests (81)** | Implemented | 9 spec files: stores `issuesStore` (fetch/CRUD/filtros/estados), `uiStore` (filtros, cola offline, apiMode, dark mode), `notificationsStore` (push/dismiss/persistencia/categorías); composables `useKeyboardShortcuts` (registro/alcance/secuencias/limpieza), `useSoundEffects` (AudioContext mock, mute, throttle); componentes `FilterBuilder` (dropdowns/tri-state/chips/clear), `IssueCard` (render/emitidos/kill switch), `ModuleCard`, `SyncQueueDrawer` (vacío/cola/retry/delete/conflictos con `Keep local`/`Keep remote`/`Merge`) |
| **Playwright E2E (8)** | Implemented | `frontend/playwright.config.ts`: `webServer` dual — Vite (`:5173 --host --strictPort`) + mock API (`python -m uvicorn server:app --app-dir ../mock-api`, `DATA_DIR` = copia temporal `.e2e-data/` generada por `scripts/prepare-e2e-data.mjs` vía hook `pretest:e2e`, para no escribir sobre el dataset git-trackeado); `workers: 1` (el mock API lee/escribe JSON sin locks → paralelismo provoca carreras), `retries: 2` en CI, reporter `list` + `html`; specs: `navigation.spec.ts` (redirect `/`→`/board`, sidebar→Kanban, sandbox, 404), `issue-flow.spec.ts` (crear issue → tarjeta → detalle → cerrar, drag & drop Open→Blocked, overview del board), `sandbox.spec.ts` (seleccionar regla → Simulate → `Simulation Result` con edges/violations) |
| **ESLint flat config** | Implemented | `frontend/eslint.config.js` (ESLint 9: `@eslint/js` + `typescript-eslint` recommended + `eslint-plugin-vue` flat/recommended); reglas relajadas según convención del proyecto (`no-explicit-any` off, formato Vue off, `vue/no-mutating-props` en `warn`, `vue/require-toggle-inside-transition` off); scripts `lint`/`lint:fix`; resultado: 0 errores, 2 warnings |
| **GitHub Actions** | Implemented | `.github/workflows/frontend-ci.yml` (workflow separado de `ci.yml`, activado por cambios en `frontend/**`): setup Node 20 con cache npm → `npm ci` → `npm run lint` → `npm run build` (vue-tsc + vite) → `npm test` → setup Python 3.11 + `pip install -r mock-api/requirements.txt` → `npx playwright install --with-deps chromium` → `npm run test:e2e`; sube `playwright-report/` como artifact si falla; los jobs Python de `ci.yml` quedan intactos |
| **Fixes de código** | Implemented | `useMockStream.ts` (`let`→`const` en `tokenCounter`, `default` en el switch de `intervalMs`), `piiDetector.ts` (escapes `\-` innecesarios en el regex de API keys); spacing auto-fixable en `FloatingChat`/`GitHubSyncCard`/`DashboardSystemView`/`IssueDetailView` |
| **i18n** | Not needed | Los tests usan los textos EN existentes (no se añadieron claves) |
| **Verification** | Implemented | `npm run lint` ✓ (0 errores), `npm test` ✓ (81/81), `npm run build` ✓, `npm run test:e2e` ✓ (8/8 en dos corridas consecutivas) |
| **Suite status (2026-09-29)** | Implemented | 167 unit tests / **22 spec files** (los 9 de #518 + `authStore`, `CreateIssueModal`, `GitHubSyncCard`, `KanbanView`, `ListView`, `KeyboardShortcutsHelp`, `MCPInspectorView`, `mcpStore`, `ragStore`, `ruleEngine`, `useFocusTrap`, `pendingFeatures`, `Sidebar`); lint 0 errores (2 warnings preexistentes `vue/no-mutating-props` en IssueDetailView), build verde, E2E 8/8 |
| **Suite status (2026-10-01)** | Implemented | **208 unit tests / 27 spec files** (`npm test` 27/27 verdes), `npm run lint` 0 errores (2 warnings preexistentes `vue/no-mutating-props`), `npm run build` verde (`vue-tsc -b && vite build`); inventario de UI recalado contra el código el 2026-10-01 (#535, §68) |
| **Suite status (2026-10-04)** | Implemented | **270 unit tests / 39 spec files** (`npm test`), `npm run lint` 0 errores (2 warnings preexistentes), `npm run build` verde; inventario de UI recalado contra el código (vistas 29, componentes 101, rutas 27, i18n 78/1680, pendientes 21) — backlog v5 #542–#546 (§69) |

---

## 64. OAuth2/SSO Authentication & Role-Based Route Protection

Issue #519. Real login for the frontend: JWT sessions with rotating refresh tokens, GitHub/Google OAuth2 (PKCE), API-key fallback and role-based protection of routes and actions (the sidebar menu itself stays stable across data-source modes, §58).

| Feature | Status | Details |
|---|---|---|
| **JWT issue & verify (HS256)** | Implemented | `src/socialseed_tasker/auth/tokens.py`, stdlib puro (`hmac`/`hashlib`/`base64`, sin dependencias nuevas): access 900s (`TASKER_JWT_ACCESS_TTL`), refresh 604800s (`TASKER_JWT_REFRESH_TTL`), secret `TASKER_JWT_SECRET`; claims `sub/username/role/permissions/typ/jti` |
| **Refresh rotation + reuse detection** | Implemented | jtis activos en registro in-memory por subject; `POST /auth/refresh` descarta el jti viejo y emite uno nuevo; presentar un refresh ya rotado revoca todos los jtis del subject (fuerza re-login); logout revoca el jti presentado |
| **Role change → re-login** | Implemented | `PUT /users/{id}` (#561): cuando `body.role` cambia efectivamente (rol pre-update ≠ `role_id` nuevo) y `human_user.password_hash` no está vacío, `_revoke_user_sessions` (`routers/user.py`) ejecuta `tokens.revoke_all_for_subject(uid)` (limpia los jtis activos del sub) + `AuthSessionStore.delete_all_for_user(uid)` (SCAN `session:{uid}:*` en Redis / sweep por prefijo en memoria, sin índice secundario); best-effort en try/except — el PUT ya commitado nunca falla por la revocación. El refresh viejo → 401 `Session revoked`, el access viejo cae igual (middleware/`me` consultan la sesión, más estricto que el AC) y el siguiente login emite JWT con el rol actual de PG; sin credencial (#563 pendiente, `password_hash=''`) no hay sesiones de password que revocar. La alternativa no elegida (`rotate()` releyendo PG) queda documentada en la issue |
| **Delete → cascada (raíz)** | Implemented | `DELETE /users/{id}` (#562): el perfil se lee de PG (404 si no existe), el guard de último humano cuenta `SELECT count(*) FROM users WHERE user_type = 'human'` —agentes exentos— ⇒ 409 sin borrar nada, y el `DELETE FROM users` es autoritativo (rowcount ⇒ 404 en carrera, excepción ⇒ 500, sin `TASKER_DATABASE_URL` ⇒ 503, decisión consistente con el resto de `/users`); `human_user`/`agents_user`/`user_skills` caen por FK cascade. Después: revocación incondicional de sesiones del sub (`tokens.revoke_all_for_subject` + `AuthSessionStore.delete_all_for_user`, reutiliza #561, best-effort), proyección Neo4j (solo si hay driver — antes un sin-driver era 503 — y log si falla) y `notifications` de Mongo (`NotificationMongoRepository.clear_all`, async) ambos en try/except que degradan a log sin romper el 200. Frontend: `usersStore.deleteUser` re-lanza el error (`Promise<void>`), `usersApi.deleteUser` mutea el toast genérico (`suppressErrorToast`) y la vista pinta `Error: {detail}` con `common.error` de fallback (#562) |
| **Temporary password** | Implemented | `POST /users` (#563): para humanos genera `secrets.token_urlsafe(12)`, lo hashea con bcrypt (`hash_password`) y lo persiste en `human_user.password_hash` vía `create_human_user(password_hash=…)`; el plaintext se devuelve **una sola vez** en `temporary_password` del 201 — si el body trae `password` explícito se usa ese y no se devuelve temporal; `GET /users*` siempre `null` y en claro no queda nada en PG. Frontend: `usersApi.createUser` devuelve `{ user, temporaryPassword }` (`normalizeBackendUser` ignora el campo, la tarjeta no se contamina), el store no persiste el plaintext y `TemporaryPasswordDialog` la muestra monoespaciada con copiar (Clipboard API) + aviso `users.passwordOnce` + "Entendido" que limpia el estado; agentes sin credencial (sin fila `human_user`, #564) |
| **Agent profiles CRUD** | Implemented | `/agents/profiles` dedicado (#564): `PostgresAgentProfileStore` (`auth/user_store.py`) hace CRUD transaccional sobre `users` + `agents_user` + `user_skills` con uid generado por PG (`user_type='agent'`, sin credencial ni rol RBAC); `tools` se validan contra el catálogo `tools` (422 slug desconocido, escritura no empieza), username duplicado ⇒ 409, sin fila ⇒ 404, sin `TASKER_DATABASE_URL` ⇒ 503; update parcial (`None` = keep, listas presentes reemplazan, skills con reemplazo total) y `delete_profile` con guard `WHERE user_type='agent'` que nunca toca humanos (ellos van por `DELETE /users` #562, y la cascada FK limpia `agents_user`/`user_skills`). El router `routers/agent_profiles.py` se registra en `app.py` **antes** de `agent_router` para que `/agents/profiles` no caiga en `/agents/{agent_id}` (test explícito); `role` siempre `null` (el front deriva `ai-agent`) y `type='agent'`; sin login posible (sin fila `human_user`). La migración de Agent Studio a esta API es #573 |
| **Auth endpoints** | Implemented | `src/.../routers/auth.py` (`/api/v1/auth/`): `POST login` (API key → JWT + user; reutiliza `InMemoryAuthProvider` de `TASKER_AUTH_USERS`/`auth/users.json`; rol derivado de permisos: `admin`→ADMIN, `create/delete:issue`→DEVELOPER, resto VIEWER), `POST refresh`, `POST logout`, `GET me`, `GET oauth/{provider}/authorize` (state + PKCE S256, TTL 600s), `GET oauth/{provider}/callback` (code exchange → perfil GitHub/Google → redirect `TASKER_FRONTEND_URL/auth/oauth-callback?code=` con código one-time 60s; `TASKER_AUTH_ADMIN_EMAILS` promueve a ADMIN), `POST exchange`; sin `GITHUB_*`/`GOOGLE_*` → 403 `oauth_not_configured:{provider}`; desde #527 `POST login` acepta tambien `username`+`password` (bcrypt en PG) |
| **Middleware** | Implemented | `app.py`: salta `/api/v1/auth/*`; `X-API-Key` intacto para CLI/SSE; un `Authorization: Bearer` distinto de la API key se valida como JWT (`verify_access`) → 401 solo si tampoco es JWT válido; `/health` y docs siguen abiertos; tokens con claim `sid` sin sesion en Redis -> 401 (#527) |
| **Session registry (Redis)** | Implemented | `auth/redis_sessions.py`: `AuthSessionStore` persiste sesiones JWT bajo `session:{user_id}:{session_id}` (jti, roles, timestamps, user-agent) con TTL = `REFRESH_TTL` via redis-py; wiring `app.state.auth_sessions` en `app.py`; degrada a dict in-process sin `TASKER_REDIS_URL` o si Redis falla (#527) |
| **Session holder** | Implemented | `frontend/src/api/authSession.ts`: access en RAM, refresh en `localStorage['tasker_refresh_token']`, user en `tasker_session_user`, auto-refresh programado 60s antes de expirar, `clearSession()`; sin imports de axios/Pinia (evita ciclos de módulos) |
| **Auth API client** | Implemented | `frontend/src/api/authApi.ts` (axios propio, sin `X-API-Key`): `login/refresh/logout/me/exchange/startOAuth`, refresh **single-flight** (promesa compartida entre timer e interceptor), `restoreSession(legacyKey)` al arrancar (refresh guardado → API key legada/env); registra el handler de refresh en el holder |
| **authStore RBAC** | Implemented | `stores/authStore.ts` (rewrite): `initSession()` idempotente (mock → usuario demo ADMIN en memoria; real → `restoreSession`), `login`/`loginOAuth`/`completeOAuth`/`logout`, `can(action)`→permiso backend (`issue.create/edit/kill`→`create:issue`, `issue.delete`→`delete:issue`, `hitl.approve`/`user.manage`/`settings.manage`/`admin.reset`→`admin`), `hasRole`/`rolesAllowed` con rango ADMIN≥DEVELOPER≥VIEWER; **en mock `can()` autoriza siempre** (demo auto-auth intacta); `auth:unauthorized` cierra la sesión → shell desmontado y pantalla de login en vista limpia (#557) |
| **Client interceptors** | Implemented | `client.ts`: request añade `Bearer` en modo real (excepto `/auth/`); response 401 → `refresh()` + retry 1× (marcador `__retried`, token nuevo gracias al interceptor de request) → si el refresh falla, limpia sesión y emite `auth:unauthorized`; los errores ≥400 siguen con toast |
| **Route guards** | Implemented | `router.beforeEach`: `await initSession()` + `meta.roles` en `/users`, `/organization`, `/audit-log`, `/constraints` → redirect `/board` con toast `auth.forbidden`; nueva ruta `/auth/oauth-callback` (`AuthCallbackView` completa el intercambio y redirige a `/board`) |
| **Sidebar items (stable)** | Implemented | `Sidebar.vue` **no** filtra ítems: renderiza los 3 grupos / 24 items idénticos en mock y real (el filtro por `canRoute` se retiró para que el menú no cambie al alternar data source); la protección RBAC sigue en `router.beforeEach` (redirect `/board` + toast `auth.forbidden`) y en el gate de acciones |
| **Action gating** | Implemented | `IssueCard` kill switch → `can('issue.kill')`; `HITLCommandCenter` approve/modify/reject → `can('hitl.approve')`; `IssueDetailView` selects de status/priority/assignee → `can('issue.edit')` (con estilo `disabled` visible) |
| **Login screen & menu** | Implemented | `LoginScreen.vue`: modo **credentials por defecto** (inputs usuario/clave → `authStore.loginWithCredentials`, `data-testid="login-username|login-password"`) con conmutador al modo API key (`login-toggle-apikey`/`login-toggle-credentials`, master key #552 intacta), botones GitHub/Google (`data-testid="oauth-github|google"`), párrafo superior y divisor condicionales por modo, busy/error (`data-testid="login-submit|login-error|login-clear"`, submit deshabilitado si faltan campos); errores traducidos desde `detail` del backend (401 key inválida, 403 oauth sin configurar); `UserMenu` muestra username + rol reales (`profile.roles.*`) y `logout()` (revoca refresh en backend + limpia sesión + reload) (#554); **en App.vue el login se renderiza en lugar del shell cuando no hay sesión** — vista totalmente limpia sin sidebar/header/board detrás y sin montar `RouterView`, backdrop sólido `bg-white dark:bg-gray-900` (#557) |
| **i18n** | Implemented | `auth.{github,google,orContinue,invalidKey,loginFailed,oauthError,oauthNotConfigured,forbidden,username,password,enterCredentials,orAccount,useApiKey,useCredentials}` EN/ES (#554 añade las 6 últimas) |
| **Tests** | Implemented | `authStore.spec.ts` (10 tests): auto-auth mock, restore/login/API key legada, permisos de admin/developer/viewer, `rolesAllowed` por ruta, errores traducidos (key inválida + oauth sin configurar), exchange OAuth; `LoginScreen.spec.ts` (5 tests, #554): credentials por defecto, submit deshabilitado, login `admin/admin`, conmutador API key/back, error visible; `App.spec.ts` (3 tests, #557): /setup bare, sin sesión en /board → solo login sin shell, con sesión → shell sin login |
| **Verification** | Implemented | Frontend: `npm test` ✓ (91/91), `npm run lint` ✓ (0 errores/2 warnings preexistentes), `npm run build` ✓ (vue-tsc + vite), `npm run test:e2e` ✓ (8/8). Backend: `ruff`+`mypy` limpios en los ficheros nuevos; `app.py` ruff 34 (baseline 35) y mypy 78 (baseline 79), delta no positivo; smoke `TestClient` 19/19 (middleware 401/200 con API key y Bearer JWT, login admin/viewer, `/auth/me`, rotación de refresh, reuse detection, logout, token adulterado, oauth 403 sin env, `/health` abierto); `pytest -k "not integration"` 1009 passed / 3 failed (las 3 preexistentes en HEAD, verificadas con stash: `test_delivery_retry` + 2 de `workers/test_tasks_unit`) y `tests/api/test_flags_api_unit.py` 8/8 (2 fallos preexistentes corregidos: fixture `TASKER_AUTH_ENABLED=true` + import de `HTTPException` en `_require_admin`) |
| **Docker review** | Implemented | `docker-compose.yml`: `TASKER_AUTH_ENABLED=true`, `TASKER_JWT_SECRET`, `TASKER_FRONTEND_URL`, `TASKER_API_KEY=test-token`; fix `[tool.setuptools.package-data]` `auth/*.json` en `pyproject.toml` (el wheel no incluía `users.json`); `_require_admin` acepta ahora Bearer JWT (claims firmados `role`/`permissions`) además de la API key cruda; 4 contenedores healthy; smoke en :19001: login admin 200/ADMIN/6 perms/900s, login reader 200/VIEWER/2, key mala 401, `/admin/flags` sin Bearer 403 / con JWT admin 200 / con JWT reader 403, refresh rota (token nuevo), whoami con JWT 200 `authenticated=true`, UI sirve bundle nuevo |

---

## 65. Real Persistence & Auto-Healing Pipeline Engine

Issue #520. Backend pipeline executor with real five-stage runs, downloadable `.patch` artifacts, live cancel/restart, and the monitor UI connected to it; the mock experience is preserved untouched.

| Feature | Status | Details |
|---|---|---|
| **Pipeline engine** | Implemented | `src/socialseed_tasker/healing/engine.py`: `AutoHealingEngine` runs the five stages (`test_failure` → `neo4j_root_cause` → `task_generation` → `agent_fix` → `pr_created`) as an asyncio task with `TASKER_HEALING_STAGE_DELAY` (1s default) between stages so cancellation is observable live; runs marked `running` at boot are failed with `Interrupted by API restart`; stage logs carry `test`/`system`/`agent` sources |
| **Real stage work** | Implemented | Stage 1 looks the anchor issue up in Neo4j (honest failure if missing); stage 2 runs `RootCauseAnalyzer.find_root_cause(TestFailure, closed_issues)`; stage 3 calls `create_issue_action` (title dedupe makes restarts idempotent); stage 4 applies one of three real strategies (`remove_debug_statements` / `strip_trailing_whitespace` / `ensure_trailing_newline`, chosen by issue keywords) to a seeded sandbox at `.tasker-data/auto-healing/workspace` (DEBUG prints, trailing whitespace, missing final newline), snapshotting a pre-fix backup and generating a `difflib` unified diff; stage 5 commits on branch `autohealing/<run_id>` when git exists (now installed in the runtime image) or falls back to a sha1 snapshot |
| **Storage** | Implemented | `healing/storage.py`: atomic `runs.json`, `patches/` and `backups/` dirs with a path-traversal guard; root dir from `TASKER_HEALING_DIR` (default `.tasker-data/auto-healing`, already gitignored); `TASKER_HEALING_REPO` optional workspace override |
| **API** | Implemented | `routers/auto_healing.py` (prefix `/api/v1`): `GET/POST /auto-healing/runs`, `GET .../{id}`, `.../{id}/logs`, `.../{id}/patches`, `GET .../{id}/patches/{pid}` (raw `text/plain` + `Content-Disposition: attachment`), `POST .../{id}/cancel`, `POST .../{id}/restart {stageId?}`; camelCase models + standard `{data, error, meta}` envelope; 404 for unknown run/issue/patch, 409 for double cancel, restart while running and unknown stage |
| **Cancel / restart semantics** | Implemented | Cancel flips run+stage to `cancelled` (stable, never self-completes); restart with no `stageId` resumes at the first non-completed stage; restart from `agent_fix` restores pre-fix backups, drops old patch artifacts and regenerates the fix; everything persists in `runs.json` across restarts |
| **Frontend API & types** | Implemented | New `frontend/src/api/autoHealingApi.ts` (`fetchPipelineRuns/Run/Logs`, `startPipelineRun`, `cancelPipelineRun`, `restartPipelineRun`, `fetchPatchContent`, `patchDownloadUrl`); `types/autoHealing.ts` gains `cancelled` statuses, `PatchMeta`, `PipelineRun.createdIssueId/patches/logs` — matching the backend camelCase contract |
| **Store (real + mock)** | Implemented | `autoHealingStore.ts`: `init/refresh` against the API, 2s polling only while a run is `running` (stopped on view unmount), `startRun/cancelRun/restartRun`, success sound on a running→completed transition, `runLogs`/`runPatches` from the API in real mode; mock arrays + `simulateCompletion` untouched so the mock mode behaves exactly as before |
| **Monitor UI** | Implemented | `AutoHealingMonitorView.vue`: real-mode issue picker + **Start Pipeline** button, **Cancel Run**/**Restart Run** controls in the progress panel, amber `Cancelled` badge/bars, live logs from the API, and a **Patch Artifacts** panel (strategy, files, size, commit) with **View Diff** loading the real patch into `DiffViewer`; mock mode keeps the fix-attempts panel |
| **DiffViewer download** | Implemented | Optional `downloadUrl` prop: the download button fetches the stored `.patch` through the API (`client` + auth headers) as a blob, falling back to the rendered content when absent (mock mode) |
| **i18n** | Implemented | `autoHealing.{startRun,starting,selectIssue,noRuns,cancelRun,restartRun,cancelled,patches,viewDiff,hideDiff,closeDiff,loadingDiff}` in EN + ES |
| **Tests** | Implemented | `tests/api/test_auto_healing_unit.py` 7/7 with a `FakeRepo` of domain entities: full run (5/5 stages, real patch download with unified diff, workspace mutated, fix issue created), live cancel + restart to completion, 409 conflicts (double cancel, restart while running, unknown stage), 404s, restart from `agent_fix` (revert + fresh patch id), persistence and interrupted-run recovery across engine reloads |
| **Verification** | Implemented | Backend: `pytest -k "not integration"` 1016 passed / 3 failed (the 3 pre-existing on HEAD), new file 7/7; `ruff check src/` 1012 errors (≤ HEAD; healing/, `routers/auto_healing.py`, `routes.py`, `routers/__init__.py` clean, `app.py` 34 = HEAD after fixing the import block I introduced); `mypy src/` 1158 errors in 133 files (HEAD 1173/133). Frontend: `npm run lint` 0 errors (2 pre-existing warnings), `npm test` 91/91, `npm run build` green (vue-tsc + vite) |
| **Docker review** | Implemented | `Dockerfile` runtime stage now installs `git` (real branch commits); rebuilt `tasker-api` + `tasker-board`, 4 containers healthy; smoke on :19001: `POST /auto-healing/runs` → 201 camelCase run → poll → `completed` 5/5 with commit `706cfab`, fix issue `78be49fc…` created in Neo4j, 21 logs, 1 patch; patch download 200 `text/plain; charset=utf-8` + `attachment` with a real unified diff over `src/report.py` + `web/dashboard.js`; cancel → `cancelled` and stable, second cancel 409; restart on cancelled → `completed` 5/5 with a fresh patch; 404 for run/issue/patch/cancel-unknown, 409 for restart-while-running; served bundle contains the new build (`autoHealingStore` chunk, `Start Pipeline`, `auto-healing/runs`) |

## 66. Policy Sandbox Rules Engine

Issue #521. The Policy Sandbox now evaluates draft rules against the real dependency graph (`GET /api/v1/graph/dependencies` over Neo4j) instead of seeded fixtures: a bounded rule engine renders matching nodes, violations and blast radius, the advanced editor parametrizes the rule with a live preview, and promotion creates a real policy through `POST /api/v1/policies`.

| Feature | Status | Details |
|---|---|---|
| **Rule engine** | Implemented | New `frontend/src/utils/ruleEngine.ts`: DSL JSON (`RuleDsl` with `node`/`edge` kinds and `compare/contains/matches/dependencyCount/sameNode/all/any/not` conditions) evaluated over `GraphData` under `DEFAULT_ENGINE_LIMITS` (5000 nodes, 20000 edges, 2000ms timeout, condition depth 16, 200k condition evaluations, 500 matches, blast depth 10); unparsable code returns `failed`/`unrecognizedRule`; legacy interpreters keep old rules working (cypher self-dependency, `depCount > N`, `layer = 'x'`; yaml `contains`/`not_contains`/`equals`/`not_equals`) |
| **Real graph source** | Implemented | New `frontend/src/api/graphApi.ts`: `fetchDependencyGraph()` maps `GET /graph/dependencies` (`nodes` + `from_node`/`to_node` edges → `from`/`to`); when the endpoint yields nothing the store builds the graph from `fetchIssues` + `fetchComponents` and finally falls back to a seeded 6-node demo graph; `SimulationResult.dataSource` (`api`/`fallback`) drives the badge in the report and editor preview |
| **Simulate + impact report** | Implemented | `sandboxStore.loadGraph/simulateRule/simulatePreview` run the engine over the loaded graph and persist simulations; `ImpactReport.vue` shows nodes/edges checked, violations, matched-node chips, blast radius grid (direct/total/critical/high/depth), live-vs-fallback badge, truncation warning and a failed state for unparsable rules; the promote gate stays available with an amber (violations) / green (clean) button |
| **Advanced editor** | Implemented | New `components/sandbox/RuleEditorModal.vue`: presets (field condition, dependency count, required label, self dependency, forbidden path) with node/edge target, operator/value, blast radius depth and message template; the parameters regenerate the JSON code, hand-edited JSON is validated (`invalidJson` / `legacyFormatNotice`), and the preview runs the real engine before saving; `PolicySandboxView` keeps the inline code panel (save draft + **Simulate on real graph**, JSON/Cypher/YAML select) and delegates create/edit to the modal |
| **Draft persistence** | Implemented | `sandboxStore` persists rules in `localStorage` (`socialseed-sandbox-rules`) with seed rules/simulations on first load; `createRule` starts drafts (`isDraft`), `updateRule`/`deleteRule`/`promoteRule` re-persist |
| **Promotion** | Implemented | Promote → `policiesStore.createPolicy` → `policiesApi.createPolicy`, which maps the sandbox body to the backend contract (`rule` → `logic_definition`, `level` HARD→`BLOCKER`/SOFT→`WARNING`, scope `project|component|issue` → `PROJECT|COMPONENT|CODE_SYMBOL`, pass-through of already-valid enums) — the raw body would raise `ValueError` in `PolicyTargetScope(...)`/`PolicySeverity(...)` and 500; mock/offline path unchanged; success/error surfaced with toasts |
| **i18n** | Implemented | `sandbox.*` EN + ES (ASCII in ES): `simulateReal`, `graphSourceApi/Fallback`, `nodesChecked`, `matchedNodes`, `blastRadius`/`blastDirect`/`blastTotal`/`blastCritical`/`blastHigh`/`blastDepth`, `truncatedWarning`, `simulationFailed`, `unrecognizedRule`, `invalidJson`, `legacyFormatNotice`, rule editor fields/presets/target, preview keys, `completedLabel`, `promoteSuccess`/`promoteFailed` |
| **Tests** | Implemented | New `frontend/src/utils/ruleEngine.spec.ts` 22 tests: DSL validation (incl. depth limit), JSON/cypher/yaml parsing, node/edge matching, array comparisons (`=`/`!=`), dependency counts, composite `all/any/not`, message templates, `failed` states, `maxNodes` + evaluation-budget truncation, blast radius depth (0 → null, capped at limit) |
| **Verification** | Implemented | Frontend: `npm run lint` 0 errors (2 pre-existing warnings), `npm test` 113/113, `npm run build` green (vue-tsc + vite); backend untouched. Docker: rebuilt `tasker-board` from the fresh `dist/`, 4 containers healthy; smoke on :19001 → page 200, served bundle contains the `PolicySandboxView` chunk + new i18n keys, `GET /api/v1/graph/dependencies` returns real Neo4j nodes/edges, `POST /api/v1/policies` with the mapped body → **201** (`target_scope: PROJECT`, `severity: BLOCKER`, `logic_definition` stored) |

## 67. Bidirectional Real Sync with GitHub

Issue #522. Tasker now exchanges real updates with GitHub: HMAC-signed webhooks mutate local issues (edits, comments, PRs), local edits push back to GitHub, and double-edit conflicts are detected per field with a Keep local / Keep remote / Merge resolution panel; the issue detail subscribes to a live SSE stream of sync events.

| Feature | Status | Details |
|---|---|---|
| **Webhook receiver** | Implemented | `POST /api/v1/webhooks/github` validates `X-Hub-Signature-256` (HMAC-SHA256 over the raw body with `GITHUB_WEBHOOK_SECRET`, 401 when missing/invalid) and processes `issues`, `issue_comment` and `pull_request` events through `apply_github_event`; the API-key middleware exempts this path (GitHub cannot attach API keys, the signature is the authentication); delivery logs gained a `detail` field (`applied title,labels`, `conflict title`, `ignored_echo`, ...) and the `GET /webhooks/github/logs` response exposes it |
| **3-way merge service** | Implemented | New `application/github_sync.py`: the `github_base` snapshot (last known GitHub state) enables per-field dirty checks without trusting timestamps - a conflict is raised only when local differs from base, remote differs from base and local differs from remote; state kept in `github_sync_status` (`SYNCED` / `CONFLICT` / `ERROR`), `github_conflict {fields, local, remote, detected_at}` and `github_error` |
| **Incoming updates** | Implemented | Webhook edits apply remote title/description/status/labels; `issue_comment` appends the comment with the GitHub author (Tasker's own echoes are skipped via the `<!-- socialseed-tasker -->` marker); `pull_request` records `github_pr_url` / `github_pr_number` and closes the linked issue when merged |
| **Outgoing updates** | Implemented | `PATCH /issues/{id}` and `POST /issues/{id}/close` push the changed mirrored fields (title, description, status, labels) to GitHub after persisting; without `GITHUB_TOKEN` / `GITHUB_REPO` the push degrades to a visible `ERROR` state with the message instead of failing the request |
| **Conflict resolution** | Implemented | `POST /issues/{id}/github-sync/resolve` with `local` (push local values), `remote` (apply remote values) or `merge` (apply the supplied values); 400 when there is no conflict or values are missing; `POST /issues/{id}/github-sync` force re-syncs (pull + merge); `link-github` stores the metadata + base snapshot and `unlink-github` clears all nine GitHub fields |
| **Live stream** | Implemented | `RealtimeHub.publish_sync/subscribe_sync` + `GET /issues/{id}/github-sync/stream` SSE (`connected` / `ping` / `sync` events); webhook processing, force re-sync and conflict resolution broadcast to connected viewers |
| **Frontend card + detail** | Implemented | `GitHubSyncCard` rewritten against the real API (the `setTimeout` simulation is gone): CONFLICT badge, sync error panel, PR link, null-safe last-synced, and a conflict panel showing per-field Tasker vs GitHub values with Keep local / Keep remote / Merge (editable textareas) calling `githubSyncApi.ts` (`resyncIssue`, `resolveConflict`) and emitting the updated issue; `IssueDetailView` refetches on `sync:updated` and on SSE `sync` events in real mode; `GitHubSyncHealth` gained the CONFLICT bucket in the bar and rows |
| **Mock parity** | Implemented | `mockClient` routes + `mockApi.resyncGithubIssue/resolveGithubConflict` persist through the mock server (`IssueUpdate.github_sync`), so mock mode keeps working end to end |
| **Offline queue (#515)** | Implemented | GitHub pushes happen server-side on the same PATCH/close endpoints the offline queue replays, so queued offline mutations flush into GitHub pushes automatically when connectivity returns; no separate queue entry is needed |
| **i18n** | Implemented | `githubSync.*` EN + ES (ASCII in ES): `status.CONFLICT`, `conflict`, `conflictHint`, `keepLocal`, `keepRemote`, `merge`, `applyMerge`, `local`, `remote`, `error`, `actionFailed`, `prView`, `neverSynced` |
| **Tests** | Implemented | New `tests/unit/test_github_sync.py` 24 tests (signed webhook processing, comment echo skip, PR merge close, 3-way merge/conflict matrix, push from PATCH/close, resolve local/remote/merge, force re-sync, response representation) and new `frontend/src/components/issue/GitHubSyncCard.spec.ts` 6 tests (real resync emit, error path, conflict panel, keep-local, merge flow) |
| **Verification** | Implemented | Backend: `ruff check src/` 1011 errors (baseline 1012), `mypy src/` 1158 errors / 133 files (baseline 1159/133), `pytest -k "not integration"` 1040 passed / 3 pre-existing failures. Frontend: `npm run lint` 0 errors (2 pre-existing warnings), `npm test` 119/119, `npm run build` green (vue-tsc + vite). Docker (:19001): rebuilt `tasker-api` + `tasker-board`, 4 containers healthy, smoke 28/28 - bundle serves the new conflict i18n, webhook secret configured, unsigned webhook 401, `link-github` -> SYNCED, remote edit applied without conflict, local edit -> graceful ERROR without token, second remote edit -> CONFLICT with local/remote values, resolve remote -> SYNCED, resolve local keeps the local title and surfaces the push error, force re-sync degrades to ERROR, `issue_comment` appends the comment, delivery logs carry `detail`, SSE stream emits `event: connected` |

## 68. RAG Explorer & MCP Server Integration

Issues #524, #535. The Graph RAG Explorer now queries the real Neo4j vector index instead of seeded fixtures, and the MCP Inspector gained a live mode backed by a backend MCP registry: servers/sessions/tool calls are served over REST + SSE with server-side secret redaction, per-tool latency metrics, payload inspection and one-click re-run. Since #535 the registry also backs a real MCP transport (streamable HTTP at `/mcp` + stdio) that external clients like Cursor and Claude Desktop can connect to.

| Feature | Status | Details |
|---|---|---|
| **Backend MCP registry** | Implemented | New `src/socialseed_tasker/infrastructure/web_api/routers/mcp.py`: in-process `MCPRegistry` (server upserts, sessions with heartbeat, `deque` capped at 500 tool calls, SSE subscriber set) behind 9 endpoints under `/api/v1/mcp/*` (`servers`/`sessions`/`tool-calls` GET/POST/DELETE) returning the `APIResponse` envelope in camelCase (`CamelModel`); arguments/results/errors pass through `SecretFilter` before leaving the server; `POST /mcp/tool-calls/{id}/rerun` re-executes registered executors (`rag_search`, `rag_stats`), 404 for unknown ids, 400 without executor, 200 with `status=error` when the executor raises; `GET /mcp/tool-calls/stream` emits `connected`, the `tool_calls` snapshot, `tool_call`/`tool_call_update` and re-publishes `server_update`/`session_update`/`session_removed` to subscribers with a 15s ping; registered in `routers/__init__.py` (explicit `mcp_router as mcp_router` alias), `web_api/routes.py` and `web_api/app.py` |
| **MCP server (#535)** | Implemented | New `src/socialseed_tasker/entrypoints/mcp_server.py`: `MCPServer` (SDK `mcp` 2.2, `MCPServer`/`Context` from `mcp.server.mcpserver`) exposing 6 graph tools (`graph_architecture`, `list_components`, `blocked_issues`, `active_policies`, `issue_detail`, `dependency_impact`) over streamable HTTP (`build_streamable_http_app`: stateless + JSON responses, `TransportSecuritySettings(enable_dns_rebinding_protection=False)` so the Docker Host passes) mounted at `/mcp` in `app.py` via `app.routes.extend(mcp_http_app.routes)` with the session manager running in the root lifespan (sub-app lifespans do not run); auth reuses the existing `X-API-Key` guard (401 without key); every tool audits into the #524 registry (`upsert_session` external + `record_call` with camelCase payload, session id `ext-<sha1[:12]>` derived from the client User-Agent, audit failures logged and never break the tool) and `tasker-mcp` is auto-registered as an online server; stdio entrypoint `main()` + console script `tasker-mcp` (`Container.from_env()`, direct Neo4j, no secrets on stdout); `pyproject.toml` adds `mcp>=2.0.0` + `[project.scripts]`; README documents Cursor/Claude Desktop snippets; tests `tests/api/test_mcp_server_protocol.py` (10: initialize handshake, `tools/list` (6 + required `issue_id`), all tools against a graph mock, unknown tool/missing arg/404 as `isError`, inspector sessions, audit on success/error, 401/200 auth) + `test_mcp_api_unit` updated for the built-in `tasker-mcp` entry; Docker smoke on :8888 → initialize 200, `tools/list` 6 tools, `tools/call blocked_issues` 200, 401 without key, inspector shows `tasker-mcp` online + `blocked_issues` call with `ext-*` session; gates: `ruff check src/` 1011 (baseline), `mypy src/` 1152/133 (identical to HEAD worktree; +0 from source), `pytest -q` 1206 passed / 27 skipped / 6 failed (3 pre-existing: delivery_retry + 2× tasks; 3 env: Windows Hyper-V excludes TCP ports 8946–9145 which covers the contract mock server's 9010, also failing at HEAD) |
| **RAG real** | Implemented | New `frontend/src/api/ragApi.ts` (`searchRag` → `POST /rag/search?query&limit&threshold`, `getRagStats` → `GET /rag/stats`, raw payloads without envelope); `ragStore` branches on `isMockMode()`: real searches map each chunk to an `RAGResult` (`issueId`=sourceId, status `INDEXED`, component=sourceType, context nodes chunk+source joined by a `FROM` edge, model `neo4j-vector`) and stats fill the metrics panel (`totalEmbeddings` from `total`, `topComponents` sorted from `by_type`); backend errors surface in the `rag.errorTitle` box; the mock path (800ms fixtures) is untouched |
| **Solution memory (#534)** | Implemented | Closing an issue now embeds its solution text (title + resolution + description + commit) via `close_issue_action` (`build_solution_text` + `resolve_embedding_port` + `embed_issue_solution` in `application/actions.py`, injectable `embedder`, never raises, logs and degrades without `OPENAI_API_KEY`); the duplicate embed block was removed from `neo4j_impl/issue_mixin.close_issue` (create/update still embed); new `POST /api/v1/ai/search-similar-solutions` (`SimilarSolutionsRequest` {query, threshold, limit} → embed query → `search_by_embedding` overfetch → endpoint-side CLOSED filter → `{issue_id, title, score, resolution}`, `data=[]` without a provider) and new `POST /api/v1/ai/backfill-embeddings?force=` (embeds closed issues missing `description_embedding`, `force` re-embeds all → `{embedded, skipped, failed, total_closed}`); tests `tests/unit/test_embedding_on_close.py` (8) + `tests/api/test_search_similar_solutions.py` (7) |
| **MCP live frontend** | Implemented | New `frontend/src/api/mcpApi.ts` (`normalizeSession/Server/ToolCall` + fetch/register servers, save/remove sessions, fetch/record/rerun tool calls); `mcpStore` gained `servers`, `toolCalls`, `error`: real `fetchSessions` runs `Promise.all` of the three GETs, `startStream` connects `connectSSE('/mcp/tool-calls/stream')` and upserts sessions/servers/calls from stream events, mock mode keeps local fixtures (6 sessions, 2 servers, 8 calls) plus a 5s ticker; `utils/pendingFeatures.ts` no longer excludes `/rag` and `/mcp` |
| **Inspector UI** | Implemented | LIVE/MOCK badge in both view headers; MCP Servers panel (transport, URL, tools, last seen); tool-call feed (status pill, amber duration over 800ms, started-at, view-payload and re-run actions with disabled state while running); **Latency by Tool** table (calls/successes/errors/avg/max with an amber `Slow` badge when avg > 800ms); payload modal with pretty-printed arguments, result summary, error and a Re-run button; sessions matrix unchanged |
| **i18n** | Implemented | `rag.{dataLive,dataMock,errorTitle}` and `mcp.{dataLive,dataMock,servers,noServers,lastSeen,toolCalls,noToolCalls,tool,duration,startedAt,rerun,rerunning,rerunOf,viewPayload,payload,argumentsLabel,resultLabel,errorLabel,latency,calls,successes,errors,avg,max,slow,callStatuses.*}` EN + ES (ASCII in ES); fixed the pre-existing `mcp.avgPerMin` message from `{{rate}}` to `{rate}` - vue-i18n compiles named placeholders with single braces, so the double braces raised "Not allowed nest placeholder" and crashed the inspector view at runtime |
| **Tests** | Implemented | Backend new `tests/api/test_mcp_api_unit.py` 13 tests (registry upserts, session validation, tool-call filters/422, updates without duplicates, secret redaction, rerun 404/400/success/error, SSE by invoking `stream_tool_calls(Request(scope))` directly because `TestClient.stream` hangs for every SSE endpoint in this environment, subscribe/publish, 500-cap); frontend +18: `stores/ragStore.spec.ts` 6, `stores/mcpStore.spec.ts` 9, `views/MCPInspectorView.spec.ts` 3 |
| **Verification** | Implemented | Backend gates at baseline: `ruff check src/` 1011, `mypy src/` 1158/133, `pytest -q` 1093 passed / 27 skipped / 3 pre-existing failures (reproduced with the changes stashed). Frontend: `npm run lint` 0 errors (2 pre-existing `vue/no-mutating-props` warnings), `npm test` 158/158 (20 files), `npm run build` green (vue-tsc + vite). Docker: rebuilt `tasker-api` + `tasker-board`, smoke on :19001 -> index 200, served bundle contains `MCP Servers`, `Latency by Tool`, `Re-run tool`, `Payload Inspection`, `Graph RAG Explorer`; `GET /api/v1/mcp/{servers,sessions,tool-calls}` -> 200 with the envelope, `GET /api/v1/rag/stats` -> `{"total":0,"by_type":{}}`, `POST /api/v1/rag/search` -> `{"results":[],"count":0}` (no `OPENAI_API_KEY` => visible empty/error state in the UI), SSE `/api/v1/mcp/tool-calls/stream` -> `event: connected` + `tool_calls` snapshot |

---

## 69. Setup Wizard & First-Run Installation (Onboarding)

Backlog v5 (`notas.md` Épica *Onboarding & Setup Wizard Empresarial*) — issues #542–#546: from the `tasker setup` CLI command to the guided first-run wizard in the UI, guarded by a persisted install flag and hardened against accidental reinstalls.

| Feature | Status | Details |
|---|---|---|
| **`tasker setup` CLI (#542)** | Implemented | New `src/socialseed_tasker/cli/setup_command.py`: Docker/Compose preflight (`shutil.which`), idempotent `.env` seeding `TASKER_INSTALLED=false`, parametrized `docker-compose.yml` (`${TASKER_*}` defaults matching the current stack, ports API `8888`/board `19001`), `docker compose up -d --build` and Rich output with the wizard URL `http://localhost:<port>/setup` (`--port` default `19001`); `--dev` flag kept but **deprecated** — images are now always rebuilt so a stale `tasker-board`/`tasker-api` image can no longer serve old code (#555, root cause of the masked #552/#553 deploy); `.env.example` documents the compose vars |
| **Setup endpoints (#543)** | Implemented | `routers/setup.py`: `GET /api/v1/setup/status` → `{installed, needSetup}` from the `:Project {initialized_at}` node or the `TASKER_INSTALLED=true` override; `POST /setup/initialize` sanitizes the admin (`normalize_username`, default `admin`/`admin`), wipes Neo4j + PostgreSQL public tables + Mongo chat collections + Redis, creates the bcrypt admin in PostgreSQL plus `:User ADMIN`, the root `:Project` and `[:ENFORCES]` policy links; returns **403** when already installed; development auth seed (`TASKER_AUTH_SEED`) is skipped once installed |
| **Wipe hardening (#546 follow-up)** | Implemented | `setup_initialize` is fail-closed: **503** when the store cannot answer (never wipe on a degraded status check) and **400** unless `confirm_wipe=true` when the graph still holds nodes while the install flag reads "not installed" — an independent signal that blocks accidental wipes on stale/failed reads; `_installed` now logs the degradation instead of failing silently; the initialize guard is covered by `test_initialize_fails_with_503_when_store_unavailable`, `test_initialize_requires_confirm_wipe_when_system_has_data` and `test_initialize_fails_closed_when_node_count_unavailable` |
| **Navigation guard (#544)** | Implemented | `router/setupGuard.ts` chained after `initSession()`: redirects to `/setup` when not installed and to `/board` when `/setup` is entered already installed; `/setup` exempted from `LoginScreen`; no guard in mock mode (issue #517); `uiStore.isInstalled` / `checkSetupStatus()` cached |
| **Setup wizard UI (#545)** | Implemented | `SetupWizardView.vue`: `/setup` route outside the navigation with a clean `isSetupRoute` shell (no sidebar/header/ticker/chat), 4 steps (credentials with password toggle, project name/summary, 3 predefined policy checkboxes + dynamic custom policies, confirmation with loader); forces `setApiMode('real')` right after install (#545); i18n `setup.*` EN + ES (ASCII in ES) + spec vitest |
| **AI credentials & MCP (#546)** | Implemented | `SetupPayload` extended with `api_key` (empty → backend generates `tasker_sk_live_…` via `secrets.token_urlsafe(32)`) and `mcp_port` (0 = auto); the master key is persisted in the secrets store (`master_api_key`, metadata `mcpPort`/`source`, degrades to in-process key only) and accepted by the auth middleware with lazy reload after an API restart; post-install panel `McpSetupPanel.vue` (key + copy feedback, editable MCP port, ready-to-paste `.cursor/mcp.json` snippet whose URL derives from `window.__API_URL__`/`VITE_API_URL` and carries the `X-API-Key` header); nginx serves `index.html` with `Cache-Control: no-cache` and proxies `location /mcp` to `tasker-api:8000/mcp` with streaming (no buffering); `finish` navigates to `/board` from the credentials panel |
| **Welcome notification (#549)** | Implemented | `setup_initialize` is now `async`: the install body (sync Neo4j sessions, bcrypt, pymongo/redis wipes) runs in the worker thread via `run_in_threadpool` (`_perform_initialize`) exactly as FastAPI ran sync endpoints, while only the onboarding insert runs on the event loop against `app.state.notification_repository` (#547) — same motor client/loop as the lifespan; seeds **two** admin notifications (literal notas.md welcome + *"Define tus agentes en Usuarios"*, both `WELCOME`/`INFO`/`channel=system`, `requiresAction`, `linkTo /users`); `_wipe_mongo` already drops **every** non-system collection incl. `notifications` (locked by `test_wipe_mongo_drops_notifications_collection`); `NotificationStoreError` degrades to a warning (install always succeeds) and a per-`(user_id, title)` guard via `list_for_user(..., "WELCOME")` never duplicates either notification (#549, #552) |
| **Wizard auto-login (#552)** | Implemented | On successful `POST /setup/initialize` the wizard calls the new `authApi.loginWithCredentials` (`POST /auth/login {username,password}`, best-effort — failure clears the error and falls back to the LoginScreen) before showing the credentials panel, so `/board` mounts with a live session and `notificationsStore.startRealtime()` hydrates the onboarding pair immediately; `authStore.isAuthenticated` no longer treats the hardcoded `window.__API_KEY__` as a session, so a browser without a real session shows the LoginScreen instead of a silently empty feed |
| **Master-key session (#552)** | Implemented | `POST /auth/login` with `{api_key}` accepts the setup-wizard master key (`tasker_sk_live_…`) as a full **ADMIN** session: shared `setup.resolve_master_key(app.state)` (in-process copy with lazy secrets-store fallback, now also caching `adminUsername` metadata) used by both the auth middleware and the login branch, so the apiKey shown in the wizard/CLI is a valid credential for the LoginScreen and identifies the installed admin (falls back to `admin` when the metadata is absent) |
| **Tests & gates** | Implemented | Backend `tests/api/test_setup_endpoints.py` (20 tests: status/env override/degraded 200, wipe order, policy mapping, 403/400/503/422, master key generate/echo/persist + middleware auth incl. lazy reload, `confirm_wipe`); frontend `SetupWizardView.spec.ts` + `McpSetupPanel.spec.ts`; gates: `pytest -q` 1282 passed + 3 pre-existing, `ruff check src/` 1011, `mypy src/` 1153, `npm run lint` 0 errors, vitest 270 passed (39 files); live smoke on :19001: `/mcp` initialize 200 with the env key / 401 with a bogus `tasker_sk_live_…`, `POST /setup/initialize` 403 while installed, `GET /setup/status` `installed=true` — #549 extends the suite to 27 tests (`pytest` 1313 passed + 3 pre-existing, `ruff`/`mypy` at baseline) |
