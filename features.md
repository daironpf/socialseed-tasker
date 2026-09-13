# SocialSeed Tasker - Frontend Feature Inventory

> Complete catalog of all UI features, interactions, and capabilities currently implemented.
> Use this document to identify gaps, plan new features, and track what is missing.

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
15. [Shared UI Components](#15-shared-ui-components)
16. [Data Layer (Stores)](#16-data-layer-stores)
17. [API Layer](#17-api-layer)
18. [Type System](#18-type-system)
19. [CRUD Matrix](#19-crud-matrix)
20. [Interactions Matrix](#20-interactions-matrix)
21. [Known Gaps & Missing Features](#21-known-gaps--missing-features)

---

## 1. Global Infrastructure

| Feature | Status | Details |
|---|---|---|
| Vue 3.5 + TypeScript | Implemented | Composition API, `<script setup>` |
| Vite 6 build tool | Implemented | HMR, optimized production builds |
| Tailwind CSS 3 | Implemented | Dark mode via `class` strategy |
| Pinia state management | Implemented | 8 stores |
| Vue Router | Implemented | 11 routes, lazy-loaded, scroll-to-top |
| i18n (EN/ES) | Implemented | `vue-i18n` with `legacy:false`, 200+ keys per language, localStorage persistence |
| Dark mode | Implemented | Toggle via UserMenu, localStorage persistence, system preference detection |
| Mock API mode | Implemented | `USE_MOCK = true` in client.ts, full in-memory routing via mockApi.ts + mock-api server |
| Real API mode | Implemented | Axios client, API key auth via `X-API-Key` header, 401 interceptor |
| Docker deployment | Implemented | Frontend at `:8889`, mock-api at `:8001`, real API at `:8888`, Neo4j at `:7474`/`:7687` |

---

## 2. Authentication

| Feature | Status | Details |
|---|---|---|
| Login modal | Implemented | Full-screen overlay, password input for API key |
| API key storage | Implemented | localStorage persistence |
| Mock mode bypass | Implemented | Auto-authenticated when `USE_MOCK = true` |
| 401 interceptor | Implemented | Dispatches `auth:unauthorized` event, triggers reload |
| Logout | Implemented | Clears API key + full page reload (via UserMenu) |

---

## 3. Layout & Navigation

### Sidebar
| Feature | Status | Details |
|---|---|---|
| Collapsible sidebar | Implemented | 20px collapsed → 256px on hover, smooth transition |
| Logo + branding | Implemented | "SocialSeed" text when expanded |
| Navigation groups | Implemented | Principal (4), Management (4), Analysis (2) |
| Active route highlighting | Implemented | Color change on current route |
| Nav icons | Implemented | SVG icons per nav item |
| i18n labels | Implemented | All nav labels use `t()` |

### Header (AppHeader)
| Feature | Status | Details |
|---|---|---|
| Dynamic page title | Implemented | Maps route path → translated title |
| UserMenu component | Implemented | Top-right corner |

### UserMenu
| Feature | Status | Details |
|---|---|---|
| Avatar with initials | Implemented | Auto-generated from username |
| Dropdown menu | Implemented | Click to toggle, click-outside to close |
| Dark/Light mode toggle | Implemented | Sun/Moon icons |
| Language selector | Implemented | EN/ES flag buttons, reactive switching |
| Sign out | Implemented | Clears auth + reloads |
| User info display | Implemented | Avatar, username, role |

### TeamTicker
| Feature | Status | Details |
|---|---|---|
| Bottom marquee bar | Implemented | Fixed bottom, infinite CSS animation |
| User avatars + names | Implemented | All users from store |
| Active status indicator | Implemented | Green dot with ping if active within 24h |
| Hover pause | Implemented | Animation pauses on hover |
| Auto-refresh | Implemented | Polls every 10 seconds |

---

## 4. Dashboard (BoardView)

| Feature | Status | Details |
|---|---|---|
| **Stats cards** | Implemented | 4 cards: Total Issues, Resolved This Month, In Progress, Blocked |
| **Trend chart** | Implemented | Custom SVG line chart, 8-week rolling, 3 lines (Open/Closed/In Progress), legend |
| **Avg Resolution Time** | Implemented | Circular SVG gauge, color-coded (green ≤3d, blue ≤7d, orange ≤14d, red >14d), min/max stats |
| **Daily Activity Chart** | Implemented | Custom SVG bar chart, month selector, created vs resolved bars, balance summary |
| **Status Distribution** | Implemented | Horizontal bar chart, 5 statuses, percentage breakdown, total count |
| **Project info bar** | Implemented | Project name, description, active policies count |
| Loading state | Implemented | Spinner while fetching |
| Error state | Implemented | Error message + refresh button |
| Filter reactivity | Implemented | Re-fetches on status/priority/component/project filter changes |
| i18n | Implemented | All labels translated |

---

## 5. Issues List (ListView)

| Feature | Status | Details |
|---|---|---|
| **Data table** | Implemented | Columns: Title, Status, Priority, Component, Labels (max 2 + overflow), Created, Actions |
| **Search** | Implemented | Text filter on title, ID, description (client-side) |
| **Status filter** | Implemented | Dropdown: All, OPEN, IN_PROGRESS, BLOCKED, CLOSED |
| **Priority filter** | Implemented | Dropdown: All, CRITICAL, HIGH, MEDIUM, LOW |
| **Component filter** | Implemented | Dynamic dropdown from store |
| **Result count** | Implemented | "Showing X of Y issues" |
| **Row color coding** | Implemented | Left border: red=Critical, orange=High |
| **New Issue button** | Implemented | Opens CreateIssueModal |
| **Close action** | Implemented | Checkmark icon, hidden if already closed |
| **Delete action** | Implemented | Trash icon, confirm dialog |
| **Click row → detail** | Implemented | Opens IssueDetailView slide-in panel |
| i18n | Implemented | All labels translated |

---

## 6. Kanban Board (KanbanView)

| Feature | Status | Details |
|---|---|---|
| **4 status columns** | Implemented | OPEN, IN_PROGRESS, BLOCKED, CLOSED |
| **Column headers** | Implemented | Color-coded titles, issue count badges |
| **Drag-and-drop** | Implemented | IssueCard `draggable="true"`, KanbanColumn drop zones |
| **Priority sorting** | Implemented | CRITICAL > HIGH > MEDIUM > LOW within columns |
| **Status change on drop** | Implemented | Auto-sets `closed_at` when dropping to CLOSED, clears when leaving |
| **New Issue button** | Implemented | Opens CreateIssueModal |
| **Empty state** | Implemented | "No issues" message per column |
| **Click card → detail** | Implemented | Opens IssueDetailView slide-in panel |
| **Column titles i18n** | Implemented | Reactive via `computed()` |
| **AI agent indicator** | Implemented | Pulsing cyan circle on agent_working issues |

---

## 7. Issue Detail Panel (IssueDetailView)

| Feature | Status | Details |
|---|---|---|
| **Slide-in panel** | Implemented | Right-side overlay, click-outside to close |
| **Header** | Implemented | Issue ID, AI Agent Active badge (animated), close button |
| **3 tabs** | Implemented | Details, AI Reasoning, Progress |
| **Details tab** | Implemented | Title input, Assignee card, Creator card, Description textarea, Status select, Priority select, Labels (add/remove), Dependencies list, Created/Updated timestamps |
| **AI Reasoning tab** | Implemented | Loading state, reasoning logs with MarkdownRenderer, timestamps |
| **Progress tab** | Implemented | Task checklist (PROGRESS), Files changed (FILES), Technical debt (DEBT), MarkdownRenderer |
| **Save** | Implemented | Emits update with full body |
| **Close** | Implemented | Sets closed_at, hidden if already closed |
| **Delete** | Implemented | Confirm dialog |
| **Label management** | Implemented | Add (Enter key), remove (X button) |
| **Agent logs** | Implemented | Fetched via `GET /issues/{id}/agent-logs` |
| i18n | Implemented | All labels translated |

---

## 8. Components Management (ComponentsView)

| Feature | Status | Details |
|---|---|---|
| **Table view** | Implemented | Columns: Alias, Name, Description, Project, Issues, Actions |
| **Grid view** | Implemented | Cards with alias icon, name, project, issue count, description |
| **View toggle** | Implemented | Table/Grid switch buttons |
| **Search** | Implemented | Filter by name, alias, ID (client-side) |
| **Detail panel** | Implemented | Slide-in with alias, name, UUID, description, project, status breakdown, issue list |
| **Create** | Implemented | Modal: Alias (4 chars), Name*, Description, Project |
| **Edit** | Implemented | Same modal, pre-filled |
| **Delete** | Implemented | Confirm dialog |
| **Status breakdown** | Implemented | 4-column: Open/In Progress/Blocked/Closed counts |
| **Associated issues** | Implemented | List with status/priority badges |
| i18n | Implemented | All labels translated |

---

## 9. Policies Management (PoliciesView)

| Feature | Status | Details |
|---|---|---|
| **Card grid** | Implemented | Responsive 1-3 columns |
| **Policy cards** | Implemented | Name, active/inactive badge, description, target scope, rules count |
| **Create** | Implemented | Modal: Name*, Description, Rule select (4 types), Level (SOFT/HARD), Target Scope |
| **Edit** | Implemented | Same modal + Is Active checkbox |
| **Empty state** | Implemented | Icon + message + description |
| i18n | Implemented | All labels translated |
| **Delete** | Not in UI | Store has `deletePolicy` but no button in the UI |

---

## 10. Constraints Management (ConstraintsView)

| Feature | Status | Details |
|---|---|---|
| **Stats row** | Implemented | 4 cards: Total, Hard (red), Soft (amber), Active (green) |
| **Data table** | Implemented | Columns: ID, Name, Category, Severity, Scope, Active, Auto-fix, Actions |
| **Search** | Implemented | Filter by name, ID, description |
| **Category filter** | Implemented | Dropdown: ARCHITECTURE, TECHNOLOGY, NAMING, PATTERNS, DEPENDENCIES |
| **Severity filter** | Implemented | Dropdown: HARD, SOFT |
| **Detail panel** | Implemented | Slide-in with severity, name, UUID, category, scope, description, logic, rule JSON, remediation, active/auto-fix badges |
| **Create/Edit** | Implemented | Modal: Name*, Description, Category, Severity, Scope, Auto-fix, Logic, Remediation |
| **Delete** | Implemented | Confirm dialog |
| **Run Validation** | Implemented | Button → `POST /constraints/validate` → Results banner |
| **Validation results** | Implemented | Valid/invalid indicator, violation count, individual cards with severity, name, message, remediation, category |
| i18n | Implemented | All labels translated |

---

## 11. Users Management (UsersView)

| Feature | Status | Details |
|---|---|---|
| **Stats row** | Implemented | 3 cards: Total Users, Humans (blue), AI Agents (purple) |
| **User cards grid** | Implemented | Responsive 1-4 columns |
| **User cards** | Implemented | Avatar, username, email, type badge, role, model (agents), skills tags, stats, last active |
| **Stats buttons** | Implemented | Assigned/Created/Completed counts → opens issues modal |
| **Issues modal** | Implemented | List of user's issues with status/priority badges |
| **Create user** | Implemented | Modal: Username*, Email*, Role, Skills, Avatar picker (11 emojis) |
| **Edit user** | Implemented | Modal: Same fields, pre-filled |
| **Edit agent** | Implemented | Modal: Username, Email, Model select (5 models), Specialization, Skills, Avatar picker (8 robot emojis) |
| **Delete user** | Implemented | Human only, confirm dialog |
| **Agent delete** | Not in UI | Agents cannot be deleted from the UI |
| i18n | Implemented | All labels translated |

---

## 12. Dependency Graph (GraphView)

| Feature | Status | Details |
|---|---|---|
| **vis-network graph** | Implemented | Nodes = components (purple boxes) + issues (colored dots), Edges = dependency arrows |
| **Color legend** | Implemented | Component, Open, In Progress, Blocked, Closed |
| **Status filter** | Implemented | Dropdown to filter issues by status |
| **Search** | Implemented | Text filter |
| **Layout toggle** | Implemented | Hierarchical (top-down) vs Force Directed (Barnes-Hut) |
| **Graph interactions** | Implemented | Hover, tooltip, zoom, drag, navigation buttons, keyboard |
| **Click node → detail** | Implemented | Opens IssueDetailView for issue nodes |
| **Loading state** | Implemented | Spinner |
| **Empty state** | Implemented | Message when no data |
| i18n | Implemented | All labels translated |

---

## 13. Impact & Root Cause Analysis (AnalysisView)

### Impact Analysis
| Feature | Status | Details |
|---|---|---|
| **Issue selector** | Implemented | Dropdown of all issues |
| **Analyze button** | Implemented | Triggers BFS analysis |
| **Results display** | Implemented | Issue title, risk level badge (LOW/MEDIUM/HIGH/CRITICAL) |
| **4 stats** | Implemented | Total Affected, Direct Dependencies, Transitive, Cascade Blocked |
| **SVG tree visualization** | Implemented | Custom `ImpactSvgTree` with root node, level-grouped children, color-coded by status |
| **Direct dependencies** | Implemented | Blue cards with status badges |
| **Transitive dependencies** | Implemented | Amber cards with level badges (L2+) |
| **Cascade blocked** | Implemented | Red section with stop icon |
| **Affected components** | Implemented | Purple pill badges |
| **Click node → re-analyze** | Implemented | Click any node in tree to analyze from that issue |
| Loading state | Implemented | "Running BFS" label |

### Root Cause Analysis
| Feature | Status | Details |
|---|---|---|
| **Test failure form** | Implemented | Test Name, Component (with "Any"), Error Message |
| **Label toggles** | Implemented | 13 labels: bug, auth, security, performance, database, ui, feature, webhook, graphql, dependencies, regression, timeout, concurrency |
| **Find Root Cause** | Implemented | Disabled if no test_name/error_message |
| **Load Sample** | Implemented | Cycles through preset failures |
| **Results list** | Implemented | Ranked candidates with number, issue ID/title, status badge, graph distance, confidence % with progress bar, reason tags |
| Loading state | Implemented | Spinner |

---

## 14. System Dashboard (DashboardSystemView)

| Feature | Status | Details |
|---|---|---|
| **Main metrics** | Implemented | 4 cards: Total Issues (blue), Blocked Issues (red), Total Components (purple), Agents Working (cyan) |
| **System health** | Implemented | Neo4j (connected, latency), API (FastAPI version, running), Workers (active, queue, running) |
| **Sync queue** | Implemented | GitHub connected/disconnected, pending items, last sync, queue item list (action, resource, status) |
| **Constraints summary** | Implemented | Total rules, Active, Inactive |
| **Seed button** | Implemented | `POST /admin/seed` with confirm dialog |
| **Reset button** | Implemented | `POST /admin/reset` with confirm dialog |
| **Success/error messages** | Implemented | Display after admin operations |
| **Refresh button** | Implemented | Re-fetches health + sync queue |
| i18n | Implemented | All labels translated |

---

## 15. Shared UI Components

| Component | Purpose | Details |
|---|---|---|
| `StatusBadge` | Status pill | Color-coded: Open (blue), In Progress (amber), Closed (green), Blocked (red) |
| `PriorityBadge` | Priority pill | Color-coded: Low (gray), Medium (blue), High (orange), Critical (red) |
| `LabelTag` | Label pill | Gray rounded pill |
| `LoadingSpinner` | Loading indicator | Animated spinning circle |
| `StatsCard` | Metric card | Title, value, subtitle, trend %, color theme, icon slot |
| `NavItem` | Sidebar nav link | Icon + label, active state |
| `MarkdownRenderer` | Markdown → HTML | H1-H3, bold, italic, code, checkboxes, lists, XSS-safe |

---

## 16. Data Layer (Stores)

| Store | State | Computed | Actions |
|---|---|---|---|
| `authStore` | storedKey, isAuthenticated | — | setApiKey, clearApiKey, getApiKey |
| `issuesStore` | issues[], pagination, loading, error | openIssuesCount, blockedIssuesCount | fetchIssues, fetchIssue, createIssue, updateIssue, deleteIssue, closeIssue, fetchBlockedIssues |
| `componentsStore` | components[], loading, error | projects | fetchComponents, fetchComponent, createComponent, updateComponent, deleteComponent |
| `policiesStore` | policies[], loading, error | activeCount, inactiveCount | fetchPolicies, createPolicy, updatePolicy, deletePolicy |
| `constraintsStore` | constraints[], loading, error, validationResult | hardCount, softCount, activeCount | fetchConstraints, createConstraint, updateConstraint, deleteConstraint, validateConstraints |
| `usersStore` | users[], loading, error | humans, agents, activeAgents | fetchUsers, updateUser, createUser, deleteUser |
| `analysisStore` | impactResult, rootCauseResults[], loading* | — | analyzeImpact, analyzeRootCause, fetchTestFailures, clearResults |
| `uiStore` | selectedIssueId, sidebarOpen, viewMode, darkMode, locale, filters | — | setSelectedIssue, toggleSidebar, setViewMode, setFilter, clearFilters, toggleDarkMode, initDarkMode, setLocale, getBackendFilters |

---

## 17. API Layer

| Module | Endpoints | Methods |
|---|---|---|
| `issuesApi` | `/issues`, `/issues/{id}`, `/issues/{id}/close`, `/blocked-issues` | GET, POST, PATCH, DELETE |
| `componentsApi` | `/components`, `/components/{id}` | GET, POST, PATCH, DELETE |
| `policiesApi` | `/policies`, `/policies/{id}` | GET, POST, PATCH, DELETE |
| `constraintsApi` | `/constraints`, `/constraints/{id}`, `/constraints/validate` | GET, POST, PATCH, DELETE |
| `usersApi` | `/users`, `/users/{id}` | GET, POST, PUT, DELETE |
| `analysisApi` | `/analysis/impact/{id}`, `/analysis/root-cause`, `/test-failures` | GET, POST |
| `systemApi` | `/health`, `/sync-queue`, `/admin/seed`, `/admin/reset` | GET, POST |
| `agentLogsApi` | `/issues/{id}/agent-logs` | GET |

---

## 18. Type System

### Enums
- `IssueStatus`: OPEN, IN_PROGRESS, CLOSED, BLOCKED
- `IssuePriority`: LOW, MEDIUM, HIGH, CRITICAL
- `ConstraintCategory`: ARCHITECTURE, TECHNOLOGY, NAMING, PATTERNS, DEPENDENCIES
- `ConstraintSeverity`: HARD, SOFT

### Core Entities
- `Issue`, `Component`, `User`, `Policy`, `Constraint`, `AgentLog`
- `ImpactAnalysis`, `CausalLink`, `TestFailure`
- `SystemHealth`, `SyncQueue`, `DependencyGraph`

---

## 19. CRUD Matrix

| Entity | Create | Read | Update | Delete | Close | Validate |
|---|---|---|---|---|---|---|
| Issues | Modal | Table/Kanban/Graph/Board | Detail Panel | Confirm | Close btn | — |
| Components | Modal | Table/Grid | Modal | Confirm | — | — |
| Policies | Modal | Card Grid | Modal | **Missing in UI** | — | — |
| Constraints | Modal | Table | Modal | Confirm | — | Analyze btn |
| Users (human) | Modal | Card Grid | Modal | Confirm | — | — |
| Users (agent) | **Missing in UI** | Card Grid | Modal | **Missing in UI** | — | — |
| System | — | Dashboard | — | — | — | Seed/Reset |

---

## 20. Interactions Matrix

| Interaction | Location |
|---|---|
| Drag-and-drop | KanbanView |
| Text search | ListView, ComponentsView, ConstraintsView, GraphView |
| Dropdown filters | ListView (status, priority, component), ConstraintsView (category, severity), GraphView (status) |
| View mode toggle | ComponentsView (table/grid) |
| Layout toggle | GraphView (hierarchical/force-directed) |
| Dark mode toggle | UserMenu |
| Language switch | UserMenu (EN/ES) |
| Click-to-detail | List rows, Kanban cards, Graph nodes, Component cards, Constraint rows |
| Slide-in panels | IssueDetailView, Component detail, Constraint detail |
| Modal overlays | Create/Edit forms, Issue detail, User issues modal |
| Confirm dialogs | Delete actions (issues, components, constraints, users, admin reset) |
| SVG chart rendering | TrendChart, DailyActivity, AvgResolution, ImpactSvgTree |
| Graph visualization | GraphView (vis-network) |
| Markdown rendering | IssueDetailView (reasoning/progress), RootCausePanel |
| Validation workflow | ConstraintsView → results banner |
| Admin operations | Seed/Reset with confirmation |
| Pagination | Backend API (page/limit params) |
| Auto-refresh | TeamTicker (10s) |
| Click-outside close | UserMenu, modals |

---

## 21. Known Gaps & Missing Features

### Missing CRUD Operations
- [ ] **Policy delete** — store has `deletePolicy()` but no UI button
- [ ] **Agent creation** — CreateUserModal hardcodes `type: "human"`, no way to create AI agents from UI
- [ ] **Agent deletion** — no delete button for agents in UsersView

### Missing Features
- [ ] **Issue assignment** — no UI to change assignee (field exists in type but not in create/edit forms)
- [ ] **Issue creator** — no way to set `created_by` when creating an issue
- [ ] **Bulk operations** — no multi-select for batch status change, delete, etc.
- [ ] **Issue sorting** — ListView table headers not sortable (no click-to-sort)
- [ ] **Export data** — no CSV/JSON export for issues, components, etc.
- [ ] **Notifications/toasts** — success/error feedback relies on inline messages, no toast system
- [ ] **Responsive mobile layout** — sidebar hover may not work well on touch devices
- [ ] **Keyboard shortcuts** — no global hotkeys (e.g., `N` for new issue, `Esc` to close panels)
- [ ] **URL-based filters** — filter state not synced to URL query params
- [ ] **Issue linking** — no UI to create dependency relationships between issues
- [ ] **Component creation from issue** — no "create component" option inline in CreateIssueModal
- [ ] **Real-time updates** — no WebSocket/SSE for live updates (TeamTicker polls but no push)
- [ ] **User avatars (image)** — only emoji avatars, no upload/custom image support
- [ ] **Issue attachments** — no file upload capability
- [ ] **Activity log / audit trail** — no history of changes per issue
- [ ] **Advanced search** — no date range, label-based, or regex search
- [ ] **Dashboard date range selector** — charts show fixed time windows, no custom range
- [ ] **Graph filtering by component** — can only filter by status, not by component
- [ ] **Agent creation modal** — no dedicated form for creating AI agents with model/specialization
- [ ] **Constraint templates** — no pre-built constraint templates for common rules
