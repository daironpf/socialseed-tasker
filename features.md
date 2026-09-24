# SocialSeed Tasker - Frontend Feature Inventory

> Complete catalog of all UI features, interactions, and capabilities currently implemented.
> Use this document to identify gaps, plan new features, and track what is missing.
> Last updated: 2026-09-24

---

## Table of Contents

1. [Global Infrastructure](#1-global-infrastructure)
2. [Authentication](#2-authentication)
3. [Layout & Navigation](#3-layout--navigation)
4. [Dashboard (BoardView)](#4-dashboard-boardview)
5. [Issues List (ListView)](#5-issues-list-listview)
6. [Kanban Board (KanbanView)](#6-kanban-board-kanbanview)
7. [Issue Detail Panel (IssueDetailView)](#7-issue-detail-panel-issueDetailView)
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

---

## 1. Global Infrastructure

| Feature | Status | Details |
|---|---|---|
| Vue 3.5 + TypeScript | Implemented | Composition API, `<script setup>`, vue-tsc type checking |
| Vite 6 build tool | Implemented | HMR, optimized production builds, lazy-loaded routes |
| Tailwind CSS 3 | Implemented | Dark mode via `class` strategy; Inter font |
| Pinia state management | Implemented | 21 stores under `src/stores/` |
| Vue Router | Implemented | 22 view routes + `/` redirect + catch-all NotFound; lazy-loaded; scroll-to-top on navigate |
| i18n (EN/ES) | Implemented | `vue-i18n` with `legacy:false`, 65 top-level sections, ~1255 leaf keys per language, localStorage persistence |
| Dark mode | Implemented | Toggle via UserMenu / `D` shortcut / CommandPalette; localStorage; system preference detection |
| Mock API mode | Implemented | `USE_MOCK = true` in `client.ts`; axios instance swapped for mock client; `mockApi.ts` uses `fetch` against `/mock-api` |
| Real API mode | Implemented | Axios client, base `window.__API_URL__ \|\| '/api/v1'`, API key auth via `X-API-Key`, 401 interceptor → `auth:unauthorized` |
| Docker deployment | Implemented | Frontend `127.0.0.1:19001→80`, mock-api `127.0.0.1:8001`, real API `127.0.0.1:8888`, Neo4j `7474`/`7687` |
| Mock data volume | Implemented | `frontend/dataset-de-pruebas/` mounted into mock-api container (`DATA_DIR`) |
| Toast notification system | Implemented | Singleton `useToast()`: success/error/warning/info, auto-dismiss, max 5 concurrent |
| html2canvas + jspdf | Implemented | PDF/PNG export for executive dashboard |
| Mermaid diagrams | Implemented | MarkdownRenderer renders Mermaid syntax in agent reasoning logs |
| vis-network | Implemented | Dependency graph visualization (issues + components + optional code nodes) |
| utils | Implemented | `modelPricing.ts`, `piiDetector.ts`, `graphUtils.ts` (BFS, cycle detection, blast radius, transitive deps) |
| Build / typecheck | Implemented | `npm run build` → `vue-tsc -b && vite build` |

### Mock dataset files (`frontend/dataset-de-pruebas/`)

`issues.json` (100), `components.json`, `users.json`, `policies.json`, `constraints.json`, `agent-logs.json`, `dependencies.json`, `dashboard-stats.json`, `projects.json`, `root-cause.json`, `index.json`, `organizations.json` (3 orgs / 6 workspaces / 9 accounts)

### Container topology

| Service | Container | Host port | Role |
|---|---|---|---|
| tasker-db | neo4j:5.26.15 | 7474 / 7687 | Graph DB (APOC) |
| tasker-api | tasker-api:local | 127.0.0.1:8888→8000 | Real FastAPI backend |
| tasker-board | tasker-board:local | 127.0.0.1:19001→80 | Vue SPA + nginx (proxies `/api/`, `/mock-api/`) |
| mock-api | mock-api:local | 127.0.0.1:8001 | FastAPI mock serving dataset JSON under `/mock/*` |

> Note: Hyper-V reserves host ports 8001–8900 on some Windows machines. Local workaround uses `19000`/`19001`/`19002`; committed compose uses `19001`/`8001`/`8888` as above.

---

## 2. Authentication

| Feature | Status | Details |
|---|---|---|
| Login screen | Implemented | Full-screen overlay (`LoginScreen.vue`), password input for API key |
| API key storage | Implemented | localStorage `tasker_api_key` via `authStore` |
| Mock mode bypass | Implemented | `isAuthenticated` true when `USE_MOCK = true` (auto-authenticated) |
| 401 interceptor | Implemented | Dispatches `auth:unauthorized`, triggers reload |
| Logout | Implemented | Clears API key + full page reload (UserMenu) |
| Sign-in flow | Implemented | `App.vue` shows `LoginScreen` when unauthenticated; reload on login |

---

## 3. Layout & Navigation

### Sidebar (desktop only, `md+`)

| Feature | Status | Details |
|---|---|---|
| Collapsible sidebar | Implemented | 20px collapsed → 64px on hover (`w-20` → `w-64`), smooth transition |
| Logo + branding | Implemented | "SocialSeed" text when expanded |
| Navigation groups | Implemented | Principal (4), Management (17), Analysis (2) = **23 nav items** |
| Active route highlighting | Implemented | Color change on current route |
| Nav icons | Implemented | SVG icons per nav item |
| i18n labels | Implemented | All nav labels use `t()` |
| Mobile behavior | Implemented | Hidden below `md` (`hidden md:flex`); hamburger opens MobileDrawer |

**Nav groups**

| Group | Routes |
|---|---|
| Principal | `/board`, `/system`, `/kanban`, `/list` |
| Management | `/components`, `/policies`, `/constraints`, `/sandbox`, `/rag`, `/finops`, `/auto-healing`, `/replay`, `/executive`, `/users`, `/chat`, `/mcp`, `/hitl`, `/organization`, `/governance-matrix`, `/audit-log`, `/agents/studio` |
| Analysis | `/graph`, `/analysis` |

### Header (AppHeader)

| Feature | Status | Details |
|---|---|---|
| Dynamic page title | Implemented | Maps route path → translated title (22 paths; `/profile` falls back to dashboard title) |
| Organization switcher | Implemented | `OrganizationSwitcher` (`hidden lg:flex`, before ProjectSelector): hierarchical Organization → Workspace dropdown, localStorage, link to `/organization` settings |
| Global HITL banner | Implemented | Shown when `urgentPendingCount > 0` (CRITICAL/HIGH pending); click → HITLCommandCenter; Review button → HITLQuickActionModal |
| Hamburger menu | Implemented | 44×44 button (`md:hidden`), emits `open-mobile-menu` |
| Project selector | Implemented | `ProjectSelector`, 4 projects, localStorage, filters issues |
| Sync status badge | Implemented | `SyncStatusBadge` (`hidden sm:flex`): SYNCED / OFFLINE_QUEUED / SYNCING |
| Notification bell | Implemented | `NotificationCenter` with unread badge |
| HITL quick action modal | Implemented | Mounted in header when `hitlStore.quickActionRequestId` set |
| UserMenu | Implemented | Top-right corner |

### MobileDrawer

| Feature | Status | Details |
|---|---|---|
| Overlay slide-in | Implemented | From left, 300ms transition, full-screen dark overlay |
| Close gestures | Implemented | Tap overlay or swipe-left |
| Navigation content | Implemented | Same 3 groups / 23 items as desktop Sidebar |
| i18n | Implemented | `mobileNav.openMenu`, `mobileNav.menu`, `mobileNav.swipeHint` |

### UserMenu

| Feature | Status | Details |
|---|---|---|
| Avatar with initials | Implemented | Auto-generated from username |
| Dropdown menu | Implemented | Click to toggle, click-outside to close |
| Dark/Light mode toggle | Implemented | Sun/Moon icons |
| Language selector | Implemented | EN/ES flag buttons, reactive switching |
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

| Feature | Status | Details |
|---|---|---|
| **Stats cards** | Implemented | 4 cards: Total Issues, Resolved This Month, In Progress, Blocked |
| **Trend chart** | Implemented | Custom SVG line chart, 8-week rolling, 3 lines (Open/Closed/In Progress), legend |
| **Avg Resolution Time** | Implemented | Circular SVG gauge, color-coded (green ≤3d, blue ≤7d, orange ≤14d, red >14d) |
| **Daily Activity Chart** | Implemented | Custom SVG bar chart, month selector, created vs resolved bars |
| **Status Distribution** | Implemented | Horizontal bar chart, 5 statuses, percentage breakdown |
| **Project info bar** | Implemented | Project name, description, active policies count |
| Loading/Error states | Implemented | Spinner + error message with refresh |
| i18n | Implemented | All labels, tooltips, and chart data translated |

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
| **GitHub Sync card** | Implemented | GitHubSyncCard: issue # link, sync badge, last synced, Force Re-sync |
| **Governance validation** | Implemented | Blocks CLOSED when requirements unmet → GovernanceValidationModal (Fix/Override) |
| **AI Reasoning tab** | Implemented | Loading state, reasoning logs with MarkdownRenderer, timestamps |
| **Progress tab** | Implemented | Affected Files (NEW/EDITED/DELETED badges + per-file DiffViewer via `diff_hunk`), Tech Debt Notes (amber Markdown), Task Checklist, Files Changed, agent-log diffs |
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
| **Responsive table** | Implemented | `overflow-x-auto` + `min-w-[720px]` |
| i18n | Implemented | All labels translated |

---

## 11. Users Management (UsersView)

| Feature | Status | Details |
|---|---|---|
| **Stats row** | Implemented | 3 cards: Total Users, Humans (blue), AI Agents (purple) |
| **User cards grid** | Implemented | Avatar, username, email, type badge, role, model, skills, stats |
| **Create user** | Implemented | Modal: Username*, Email*, Role, Skills, Avatar picker (11 emojis) |
| **Create agent** | Implemented | Modal: Username*, Email*, Model select (5 models), Specialization, Skills, Avatar (8 robot emojis) |
| **Edit user/agent** | Implemented | Dedicated modals with pre-filled fields |
| **Delete** | Implemented | Confirm dialog for users and agents |
| i18n | Implemented | All labels translated |

---

## 12. Dependency Graph (GraphView)

| Feature | Status | Details |
|---|---|---|
| **vis-network graph** | Implemented | Nodes = components + issues, Edges = dependency arrows |
| **Color legend** | Implemented | Component, Open, In Progress, Blocked, Closed + Code Overlay legend |
| **Status filter** | Implemented | Dropdown to filter issues by status |
| **Search** | Implemented | Text filter |
| **Component filter** | Implemented | GraphFilters with checkbox-based selection |
| **Max hops filter** | Implemented | Slider to limit traversal depth |
| **Layout toggle** | Implemented | Hierarchical (top-down) vs Force Directed (Barnes-Hut) |
| **Graph interactions** | Implemented | Hover, tooltip, zoom, drag, navigation, keyboard |
| **Click node → detail** | Implemented | Opens IssueDetailView for issue nodes |
| **Connect mode** | Implemented | Create relationships via click-to-connect |
| **Cycle detection** | Implemented | Prevents circular dependencies |
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
| **Edge inspector** | Implemented | Relation type, direction, weight, cycle detection (reverse `findPath` on remaining edges) |
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
| **Load Sample** | Implemented | Cycles through preset failures |

---

## 14. System Dashboard (DashboardSystemView)

| Feature | Status | Details |
|---|---|---|
| **Main metrics** | Implemented | 4 cards: Total Issues, Blocked Issues, Total Components, Agents Working |
| **System health** | Implemented | Neo4j (connected, latency), API (FastAPI version), Workers |
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
| **API key input** | Implemented | Password field with label |
| **Sign in / Skip buttons** | Implemented | Both with dark mode variants |
| **Error message** | Implemented | Red alert for invalid credentials |
| i18n | Implemented | All labels translated |

---

## 17. Shared UI Components

### Layout Components
| Component | Purpose | Details |
|---|---|---|
| `Sidebar` | Main navigation | Collapsible, 3 groups, 21 items, desktop-only |
| `MobileDrawer` | Mobile navigation | Overlay drawer, swipe-to-close, same 23 items |
| `AppHeader` | Top bar | Dynamic title, HITL banner, hamburger, org switcher (lg+), project selector, sync badge, notifications, user menu |
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
| `StatsCard` | Metric display | Title, value, subtitle, trend, color theme |
| `TrendChart` | Line chart | 8-week SVG, 3 series, legend |
| `DailyActivityChart` | Bar chart | Month selector, created/resolved bars |
| `AvgResolutionTime` | Gauge chart | Circular SVG, color-coded |
| `StatusDistribution` | Horizontal bars | 5 statuses, percentages |
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
| `NotificationCenter` / `NotificationItem` | Notification panel | Tabs (all/unread/action), mark all read; HITL click → quick action modal |
| `ToastContainer` / `ToastItem` | Toast display | Type-colored, auto-dismiss, animation |
| `KeyboardShortcutsHelp` | Shortcuts modal | Grouped shortcut list, `?` to open |
| `CommandPalette` | Quick actions | Fuzzy search: pages, actions, issues, components; recent actions; Ctrl/Cmd+K |
| `GraphFilters` | Graph filtering | Component checkboxes, priority (CRITICAL/HIGH/MEDIUM/LOW) and node type pills, status filter, max hops |
| `ProjectSelector` | Project switcher | 4 projects, localStorage, filters all views |
| `SyncStatusBadge` | Sync indicator | Green/yellow/blue, animated ping, pending count |
| `AuditLogTable` | Audit table | Timestamp, actor avatar/type, event badge, severity pill, resource, action, IP |
| `PIIRedactionPreview` | PII suite | Live `detectPII` list, Mask PII toggle, before/after preview, Mask/Reveal actions |

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
| `LoginScreen` | API key gate | Full-screen overlay login |
**Total view components:** 26 files in `src/views/` (25 routed incl. NotFound + `IssueDetailView` embedded)

**Total shared components:** 70 `.vue` files under `src/components/`

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
| **Sequence support** | Implemented | Multi-key sequences (`g` then `i`), 1000ms timeout |
| **Modifier matching** | Implemented | Ctrl, Shift, Alt, Meta |
| **Input field detection** | Implemented | Skips shortcuts when focused in input/textarea/contenteditable |
| **Scope system** | Implemented | `global` and `local` scopes |

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

> Help modal also lists `J`/`K`/`Enter`/`Esc` for list navigation; these are displayed in the help UI but are **not** currently registered via `useKeyboardShortcuts`.

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

---

## 21. Notifications System

| Feature | Status | Details |
|---|---|---|
| **Notification store** | Implemented | `notificationsStore` with localStorage persistence |
| **Mock data** | Implemented | 12 realistic notifications across 4 categories |
| **Categories** | Implemented | Mention, HITL, Constraint Violation, Agent Failure |
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
| **NotificationCenter** | Implemented | Teleported dropdown, click-outside close |

---

## 22. Data Layer (Stores)

| Store | State | Key Actions |
|---|---|---|
| `authStore` | storedKey, isAuthenticated | setApiKey, clearApiKey, getApiKey |
| `uiStore` | darkMode, locale, sidebarOpen, viewMode, currentProject, availableProjects, filters, savedSearches, connectionState, pendingSyncCount | setFilter, clearFilters, saveSearch, applySearch, toggleDarkMode, setLocale, simulateSync |
| `issuesStore` | issues[], filteredIssues, pagination, loading, selectedIssue | fetchIssues, createIssue, updateIssue, deleteIssue, closeIssue |
| `componentsStore` | components[], projects, loading | fetchComponents, createComponent, updateComponent, deleteComponent |
| `usersStore` | users[], loading | fetchUsers, createUser, updateUser, deleteUser |
| `policiesStore` | policies[], loading | fetchPolicies, createPolicy, updatePolicy, deletePolicy |
| `constraintsStore` | constraints[], validationResult, hard/soft/active counts | fetchConstraints, createConstraint, updateConstraint, validateConstraints, deleteConstraint |
| `analysisStore` | impactResult, rootCauseResults[], testFailures[] | analyzeImpact, analyzeRootCause, fetchTestFailures, clearResults |
| `notificationsStore` | notifications[], unreadCount | markAsRead, markAllAsRead, dismiss, getFiltered, ensureHitlNotifications |
| `chatStore` | conversations[], messages, activeConversationId, typingUsers[], searchQuery | selectConversation, sendMessage, togglePin, createConversation, simulateTyping |
| `sandboxStore` | rules[], selectedRule, simulationResult | Mock CRUD + simulation |
| `ragStore` | searchResults[], queryStats | Mock search, getContext |
| `mcpStore` | sessions[], selectedSession, isStreaming | Mock MCP session management |
| `hitlStore` | requests[], selectedRequest, urgentPendingCount/Requests, quickActionRequestId, loadedOnce | fetchRequests, resolveAction, openQuickAction, closeQuickAction |
| `finopsStore` | models[], components[], tasks[], roi[], alerts[], caps[], metrics | updateCap, toggleCap |
| `executiveStore` | kpis[], cycleTime[], debt[], compliance[] | formatTrend, complianceColor |
| `autoHealingStore` | runs[], logs[], fixAttempts[], selectedRunId | selectRun, stageColor, formatDuration |
| `agentReplayStore` | sessions[], currentTime, isPlaying, playSpeed | play, pause, stepForward, stepBackward, seekTo |
| `codeGraphStore` | nodes[], codeEdges[], enabled | fetchCodeStructure, toggle |
| `organizationsStore` | organizations[], currentOrgId, currentWorkspaceId, activeRole, quotaUsage, canEdit/canManage | fetchOrganizations, createOrganization, updateOrganization, setOrg, setWorkspace, setActiveRole, upsertAccount, removeAccount (persists `currentOrg`/`currentWorkspace`/`activeEnterpriseRole` in localStorage; syncs workspace → `uiStore.setProject`) |
| `governanceStore` | matrix (agent x risk x action permission cells), alerts[], activeAlerts, pausedCount | toggleCell, setCell, getCell, resetMatrix, simulateRestrictedAction, resolveAlert (matrix persisted in localStorage `governance-matrix-v1`; approval-level alerts pause/resume issue `agent_working` |
| `auditLogStore` | entries[] (84 deterministic seeded mock events), filters (dateFrom/dateTo/actor/agent/eventType/severity/search), filteredEntries, severityCounts, actors, agents, chain[] (mock hash blocks) | setFilter, clearFilters, exportRows (deterministic PRNG seed 20260924; no API — generated in store per issue spec) |
| `agentStudioStore` | profiles[] (`AgentProfile` library), enabledCount | saveProfile (create/update), cloneProfile, toggleEnabled, removeProfile, markUsed, syncUsers, blankProfile (persists localStorage `agent-studio-v1`; merges studio agents into `usersStore.users` so they survive `fetchUsers` refetch) |

**23 Pinia stores total.**

---

## 23. API Layer

### Modules (`src/api/`)

| Module | Endpoints | Methods |
|---|---|---|
| `client.ts` | Dual client: mock (`USE_MOCK`) vs axios real; API key header; 401 interceptor | — |
| `mockApi.ts` | `fetch` → `/mock-api/mock/*` | issues, components, policies, users, constraints, analysis, agent-logs, dashboard-stats, health, sync-queue, admin seed/reset |
| `issuesApi` | `/issues`, `/issues/{id}`, `/issues/{id}/close`, `/blocked-issues` | GET, POST, PATCH, DELETE |
| `componentsApi` | `/components`, `/components/{id}` | GET, POST, PATCH, DELETE |
| `policiesApi` | `/policies`, `/policies/{id}` | GET, POST, PATCH, DELETE |
| `constraintsApi` | `/constraints`, `/constraints/{id}`, `/constraints/validate` | GET, POST, PATCH, DELETE |
| `usersApi` | `/users`, `/users/{id}` | GET, POST, PUT, DELETE |
| `analysisApi` | `/analysis/impact/{id}`, `/analysis/root-cause`, `/test-failures` | GET, POST |
| `systemApi` | `/health`, `/sync-queue`, `/admin/seed`, `/admin/reset` | GET, POST |
| `agentLogsApi` | `/issues/{id}/agent-logs` | GET |
| `organizationsApi` | `/organizations`, `/organizations/{id}` | GET, POST, PATCH, DELETE |
| `useAgentStream` | `/issues/{id}/agent-logs/stream` | SSE |

### Mock API server (`mock-api/server.py`)

FastAPI endpoints under `/mock/*`: users CRUD, issues CRUD + agent-logs, components CRUD, policies CRUD, constraints CRUD + validate, organizations CRUD, dashboard-stats, analysis impact/root-cause, test-failures, health, sync-queue, admin seed/reset. Serves JSON from `DATA_DIR` (`frontend/dataset-de-pruebas`). Supports `?project=` filtering on issues.

### nginx routing (frontend container)

- `/api/` → `tasker-api:8000`
- `/mock-api/` → `mock-api:8001`

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

### Specialized Types (18 files under `types/`)
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
- `en.json`: ~1312 leaf keys, **66** top-level sections
- `es.json`: ~1313 leaf keys, matching structure

### Sections (66)
`kanban`, `mobileNav`, `nav`, `header`, `menu`, `dashboard`, `issues`, `githubSync`, `governance`, `agent`, `components`, `policies`, `constraints`, `users`, `graph`, `codeOverlay`, `analysis`, `system`, `auth`, `common`, `dashboardStats`, `trendChart`, `statusDistribution`, `dailyActivity`, `avgResolution`, `statsCard`, `shortcuts`, `palette`, `editor`, `diff`, `hitl`, `audit`, `stream`, `tokens`, `notifications`, `agents`, `toast`, `chat`, `mcp`, `hitlCenter`, `floatingChat`, `presence`, `projects`, `sync`, `export`, `bulkActions`, `profile`, `commandPalette`, `sandbox`, `rag`, `finops`, `autoHealing`, `replay`, `pii`, `executive`, `mockStream`, `filterBuilder`, `diffPreview`, `hitlBanner`, `hitlQuickAction`, `organizations`, `governanceMatrix`, `graphExplorer`, `auditLog`, `piiSuite`, `agentStudio`

### Coverage
- All user-visible text uses `t()`
- Form labels, placeholders, error messages translated
- Button text and aria-labels translated
- Status/priority/type labels translated
- Time-ago strings computed with i18n
- Audit trail descriptions use parameterized i18n
- Slash commands, toasts, chat, floating chat, PII warnings translated
- Executive, FinOps, auto-healing, replay, GitHub sync, governance, agent timer, sync status translated
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
| **Mock data** | Implemented | 2 sessions: code-creator (active), data-analyst (idle) |
| **Store** | Implemented | `mcpStore.ts` |
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
| **Rule promotion** | Implemented | Promote simulated rules to production (UI only) |
| **Mock data** | Implemented | 3 rules: dependency-depth-limit, technology-restriction, naming-convention |
| **Store** | Implemented | `sandboxStore.ts` |
| i18n | Implemented | `sandbox` section |

---

## 33. Graph RAG Explorer (GraphRAGExplorerView)

| Feature | Status | Details |
|---|---|---|
| **Search input** | Implemented | Text field + search button, Enter key |
| **Results list** | Implemented | Cards: entity name, type, score, sub-graph preview |
| **Query stats** | Implemented | Tokens, nodes, edges, sub-graph count |
| **Mock data** | Implemented | 2 results: authentication-service, payment-service |
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
| **Mock data** | Implemented | 3 runs, 12 log entries, 3 fix attempts |
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
| **Force Re-sync** | Implemented | Button with spinner, simulates sync cycle |
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
| i18n | Implemented | `governance` section |

---

## 42. Network Status & Sync Indicator

| Feature | Status | Details |
|---|---|---|
| **Connection state** | Implemented | `uiStore.connectionState`: SYNCED, OFFLINE_QUEUED, SYNCING |
| **Pending count** | Implemented | `uiStore.pendingSyncCount` |
| **Sync simulation** | Implemented | OFFLINE_QUEUED → 2s → SYNCING → 0.8s → SYNCED |
| **Visual indicator** | Implemented | `SyncStatusBadge.vue`, color-coded, animated ping |
| **Colors** | Implemented | Green SYNCED, Yellow OFFLINE_QUEUED, Blue SYNCING |
| **Integration** | Implemented | AppHeader between ProjectSelector and NotificationCenter (hidden below `sm`) |
| **Trigger points** | Implemented | ListView, KanbanView, GraphView call `simulateSync()` after CRUD |
| i18n | Implemented | `sync` section |

---

## 43. Agent Timer & Kill Switch

| Feature | Status | Details |
|---|---|---|
| **Timer data** | Implemented | `agent_working_started_at` on Issue, set for agent_working issues |
| **Live timer** | Implemented | Updates every second; "Xh Ym Zs" or "Ym Zs" |
| **Kill button** | Implemented | Red stop icon on hover; sets `agent_working=false` |
| **Timer cleanup** | Implemented | Interval cleared on unmount |
| **Store update** | Implemented | `updateIssue()` with `agent_working: false`, `agent_working_started_at: null` |
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
| `/:pathMatch(.*)*` | NotFound | NotFoundView.vue |

### Views without routes
| View | Usage |
|---|---|
| `IssueDetailView.vue` | Embedded slide-in in ListView, KanbanView, GraphView |

### Composables (`src/composables/`)
`useToast`, `usePresence`, `useMockStream`, `useKeyboardShortcuts`, `useExport`, `useAgentStream`

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
- No real backend integration (mock mode only; `USE_MOCK = true`)
- No actual WebSocket/SSE connections to a live server (mock stream only)
- No real user authentication (API key only; mock auto-auth)
- No real multi-user concurrent editing
- No actual PII remediation (masking UI only)
- No real code graph extraction (mock data only)
- No real FinOps billing data
- No real auto-healing pipeline execution
- No real agent replay recording
- No real executive KPI calculations
- No real RAG index or vector search
- No real MCP server connections
- No HITL backend workflow
- No Policy Sandbox rule engine
- No real audit trail persistence
- No test suite (no Vitest/Jest configuration or `*.spec.ts` / `*.test.ts`)
- No CI/CD pipeline (no `.github/workflows`)
- No Storybook / component documentation
- No E2E tests
- No accessibility audit (WCAG compliance)
- No performance monitoring / Lighthouse
- No service worker / offline support
- No internationalization for right-to-left languages
- No mobile bottom navigation bar (hamburger drawer only)
- No real GitHub bidirectional sync
- No real governance rule engine backend
- No real sync queue persistence
- Local list-nav shortcuts (`J`/`K`/`Enter`) shown in help modal but not registered
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
