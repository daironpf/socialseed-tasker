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
28. [Known Gaps & Missing Features](#28-known-gaps--missing-features)
29. [Chat System (ChatView)](#29-chat-system-chatview)
30. [Floating Chat Widget (FloatingChat)](#30-floating-chat-widget-floatingchat)

---

## 1. Global Infrastructure

| Feature | Status | Details |
|---|---|---|
| Vue 3.5 + TypeScript | Implemented | Composition API, `<script setup>` |
| Vite 6 build tool | Implemented | HMR, optimized production builds |
| Tailwind CSS 3 | Implemented | Dark mode via `class` strategy |
| Pinia state management | Implemented | 10 stores (auth, issues, components, policies, constraints, users, analysis, ui, notifications, chat) |
| Vue Router | Implemented | 13 routes, lazy-loaded, scroll-to-top |
| i18n (EN/ES) | Implemented | `vue-i18n` with `legacy:false`, 400+ keys per language, localStorage persistence |
| Dark mode | Implemented | Toggle via UserMenu, localStorage persistence, system preference detection, all components dark-mode compatible |
| Mock API mode | Implemented | `USE_MOCK = true` in client.ts, full in-memory routing via mockApi.ts + mock-api server |
| Real API mode | Implemented | Axios client, API key auth via `X-API-Key` header, 401 interceptor |
| Docker deployment | Implemented | Frontend at `:8889`, mock-api at `:8001`, real API at `:8888`, Neo4j at `:7474`/`:7687` |
| Toast notification system | Implemented | Singleton composable `useToast()`, 4 types (success/error/warning/info), auto-dismiss, max 5 concurrent |
| Full i18n coverage | Implemented | All user-visible strings use `t()`, both EN/ES locales in sync |

---

## 2. Authentication

| Feature | Status | Details |
|---|---|---|
| Login screen | Implemented | Full-screen overlay (`LoginScreen.vue`), password input for API key |
| API key storage | Implemented | localStorage persistence via `authStore` |
| Mock mode bypass | Implemented | Auto-authenticated when `USE_MOCK = true` |
| 401 interceptor | Implemented | Dispatches `auth:unauthorized` event, triggers reload |
| Logout | Implemented | Clears API key + full page reload (via UserMenu) |
| Dark mode on login | Implemented | All login buttons have dark mode variants |

---

## 3. Layout & Navigation

### Sidebar
| Feature | Status | Details |
|---|---|---|
| Collapsible sidebar | Implemented | 20px collapsed -> 256px on hover, smooth transition |
| Logo + branding | Implemented | "SocialSeed" text when expanded |
| Navigation groups | Implemented | Principal (4), Management (4), Analysis (2) |
| Active route highlighting | Implemented | Color change on current route |
| Nav icons | Implemented | SVG icons per nav item |
| i18n labels | Implemented | All nav labels use `t()` |
| Chat nav item | Implemented | Chat in Management group with `/chat` route |

### Header (AppHeader)
| Feature | Status | Details |
|---|---|---|
| Dynamic page title | Implemented | Maps route path -> translated title |
| Project selector | Implemented | `ProjectSelector` component, 4 hardcoded projects, localStorage persistence |
| Notification bell | Implemented | `NotificationCenter` component with unread badge |
| UserMenu component | Implemented | Top-right corner |

### UserMenu
| Feature | Status | Details |
|---|---|---|
| Avatar with initials | Implemented | Auto-generated from username |
| Dropdown menu | Implemented | Click to toggle, click-outside to close |
| Dark/Light mode toggle | Implemented | Sun/Moon icons |
| Language selector | Implemented | EN/ES flag buttons, reactive switching |
| Sign out | Implemented | Clears auth + reloads |
| User info display | Implemented | Avatar, username, role (i18n-translated) |

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
| **Avg Resolution Time** | Implemented | Circular SVG gauge, color-coded (green <=3d, blue <=7d, orange <=14d, red >14d), min/max stats |
| **Daily Activity Chart** | Implemented | Custom SVG bar chart, month selector, created vs resolved bars, balance summary, Spanish-localized tooltips |
| **Status Distribution** | Implemented | Horizontal bar chart, 5 statuses, percentage breakdown, total count |
| **Project info bar** | Implemented | Project name, description, active policies count |
| Loading state | Implemented | Spinner while fetching |
| Error state | Implemented | Error message + refresh button |
| Filter reactivity | Implemented | Re-fetches on status/priority/component/project filter changes |
| i18n | Implemented | All labels, tooltips, and chart data translated |

---

## 5. Issues List (ListView)

| Feature | Status | Details |
|---|---|---|
| **Data table** | Implemented | Columns: Checkbox, Title, Status, Priority, Component, Labels (max 2 + overflow), Created, Actions |
| **Select all checkbox** | Implemented | Header checkbox selects/deselects all visible issues |
| **Individual checkboxes** | Implemented | Per-row checkbox for multi-select |
| **Bulk actions bar** | Implemented | Appears when issues selected: status change dropdown, assignee dropdown (humans + agents with AI badge), delete button |
| **Search** | Implemented | Text filter on title, ID, description (client-side) |
| **Status filter** | Implemented | Dropdown: All, OPEN, IN_PROGRESS, BLOCKED, CLOSED |
| **Priority filter** | Implemented | Dropdown: All, CRITICAL, HIGH, MEDIUM, LOW |
| **Component filter** | Implemented | Dynamic dropdown from store |
| **Result count** | Implemented | "Showing X of Y issues" |
| **Row color coding** | Implemented | Left border: red=Critical, orange=High |
| **New Issue button** | Implemented | Opens CreateIssueModal |
| **Export button** | Implemented | CSV/JSON export dropdown with badge labels |
| **Close action** | Implemented | Checkmark icon, hidden if already closed |
| **Delete action** | Implemented | Trash icon, confirm dialog |
| **Click row -> detail** | Implemented | Opens IssueDetailView slide-in panel |
| i18n | Implemented | All labels translated, including bulk actions |

---

## 6. Kanban Board (KanbanView)

| Feature | Status | Details |
|---|---|---|
| **4 status columns** | Implemented | OPEN, IN_PROGRESS, BLOCKED, CLOSED |
| **Column headers** | Implemented | Color-coded titles, issue count badges |
| **Drag-and-drop** | Implemented | IssueCard `draggable="true"`, KanbanColumn drop zones, safe dataTransfer parsing |
| **Priority sorting** | Implemented | CRITICAL > HIGH > MEDIUM > LOW within columns |
| **Status change on drop** | Implemented | Auto-sets `closed_at` when dropping to CLOSED, clears when leaving |
| **New Issue button** | Implemented | Opens CreateIssueModal |
| **Empty state** | Implemented | "No issues" message per column |
| **Click card -> detail** | Implemented | Opens IssueDetailView slide-in panel |
| **Delete from card** | Implemented | Delete icon on IssueCard with confirmation modal |
| **AI agent indicator** | Implemented | Pulsing cyan circle on agent_working issues |
| **i18n** | Implemented | All labels translated via `computed()` |

---

## 7. Issue Detail Panel (IssueDetailView)

| Feature | Status | Details |
|---|---|---|
| **Slide-in panel** | Implemented | Right-side overlay, click-outside to close |
| **Header** | Implemented | Issue ID, AI Agent Active badge (animated), close button |
| **4 tabs** | Implemented | Details, AI Reasoning, Progress, Files |
| **Details tab** | Implemented | Title input, Assignee card (select dropdown with history), Creator card, Description (RichTextEditor), Status select, Priority select, Labels (add/remove with i18n aria-labels), Dependencies list, Created/Updated timestamps |
| **Assignee management** | Implemented | Interactive select dropdown with all users, i18n "Unassigned" label |
| **Assignee history** | Implemented | History section showing assignment timeline with user avatars, dates, and reassignment tracking |
| **Dependency management** | Implemented | Add/remove issue dependencies via RelationshipModal |
| **AI Reasoning tab** | Implemented | Loading state, reasoning logs with MarkdownRenderer, timestamps |
| **Progress tab** | Implemented | Task checklist (i18n "PROGRESS"), Files changed (i18n "FILES"), Technical debt (i18n "DEBT"), MarkdownRenderer |
| **Audit trail** | Implemented | AuditTrail component with 9 mock entries, action-type icons/colors, actor avatars |
| **Agent log stream** | Implemented | Real-time SSE connection via `useAgentStream`, status indicators, auto-scroll, kill switch |
| **HITL approval** | Implemented | HITLApprovalBanner when status is WAITING_HUMAN_APPROVAL, approve/reject/modify actions |
| **Presence indicators** | Implemented | PresenceAvatars showing who's viewing, TypingIndicator for active typers, ConflictWarning for field conflicts |
| **Token metrics** | Implemented | TokenMetrics component showing token consumption, cost, model info |
| **Save** | Implemented | Emits update with full body |
| **Close** | Implemented | Sets closed_at, hidden if already closed |
| **Delete** | Implemented | Confirm dialog |
| **Label management** | Implemented | Add (Enter key), remove (X button with aria-label) |
| **Agent logs** | Implemented | Fetched via `GET /issues/{id}/agent-logs` |
| i18n | Implemented | All labels translated including log type badges and audit descriptions |

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
| i18n | Implemented | All labels translated, icon-only buttons have aria-labels |

---

## 9. Policies Management (PoliciesView)

| Feature | Status | Details |
|---|---|---|
| **Card grid** | Implemented | Responsive 1-3 columns |
| **Policy cards** | Implemented | Name, active/inactive badge, description, target scope, rules count |
| **Create** | Implemented | Modal: Name*, Description, Rule select (4 types), Level (SOFT/HARD), Target Scope |
| **Edit** | Implemented | Same modal + Is Active checkbox |
| **Delete** | Implemented | Confirm dialog with i18n title |
| **Empty state** | Implemented | Icon + message + description |
| i18n | Implemented | All labels translated, icon buttons have aria-labels |

---

## 10. Constraints Management (ConstraintsView)

| Feature | Status | Details |
|---|---|---|
| **Stats row** | Implemented | 4 cards: Total, Hard (red), Soft (amber), Active (green) |
| **Data table** | Implemented | Columns: ID, Name, Category, Severity, Scope, Active, Auto-fix, Actions |
| **Search** | Implemented | Filter by name, ID, description |
| **Category filter** | Implemented | Dropdown: ARCHITECTURE, TECHNOLOGY, NAMING, PATTERNS, DEPENDENCIES |
| **Severity filter** | Implemented | Dropdown: HARD, SOFT (i18n-translated) |
| **Detail panel** | Implemented | Slide-in with severity, name, UUID, category, scope, description, logic, rule JSON, remediation, active/auto-fix badges |
| **Create/Edit** | Implemented | Modal: Name*, Description, Category, Severity, Scope, Auto-fix, Logic, Remediation |
| **Delete** | Implemented | Confirm dialog |
| **Run Validation** | Implemented | Button -> `POST /constraints/validate` -> Results banner |
| **Validation results** | Implemented | Valid/invalid indicator, violation count, individual cards with severity, name, message, remediation, category |
| **Close results panel** | Implemented | X button with i18n aria-label |
| i18n | Implemented | All labels translated |

---

## 11. Users Management (UsersView)

| Feature | Status | Details |
|---|---|---|
| **Stats row** | Implemented | 3 cards: Total Users, Humans (blue), AI Agents (purple) |
| **User cards grid** | Implemented | Responsive 1-4 columns |
| **User cards** | Implemented | Avatar, username, email, type badge, role, model (agents), skills tags, stats, last active timestamp |
| **Stats buttons** | Implemented | Assigned/Created/Completed counts -> opens issues modal |
| **Issues modal** | Implemented | List of user's issues with status/priority badges |
| **Create user** | Implemented | Modal: Username*, Email*, Role, Skills, Avatar picker (11 emojis) |
| **Create agent** | Implemented | Dedicated modal: Username*, Email*, Model select (5 models), Specialization, Skills, Avatar picker (8 robot emojis) |
| **Edit user** | Implemented | Modal: Same fields, pre-filled |
| **Edit agent** | Implemented | Dedicated modal: Same agent-specific fields |
| **Delete user** | Implemented | Human only, confirm dialog |
| **Delete agent** | Implemented | Agent delete button with confirm dialog |
| i18n | Implemented | All labels translated, all icon buttons have aria-labels |

---

## 12. Dependency Graph (GraphView)

| Feature | Status | Details |
|---|---|---|
| **vis-network graph** | Implemented | Nodes = components (purple boxes) + issues (colored dots), Edges = dependency arrows |
| **Color legend** | Implemented | Component, Open, In Progress, Blocked, Closed |
| **Status filter** | Implemented | Dropdown to filter issues by status |
| **Search** | Implemented | Text filter |
| **Component filter** | Implemented | GraphFilters component with checkbox-based component selection |
| **Max hops filter** | Implemented | Slider to limit traversal depth |
| **Layout toggle** | Implemented | Hierarchical (top-down) vs Force Directed (Barnes-Hut) |
| **Graph interactions** | Implemented | Hover, tooltip, zoom, drag, navigation buttons, keyboard |
| **Click node -> detail** | Implemented | Opens IssueDetailView for issue nodes |
| **Connect mode** | Implemented | Create new relationships between issues via click-to-connect |
| **Cycle detection** | Implemented | Prevents creating circular dependencies, shows error toast |
| **Loading state** | Implemented | Spinner |
| **Empty state** | Implemented | Message when no data |
| i18n | Implemented | All labels translated |

---

## 13. Impact & Root Cause Analysis (AnalysisView)

### Impact Analysis (ImpactAnalysisPanel)
| Feature | Status | Details |
|---|---|---|
| **Issue selector** | Implemented | Dropdown of all issues |
| **Analyze button** | Implemented | Triggers BFS analysis |
| **Results display** | Implemented | Issue title, risk level badge (LOW/MEDIUM/HIGH/CRITICAL) |
| **4 stats** | Implemented | Total Affected, Direct Dependencies, Transitive, Cascade Blocked |
| **SVG tree visualization** | Implemented | Custom `ImpactSvgTree` with root node, level-grouped children, color-coded by status, unique SVG IDs |
| **Direct dependencies** | Implemented | Blue cards with status badges |
| **Transitive dependencies** | Implemented | Amber cards with level badges (L2+) |
| **Cascade blocked** | Implemented | Red section with stop icon |
| **Affected components** | Implemented | Purple pill badges |
| **Blast radius slider** | Implemented | `BlastRadiusSlider` with debounced filter, 1-5 hop range |
| **Click node -> re-analyze** | Implemented | Click any node in tree to analyze from that issue |
| Loading state | Implemented | "Running BFS" label |

### Root Cause Analysis (RootCausePanel)
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
| **System health** | Implemented | Neo4j (connected, latency), API (FastAPI version, i18n), Workers (active/queued stats, i18n) |
| **Sync queue** | Implemented | GitHub connected/disconnected, pending items, last sync, queue item list with retry count (i18n) |
| **Constraints summary** | Implemented | Total rules, Active, Inactive |
| **Seed button** | Implemented | `POST /admin/seed` with confirm dialog |
| **Reset button** | Implemented | `POST /admin/reset` with confirm dialog |
| **Success/error messages** | Implemented | Display after admin operations |
| **Refresh button** | Implemented | Re-fetches health + sync queue |
| i18n | Implemented | All labels translated |

---

## 15. User Profile (ProfileView)

| Feature | Status | Details |
|---|---|---|
| **Avatar display** | Implemented | Large circular avatar with initials, camera icon button (aria-labeled) |
| **Personal info form** | Implemented | First name, Last name, Email, Role display, Timezone select |
| **Timezone selector** | Implemented | 7 options: UTC, Eastern, Central, Mountain, Pacific, London, Madrid (all i18n) |
| **Save changes** | Implemented | Saves profile with success toast notification |
| **Change password** | Implemented | Current password, new password, confirm password fields with validation |
| **Password validation** | Implemented | Min 8 chars check, mismatch detection |
| **Notification preferences** | Implemented | Toggle switches for: Email notifications, Push notifications, Agent alerts (all with descriptions) |
| **Success toast** | Implemented | Auto-dismissing green toast after save |
| i18n | Implemented | All labels, roles, timezones translated |

---

## 16. Authentication Screen (LoginScreen)

| Feature | Status | Details |
|---|---|---|
| **Full-screen overlay** | Implemented | Centered card with branding |
| **API key input** | Implemented | Password field with label |
| **Sign in button** | Implemented | Cyan with dark mode variant |
| **Skip button** | Implemented | Gray with dark mode variant (for mock mode) |
| **Error message** | Implemented | Red alert for invalid credentials |
| i18n | Implemented | All labels translated |

---

## 17. Shared UI Components

### Layout Components
| Component | Purpose | Details |
|---|---|---|
| `Sidebar` | Main navigation | Collapsible, 3 sections, i18n labels |
| `AppHeader` | Top bar | Dynamic title, project selector, notifications, user menu |
| `UserMenu` | User dropdown | Avatar, dark mode, language, logout |
| `NavItem` | Sidebar link | Icon + label, active state |

### Board Components
| Component | Purpose | Details |
|---|---|---|
| `IssueCard` | Kanban card | Draggable, status/priority badges, delete icon, AI indicator |
| `KanbanColumn` | Drop zone | Status-specific, drag events, empty state |
| `CreateIssueModal` | Issue creation | Title, component, description (RichTextEditor), priority, labels |

### Dashboard Components
| Component | Purpose | Details |
|---|---|---|
| `StatsCard` | Metric display | Title, value, subtitle, trend, color theme |
| `TrendChart` | Line chart | 8-week SVG, 3 series, legend |
| `DailyActivityChart` | Bar chart | Month selector, created/resolved bars |
| `AvgResolutionTime` | Gauge chart | Circular SVG, color-coded |
| `StatusDistribution` | Horizontal bars | 5 statuses, percentages |
| `DashboardStats` | Stats container | 4 stat cards in grid |
| `TeamTicker` | Bottom marquee | User avatars, auto-refresh |

### Analysis Components
| Component | Purpose | Details |
|---|---|---|
| `ImpactAnalysisPanel` | Impact results | Stats, SVG tree, dependency cards |
| `ImpactSvgTree` | Tree visualization | Custom SVG, color-coded nodes |
| `RootCausePanel` | Root cause results | Test failure form, label toggles, ranked candidates |
| `BlastRadiusSlider` | Depth filter | Debounced, 1-5 hop range |
| `MarkdownRenderer` | Markdown parser | XSS-safe, Mermaid diagrams, dark mode |

### UI Components
| Component | Purpose | Details |
|---|---|---|
| `StatusBadge` | Status pill | Color-coded: Open (blue), In Progress (amber), Closed (green), Blocked (red) |
| `PriorityBadge` | Priority pill | Color-coded: Low (gray), Medium (blue), High (orange), Critical (red) |
| `LabelTag` | Label pill | Gray rounded pill |
| `LoadingSpinner` | Loading indicator | Animated spinning circle |
| `RichTextEditor` | Text input | Slash commands (13 types), preview toggle, markdown formatting |
| `DiffViewer` | Diff display | Unified/split view, copy/download, line-level changes |
| `AuditTrail` | Activity log | Action-type icons/colors, actor avatars, timestamps |
| `AuditEntry` | Single audit item | i18n action labels, color-coded |
| `AgentLogStream` | Real-time logs | SSE connection, auto-scroll, kill switch, status indicator |
| `AgentCostChart` | Token costs | SVG chart of token consumption by model |
| `TokenMetrics` | Token stats | Prompt/completion counts, cost, budget tracking |
| `PresenceAvatars` | User presence | Shows who's viewing an issue |
| `TypingIndicator` | Typing status | Animated dots for active typers |
| `ConflictWarning` | Field conflicts | Warning when multiple users edit same field |
| `HITLApprovalBanner` | Approval UI | Severity badge, approve/reject/modify actions, feedback forms |
| `RelationshipModal` | Dependency creation | Issue search, relationship type selection, cycle detection |
| `BulkActionsBar` | Multi-select actions | Status change, assign, delete for selected issues |
| `NotificationCenter` | Notification panel | Tabs (all/unread/action), mark all read, per-item actions |
| `NotificationItem` | Single notification | Category icon, title, message, time-ago, read/unread styling |
| `ToastContainer` | Toast display | Positioned container for toast messages |
| `ToastItem` | Single toast | Type-colored, auto-dismiss, close button, animation |
| `KeyboardShortcutsHelp` | Shortcuts modal | Lists all registered shortcuts, grouped by scope |
| `CommandPalette` | Quick actions | Search-based navigation, issue/component jump, action triggers |
| `GraphFilters` | Graph filtering | Component checkboxes, status filter |
| `ProjectSelector` | Project switcher | Dropdown with 4 hardcoded projects |

### User Components
| Component | Purpose | Details |
|---|---|---|
| `CreateUserModal` | User creation | Username, email, role, skills, avatar picker |
| `CreateAgentModal` | Agent creation | Username, email, model, specialization, skills, avatar |
| `EditUserModal` | User editing | Same fields, pre-filled |
| `EditAgentModal` | Agent editing | Same agent-specific fields |

### Chat Components
| Component | Purpose | Details |
|---|---|---|
| `ChatView` | Full-page chat | Sidebar + message area, new conversation modal |
| `ChatSidebar` | Conversation list | Search, avatars, online status, unread badges, pin support |
| `ChatMessage` | Message display | Text (markdown), code blocks, agent actions, system pills |
| `ChatInput` | Message input | Textarea with code block insertion, typing indicators |
| `FloatingChat` | Global chat widget | Messenger-style bubble, compact window, all views |

---

## 18. Real-Time & Presence Features

| Feature | Status | Details |
|---|---|---|
| **Agent log streaming** | Implemented | SSE connection via `useAgentStream`, auto-reconnect with exponential backoff (max 5 attempts) |
| **Connection status** | Implemented | 4 states: connecting, connected, disconnected, reconnecting |
| **Auto-scroll** | Implemented | Log stream auto-scrolls to bottom, toggleable |
| **Kill switch** | Implemented | Cancels agent execution, logs cancellation |
| **User presence** | Implemented | `usePresence` composable, tracks viewers per issue |
| **Field-level presence** | Implemented | Shows which field each user is viewing/editing |
| **Typing indicators** | Implemented | Shows when agents are typing |
| **Conflict detection** | Implemented | Warns when multiple users edit the same field |
| **Mock presence generation** | Implemented | Generates realistic mock presence data for demo |
| **Heartbeat system** | Implemented | 30s heartbeat, 60s expiration, per-instance tracking |

---

## 19. Export & Data Features

| Feature | Status | Details |
|---|---|---|
| **CSV export** | Implemented | `useExport().exportCSV()`, proper escaping |
| **JSON export** | Implemented | `useExport().exportJSON()`, pretty-printed |
| **SVG export** | Implemented | `useExport().exportSVG()`, serializes SVG element |
| **PNG export** | Implemented | `useExport().exportPNG()`, 2x scale canvas rendering |
| **Markdown export** | Implemented | `useExport().exportMarkdown()`, downloads text file |
| **Export UI** | Implemented | ListView export dropdown with CSV/JSON badges |
| **Data persistence** | Implemented | Mock data served from `dataset-de-pruebas/` volume-mounted into mock-api |
| **Assignee history** | Implemented | Backfilled for all 100 issues, tracked in issue type and displayed in IssueDetailView |

---

## 20. Keyboard Shortcuts & Command Palette

### Keyboard Shortcuts (`useKeyboardShortcuts`)
| Feature | Status | Details |
|---|---|---|
| **Global listener** | Implemented | `initKeyboardShortcuts()` attaches keydown handler |
| **Sequence support** | Implemented | Multi-key sequences (e.g., `g` then `l`), 1000ms timeout |
| **Modifier matching** | Implemented | Ctrl, Shift, Alt, Meta support |
| **Input field detection** | Implemented | Skips shortcuts when focused in input/textarea |
| **Scope system** | Implemented | `global` and `local` scopes |
| **Registration API** | Implemented | `register()`, `unregister()`, `unregisterAll()` |

### Registered Shortcuts
| Shortcut | Action | Scope |
|---|---|---|
| `N` | Create new issue | Global |
| `G L` | Go to Issues list | Global |
| `G K` | Go to Kanban board | Global |
| `G D` | Go to Dashboard | Global |
| `G G` | Go to Graph | Global |
| `G U` | Go to Users | Global |
| `G C` | Go to Components | Global |
| `Ctrl+K` | Open command palette | Global |
| `J` / `K` | Next/Previous item | Local |
| `Enter` | Open detail | Local |
| `Esc` | Close panel | Local |
| `?` | Show shortcuts help | Global |
| `D` | Toggle dark mode | Global |

### Command Palette (`CommandPalette`)
| Feature | Status | Details |
|---|---|---|
| **Search input** | Implemented | Fuzzy search across pages, actions, issues, components |
| **Page navigation** | Implemented | Jump to any page (Dashboard, Issues, Kanban, Graph, etc.) |
| **Actions** | Implemented | Create issue, toggle dark mode, toggle sidebar, clear filters |
| **Issue search** | Implemented | Search by ID/title, opens detail panel |
| **Component search** | Implemented | Search by name, opens detail panel |
| **Keyboard navigation** | Implemented | Arrow keys, Enter to select, Esc to close |
| **i18n** | Implemented | All labels translated |

---

## 21. Notifications System

| Feature | Status | Details |
|---|---|---|
| **Notification store** | Implemented | `notificationsStore` with localStorage persistence, versioned seed (SEED_VERSION = 2) |
| **Mock data** | Implemented | 12 realistic notifications across 4 categories |
| **Categories** | Implemented | Mention, HITL, Constraint Violation, Agent Failure (each with icon/color) |
| **Read/unread state** | Implemented | Per-notification, visual distinction |
| **Requires action** | Implemented | Amber ACTION badge on actionable notifications |
| **Mark as read** | Implemented | Click notification to mark read |
| **Mark all read** | Implemented | Button in header |
| **Dismiss** | Implemented | Remove individual notifications |
| **Filtering** | Implemented | Tabs: All, Unread, Requires Action |
| **Unread count** | Implemented | Badge on notification bell |
| **Time-ago display** | Implemented | i18n-computed relative time (just now, Xm ago, Xh ago, Xd ago) |
| **Click-through** | Implemented | Navigate to linked issue |
| **NotificationCenter** | Implemented | Teleported dropdown with click-outside close |

---

## 22. Data Layer (Stores)

| Store | State | Computed | Actions |
|---|---|---|---|
| `authStore` | storedKey | isAuthenticated | setApiKey, clearApiKey, getApiKey |
| `issuesStore` | issues[], pagination, loading, error | openIssuesCount, blockedIssuesCount | fetchIssues, fetchIssue, createIssue, updateIssue, deleteIssue, closeIssue, fetchBlockedIssues |
| `componentsStore` | components[], loading, error | projects | fetchComponents, fetchComponent, createComponent, updateComponent, deleteComponent, getComponentById, componentsByProject |
| `policiesStore` | policies[], loading, error | activeCount, inactiveCount | fetchPolicies, createPolicy, updatePolicy, deletePolicy |
| `constraintsStore` | constraints[], loading, error, validationResult | hardCount, softCount, activeCount | fetchConstraints, createConstraint, updateConstraint, deleteConstraint, validateConstraints, byCategory, bySeverity |
| `usersStore` | users[], loading, error | humans, agents, activeAgents | fetchUsers, updateUser, createUser, deleteUser |
| `analysisStore` | impactResult, rootCauseResults[], testFailures[], loadingImpact, loadingRootCause, error | — | analyzeImpact, analyzeRootCause, fetchTestFailures, clearResults |
| `uiStore` | selectedIssueId, sidebarOpen, viewMode, darkMode, locale, currentProject, filters, availableProjects | — | setSelectedIssue, toggleSidebar, setViewMode, setFilter, clearFilters, toggleDarkMode, initDarkMode, setLocale, setProject, getBackendFilters |
| `notificationsStore` | notifications[] | unreadCount, unreadByCategory | addNotification, markAsRead, markAllAsRead, dismiss, getFiltered, seedMockNotifications |
| `chatStore` | conversations[], activeConversationId, searchQuery, typingUsers[] | activeConversation, activeMessages, filteredConversations, totalUnread | selectConversation, sendMessage, togglePin, markAsRead, createConversation, simulateAgentResponse |

---

## 23. API Layer

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
| `useAgentStream` | `/issues/{id}/agent-logs/stream` | SSE |

### Mock API (`mockApi.ts`)
All endpoints routed through `/mock-api/mock/*` prefix, delegating to mock-api server with dataset-de-pruebas volume mount.

---

## 24. Type System

### Enums
- `IssueStatus`: OPEN, IN_PROGRESS, CLOSED, BLOCKED, WAITING_HUMAN_APPROVAL
- `IssuePriority`: LOW, MEDIUM, HIGH, CRITICAL

### Type Aliases
- `ConstraintCategory`: ARCHITECTURE, TECHNOLOGY, NAMING, PATTERNS, DEPENDENCIES
- `ConstraintSeverity`: HARD, SOFT
- `AuditAction`: status, priority, assignment, agent, system, hitl, comment, label
- `NotificationCategory`: mention, hitl, constraint_violation, agent_failure

### Core Entities (26 interfaces)
- `Issue`, `Component`, `User`, `Policy`, `Constraint`, `AgentLog`
- `ImpactAnalysis`, `CausalLink`, `TestFailure`, `DependencyGraph`
- `SystemHealth`, `SyncQueue`, `ServiceStatus`, `SyncQueueItem`
- `AssigneeHistoryEntry`, `AuditEntry`, `AppNotification`
- `ValidationResult`, `ConstraintViolation`, `ConstraintRule`
- `PaginatedResponse<T>`, `PaginationMeta`, `APIResponse<T>`
- `IssueCreateRequest`, `IssueUpdateRequest`, `DependencyRequest`
- `ComponentCreateRequest`, `PolicyCreateRequest`, `UserCreateRequest`
- `ChatMessage`, `Conversation`, `ChatParticipant`, `TypingUser`

---

## 25. CRUD Matrix

| Entity | Create | Read | Update | Delete | Close | Validate | Export |
|---|---|---|---|---|---|---|---|
| Issues | Modal | Table/Kanban/Graph/Board | Detail Panel | Confirm | Close btn | — | CSV/JSON |
| Components | Modal | Table/Grid | Detail Panel | Confirm | — | — | — |
| Policies | Modal | Card Grid | Modal | Confirm | — | — | — |
| Constraints | Modal | Table | Modal | Confirm | — | Analyze btn | — |
| Users (human) | Modal | Card Grid | Modal | Confirm | — | — | — |
| Users (agent) | Modal | Card Grid | Modal | Confirm | — | — | — |
| System | — | Dashboard | — | — | — | Seed/Reset | — |
| Notifications | — | Panel | Mark read | Dismiss | — | — | — |
| Conversations | Modal | ChatView / FloatingChat | — | — | — | — | — |
| Messages | Input | Chat bubbles | — | — | — | — | — |

---

## 26. Interactions Matrix

| Interaction | Location |
|---|---|
| Drag-and-drop | KanbanView |
| Text search | ListView, ComponentsView, ConstraintsView, GraphView, CommandPalette |
| Dropdown filters | ListView (status, priority, component), ConstraintsView (category, severity), GraphView (status, component, max hops) |
| View mode toggle | ComponentsView (table/grid) |
| Layout toggle | GraphView (hierarchical/force-directed) |
| Dark mode toggle | UserMenu, KeyboardShortcut (D), CommandPalette |
| Language switch | UserMenu (EN/ES) |
| Click-to-detail | List rows, Kanban cards, Graph nodes, Component cards, Constraint rows, Notification items |
| Slide-in panels | IssueDetailView, Component detail, Constraint detail |
| Modal overlays | Create/Edit forms, Issue detail, User issues modal, Relationship modal, Command palette, Keyboard shortcuts help |
| Confirm dialogs | Delete actions (issues, components, constraints, policies, users, admin reset, Kanban card delete) |
| SVG chart rendering | TrendChart, DailyActivity, AvgResolution, ImpactSvgTree, AgentCostChart |
| Graph visualization | GraphView (vis-network) |
| Markdown rendering | IssueDetailView (reasoning/progress), RichTextEditor preview, RootCausePanel |
| Validation workflow | ConstraintsView -> results banner |
| Admin operations | Seed/Reset with confirmation |
| Pagination | Backend API (page/limit params) |
| Auto-refresh | TeamTicker (10s) |
| Click-outside close | UserMenu, modals, NotificationCenter, ProjectSelector, CommandPalette |
| Slash commands | RichTextEditor (/ prefix, 13 command types) |
| Keyboard shortcuts | Global hotkeys, sequences, scoped shortcuts |
| Bulk operations | ListView multi-select with bulk actions bar |
| Export dropdown | ListView CSV/JSON export |
| Toast notifications | useToast composable, 4 types, auto-dismiss |
| Real-time streaming | Agent log SSE with auto-reconnect |
| Presence tracking | Per-issue viewer tracking, field-level presence |
| Conflict detection | Multi-user edit detection |
| Relationship creation | GraphView connect mode with cycle detection |
| Real-time chat | ChatView message exchange, agent auto-responses, typing indicators |
| Floating chat | Persistent Messenger-style widget, expand/collapse, conversation switching |
| Chat search | Filter conversations by name/participant |
| Chat pin/unpin | Pin conversations to top of list |
| Code sharing | Triple-backtick code blocks in chat messages |
| Agent messaging | Direct communication with AI agents via chat |

---

## 27. i18n Coverage

### Locale Files
- `en.json`: 700+ lines, 37 top-level sections
- `es.json`: 700+ lines, matching structure

### Sections
`kanban`, `nav`, `header`, `menu`, `dashboard`, `issues`, `components`, `policies`, `constraints`, `users`, `graph`, `analysis`, `system`, `auth`, `common`, `dashboardStats`, `trendChart`, `statusDistribution`, `dailyActivity`, `avgResolution`, `statsCard`, `shortcuts`, `palette`, `editor`, `diff`, `hitl`, `audit`, `stream`, `tokens`, `notifications`, `agents`, `toast`, `presence`, `projects`, `export`, `bulkActions`, `profile`, `commandPalette`, `chat`, `floatingChat`

### Coverage
- All user-visible text uses `t()` function
- All form labels, placeholders, and error messages translated
- All button text and aria-labels translated
- All status/priority/type labels translated
- Time-ago strings computed with i18n
- Audit trail descriptions use parameterized i18n
- Slash command labels translated
- Toast messages translated
- Chat labels translated (conversation names, placeholders, typing indicators, time-ago)
- Floating chat labels translated (active status, search, send, like, emoji)

---

## 28. Known Gaps & Missing Features

### Missing Features
- [ ] **Real-time updates** — No WebSocket/SSE for live updates beyond agent logs and chat (TeamTicker polls but no push)
- [ ] **URL-based filters** — Filter state not synced to URL query params
- [ ] **Responsive mobile layout** — Sidebar hover may not work well on touch devices
- [ ] **Issue attachments** — No file upload capability
- [ ] **Advanced search** — No date range, label-based, or regex search
- [ ] **Dashboard date range selector** — Charts show fixed time windows, no custom range
- [ ] **Constraint templates** — No pre-built constraint templates for common rules
- [ ] **Chat persistence** — Chat messages are mock-only, not persisted to backend
- [ ] **Chat file sharing** — No image/file upload in chat messages
- [ ] **Chat emoji picker** — Emoji button present but no picker implemented
- [ ] **Chat message reactions** — Reaction data supported in types but not rendered in FloatingChat

### Technical Debt
- [ ] **3 `window as any` assertions** — client.ts and useAgentStream.ts use `window.__API_URL__` / `window.__API_KEY__` without type augmentation
- [ ] **1 `status as any` in ListView** — Type mismatch between string param and `IssueStatus` enum
- [ ] **4 minor `setTimeout` without cleanup** — ProfileView, GraphView (fixed), DiffViewer (fixed), RichTextEditor onBlur (200ms, acceptable)
- [ ] **Dashboard chart overlap** — `dashboard` and `dashboardStats` i18n sections have duplicated keys
- [ ] **Duplicate i18n sections** — `audit` appears twice in en.json/es.json (audit trail + audit descriptions)

---

## 29. Chat System (ChatView)

Full-featured messaging interface for direct communication between users and AI agents.

| Feature | Status | Details |
|---|---|---|
| **Full-page layout** | Implemented | Sidebar (conversation list) + main area (messages + input), routed at `/chat` |
| **3 conversation types** | Implemented | Direct (1:1), Group (multi-user), Agent (user-to-AI) |
| **Mock conversations** | Implemented | 7 conversations with 40+ messages seeded in chatStore |
| **Search** | Implemented | Filter conversations by name, description, or participant |
| **Pin/unpin** | Implemented | Pin conversations to top of list |
| **Unread badges** | Implemented | Per-conversation unread count, total unread in header |
| **Online status** | Implemented | Green dot on avatars for online users |
| **New conversation modal** | Implemented | Select type, name, participants from user list |
| **Message types** | Implemented | Text (with markdown), code blocks, agent actions, system notifications |
| **Date separators** | Implemented | Grouped by day between messages |
| **Typing indicators** | Implemented | Animated bouncing dots when agent is typing |
| **Agent auto-responses** | Implemented | Arch-Bot, CodeReviewer, SecurityAuditor respond with 1.5-3.5s delay |
| **Markdown rendering** | Implemented | Bold, italic, inline code in message bubbles |
| **Code block insertion** | Implemented | Triple-backtick syntax via toolbar button |
| **Dark mode** | Implemented | All components fully dark-mode compatible |
| **i18n** | Implemented | 35 keys in EN/ES (chat.* namespace) |
| **Navigation** | Implemented | Sidebar item (Management group), AppHeader title mapping |

---

## 30. Floating Chat Widget (FloatingChat)

Persistent Messenger-style chat bubble available on all views, enabling messaging without leaving current context.

| Feature | Status | Details |
|---|---|---|
| **Global presence** | Implemented | Mounted in `App.vue`, visible on every route |
| **Messenger-style bubble** | Implemented | 56px blue circle with Messenger lightning bolt icon |
| **Unread badge** | Implemented | Red badge on bubble showing total unread count |
| **330px compact window** | Implemented | Messenger-proportioned popup with rounded corners |
| **Smooth animations** | Implemented | Scale + fade open/close transitions |
| **Messenger header** | Implemented | Avatar (with online dot), name, "Active now", back/minimize/close buttons |
| **Conversation list** | Implemented | Large avatars (48px), name, last message preview, timestamp, unread badge |
| **Pill search** | Implemented | Rounded search input with gray background |
| **Bubble messages** | Implemented | Own messages right (blue bg, rounded-br), others left (gray bg, rounded-bl) |
| **Avatar grouping** | Implemented | Avatar shown only on first message in a group (Messenger pattern) |
| **Message timestamps** | Implemented | Time shown under message groups |
| **Code blocks** | Implemented | Dark background code blocks inside bubbles with language label |
| **System messages** | Implemented | Centered pill-style notifications |
| **Agent actions** | Implemented | Centered purple pill with lightning icon |
| **Typing indicator** | Implemented | Animated bouncing dots in conversation view |
| **Input bar** | Implemented | Emoji icon + rounded pill textarea + send arrow / like thumbs-up |
| **Auto-resize input** | Implemented | Textarea grows up to 60px as user types |
| **Code block insertion** | Implemented | Triple-backtick syntax support |
| **Online status** | Implemented | Green dots on avatars in list and header |
| **Minimize** | Implemented | Collapses to header-only (48px) |
| **Full chat link** | Implemented | "Open Messenger" link navigates to `/chat` |
| **Back navigation** | Implemented | Arrow button returns to conversation list |
| **Dark mode** | Implemented | Full dark mode on all elements |
| **i18n** | Implemented | 17 keys in EN/ES (floatingChat.* namespace) |
