# SocialSeed Tasker - Frontend Feature Inventory

> Complete catalog of all UI features, interactions, and capabilities currently implemented.
> Use this document to identify gaps, plan new features, and track what is missing.
> Last updated: 2026-09-20

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
40. [Known Gaps & Missing Features](#40-known-gaps--missing-features)

---

## 1. Global Infrastructure

| Feature | Status | Details |
|---|---|---|
| Vue 3.5 + TypeScript | Implemented | Composition API, `<script setup>` |
| Vite 6 build tool | Implemented | HMR, optimized production builds |
| Tailwind CSS 3 | Implemented | Dark mode via `class` strategy |
| Pinia state management | Implemented | 19 stores |
| Vue Router | Implemented | 22 routes + redirect + catch-all, lazy-loaded, scroll-to-top |
| i18n (EN/ES) | Implemented | `vue-i18n` with `legacy:false`, 1000+ keys per language, localStorage persistence |
| Dark mode | Implemented | Toggle via UserMenu, localStorage persistence, system preference detection |
| Mock API mode | Implemented | `USE_MOCK = true` in client.ts, full in-memory routing via mockApi.ts |
| Real API mode | Implemented | Axios client, API key auth via `X-API-Key` header, 401 interceptor |
| Docker deployment | Implemented | Frontend at `:8889`, mock-api at `:8001`, real API at `:8888`, Neo4j at `:7474`/`:7687` |
| Toast notification system | Implemented | Singleton composable `useToast()`, 4 types (success/error/warning/info), auto-dismiss, max 5 concurrent |
| html2canvas + jspdf | Implemented | PDF/PNG export for executive dashboard |
| Mermaid diagrams | Implemented | MarkdownRenderer renders Mermaid syntax in agent reasoning logs |
| vis-network | Implemented | Graph visualization library for dependency graph |

---

## 2. Authentication

| Feature | Status | Details |
|---|---|---|
| Login screen | Implemented | Full-screen overlay (`LoginScreen.vue`), password input for API key |
| API key storage | Implemented | localStorage persistence via `authStore` |
| Mock mode bypass | Implemented | Auto-authenticated when `USE_MOCK = true` |
| 401 interceptor | Implemented | Dispatches `auth:unauthorized` event, triggers reload |
| Logout | Implemented | Clears API key + full page reload (via UserMenu) |

---

## 3. Layout & Navigation

### Sidebar
| Feature | Status | Details |
|---|---|---|
| Collapsible sidebar | Implemented | 20px collapsed -> 64px on hover, smooth transition |
| Logo + branding | Implemented | "SocialSeed" text when expanded |
| Navigation groups | Implemented | Principal (4), Management (13), Analysis (2) = 19 total nav items |
| Active route highlighting | Implemented | Color change on current route |
| Nav icons | Implemented | SVG icons per nav item |
| i18n labels | Implemented | All nav labels use `t()` |

### Header (AppHeader)
| Feature | Status | Details |
|---|---|---|
| Dynamic page title | Implemented | Maps route path -> translated title (22 routes) |
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
| Profile link | Implemented | Navigates to `/profile` |

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
| **Avg Resolution Time** | Implemented | Circular SVG gauge, color-coded (green <=3d, blue <=7d, orange <=14d, red >14d) |
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
| **Select all** | Implemented | Header checkbox selects/deselects all visible issues |
| **Bulk actions bar** | Implemented | Status change dropdown, assignee dropdown (humans + agents with AI badge), delete button |
| **Search** | Implemented | Text filter on title, ID, description (client-side) |
| **Status filter** | Implemented | Dropdown: All, OPEN, IN_PROGRESS, BLOCKED, CLOSED |
| **Priority filter** | Implemented | Dropdown: All, CRITICAL, HIGH, MEDIUM, LOW |
| **Component filter** | Implemented | Dynamic dropdown from store |
| **New Issue button** | Implemented | Opens CreateIssueModal |
| **Export button** | Implemented | CSV/JSON export dropdown |
| **Click row -> detail** | Implemented | Opens IssueDetailView slide-in panel |
| i18n | Implemented | All labels translated |

---

## 6. Kanban Board (KanbanView)

| Feature | Status | Details |
|---|---|---|
| **4 status columns** | Implemented | OPEN, IN_PROGRESS, BLOCKED, CLOSED |
| **Drag-and-drop** | Implemented | IssueCard draggable, KanbanColumn drop zones |
| **Priority sorting** | Implemented | CRITICAL > HIGH > MEDIUM > LOW within columns |
| **Status change on drop** | Implemented | Auto-sets `closed_at` when dropping to CLOSED |
| **New Issue button** | Implemented | Opens CreateIssueModal |
| **Click card -> detail** | Implemented | Opens IssueDetailView slide-in panel |
| **AI agent indicator** | Implemented | Pulsing cyan circle on agent_working issues |
| i18n | Implemented | All labels translated |

---

## 7. Issue Detail Panel (IssueDetailView)

| Feature | Status | Details |
|---|---|---|
| **Slide-in panel** | Implemented | Right-side overlay, click-outside to close |
| **4 tabs** | Implemented | Details, AI Reasoning, Progress, Files |
| **Details tab** | Implemented | Title, Assignee, Creator, Description (RichTextEditor), Status, Priority, Labels, Dependencies, Timestamps |
| **Assignee management** | Implemented | Interactive select with all users, i18n "Unassigned" |
| **Assignee history** | Implemented | Timeline with user avatars, dates, reassignment tracking |
| **Dependency management** | Implemented | Add/remove via RelationshipModal |
| **AI Reasoning tab** | Implemented | Loading state, reasoning logs with MarkdownRenderer, timestamps |
| **Progress tab** | Implemented | Task checklist, Files changed, Technical debt |
| **Audit trail** | Implemented | 9 mock entries, action-type icons/colors, actor avatars |
| **Agent log stream** | Implemented | Real-time SSE via `useAgentStream`, status indicators, auto-scroll, kill switch |
| **HITL approval** | Implemented | HITLApprovalBanner when status is WAITING_HUMAN_APPROVAL |
| **Presence indicators** | Implemented | PresenceAvatars, TypingIndicator, ConflictWarning |
| **Token metrics** | Implemented | TokenMetrics showing consumption, cost, model info |
| i18n | Implemented | All labels translated |

---

## 8. Components Management (ComponentsView)

| Feature | Status | Details |
|---|---|---|
| **Table/Grid views** | Implemented | Toggle between table and card grid |
| **Search** | Implemented | Filter by name, alias, ID |
| **Detail panel** | Implemented | Slide-in with alias, name, UUID, description, status breakdown, issue list |
| **Create/Edit** | Implemented | Modal: Alias (4 chars), Name*, Description, Project |
| **Delete** | Implemented | Confirm dialog |
| i18n | Implemented | All labels translated |

---

## 9. Policies Management (PoliciesView)

| Feature | Status | Details |
|---|---|---|
| **Card grid** | Implemented | Responsive 1-3 columns |
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
| **Search + filters** | Implemented | Search by name/ID, filter by category and severity |
| **Detail panel** | Implemented | Slide-in with all constraint details |
| **Create/Edit** | Implemented | Modal with all fields |
| **Delete** | Implemented | Confirm dialog |
| **Run Validation** | Implemented | Button -> results banner with violation cards |
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
| **Delete** | Implemented | Confirm dialog for both users and agents |
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
| **Click node -> detail** | Implemented | Opens IssueDetailView for issue nodes |
| **Connect mode** | Implemented | Create new relationships via click-to-connect |
| **Cycle detection** | Implemented | Prevents circular dependencies |
| **Code Overlay toggle** | Implemented | Show/hide AST code nodes (File/Class/Function) alongside issue nodes |
| **Code node rendering** | Implemented | Files (cyan/database), Classes (teal/diamond), Functions (emerald/triangle) |
| **Code node detail** | Implemented | Click code node shows file path, language, lines, type |
| i18n | Implemented | All labels translated |

---

## 13. Impact & Root Cause Analysis (AnalysisView)

### Impact Analysis (ImpactAnalysisPanel)
| Feature | Status | Details |
|---|---|---|
| **Issue selector** | Implemented | Dropdown of all issues |
| **SVG tree visualization** | Implemented | Custom `ImpactSvgTree` with root node, level-grouped children, color-coded |
| **4 stats** | Implemented | Total Affected, Direct Dependencies, Transitive, Cascade Blocked |
| **Blast radius slider** | Implemented | `BlastRadiusSlider` with debounced filter, 1-5 hop range |
| **Click node -> re-analyze** | Implemented | Click any node to analyze from that issue |

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
| **Change password** | Implemented | Current, new, confirm password with validation |
| **Notification preferences** | Implemented | Toggle switches for Email, Push, Agent alerts |
| **Save changes** | Implemented | Saves with success toast notification |
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
| `Sidebar` | Main navigation | Collapsible, 3 groups, 19 nav items, i18n labels |
| `AppHeader` | Top bar | Dynamic title (22 routes), project selector, notifications, user menu |
| `UserMenu` | User dropdown | Avatar, dark mode, language, logout, profile link |
| `NavItem` | Sidebar link | Icon + label, active state, badge |

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
| `StatusBadge` | Status pill | Color-coded |
| `PriorityBadge` | Priority pill | Color-coded |
| `LabelTag` | Label pill | Gray rounded pill |
| `LoadingSpinner` | Loading indicator | Animated spinning circle |
| `RichTextEditor` | Text input | Slash commands (13 types), preview toggle |
| `DiffViewer` | Diff display | Unified/split view, copy/download |
| `AuditTrail` | Activity log | Action-type icons/colors, actor avatars |
| `AgentLogStream` | Real-time logs | SSE connection, auto-scroll, kill switch |
| `AgentCostChart` | Token costs | SVG chart of token consumption by model |
| `TokenMetrics` | Token stats | Prompt/completion counts, cost, budget tracking |
| `PresenceAvatars` | User presence | Shows who's viewing an issue |
| `TypingIndicator` | Typing status | Animated dots for active typers |
| `ConflictWarning` | Field conflicts | Warning when multiple users edit same field |
| `HITLApprovalBanner` | Approval UI | Severity badge, approve/reject/modify actions |
| `RelationshipModal` | Dependency creation | Issue search, relationship type, cycle detection |
| `BulkActionsBar` | Multi-select actions | Status change, assign, delete |
| `NotificationCenter` | Notification panel | Tabs (all/unread/action), mark all read |
| `ToastContainer/Item` | Toast display | Type-colored, auto-dismiss, animation |
| `KeyboardShortcutsHelp` | Shortcuts modal | Lists all registered shortcuts |
| `CommandPalette` | Quick actions | Search-based navigation, issue/component jump |
| `GraphFilters` | Graph filtering | Component checkboxes, status filter |
| `ProjectSelector` | Project switcher | Dropdown with 4 projects |

### Chat Components
| Component | Purpose | Details |
|---|---|---|
| `ChatView` | Full-page chat | Sidebar + message area, new conversation modal |
| `ChatSidebar` | Conversation list | Search, avatars, online status, unread badges, pin |
| `ChatMessage` | Message display | Text (markdown), code blocks, agent actions, reactions |
| `ChatInput` | Message input | PII detection, code block insertion, typing indicators |
| `PIIDetectionBanner` | PII warnings | Inline detection banner with severity colors |
| `PIIWarningModal` | PII blocking | Modal: Cancel / Mask & Send / Send Anyway |
| `FloatingChat` | Global chat widget | Messenger-style bubble, compact window, all views |

### Sandbox Components
| Component | Purpose | Details |
|---|---|---|
| `ImpactReport` | Simulation results | Pass/fail, violation details with severity, promote button |

### User Components
| Component | Purpose | Details |
|---|---|---|
| `CreateUserModal` | User creation | Username, email, role, skills, avatar picker |
| `CreateAgentModal` | Agent creation | Username, email, model, specialization, skills, avatar |
| `EditUserModal` | User editing | Same fields, pre-filled |
| `EditAgentModal` | Agent editing | Model, temperature, system prompt, tools, folder permissions |

---

## 18. Real-Time & Presence Features

| Feature | Status | Details |
|---|---|---|
| **Agent log streaming** | Implemented | SSE via `useAgentStream`, auto-reconnect with exponential backoff |
| **Connection status** | Implemented | 4 states: connecting, connected, disconnected, reconnecting |
| **Auto-scroll** | Implemented | Log stream auto-scrolls to bottom, toggleable |
| **Kill switch** | Implemented | Cancels agent execution |
| **User presence** | Implemented | `usePresence` composable, tracks viewers per issue |
| **Field-level presence** | Implemented | Shows which field each user is viewing/editing |
| **Typing indicators** | Implemented | Shows when agents are typing |
| **Conflict detection** | Implemented | Warns when multiple users edit the same field |
| **Mock presence generation** | Implemented | Generates realistic mock presence data for demo |

---

## 19. Export & Data Features

| Feature | Status | Details |
|---|---|---|
| **CSV export** | Implemented | `useExport().exportCSV()`, proper escaping |
| **JSON export** | Implemented | `useExport().exportJSON()`, pretty-printed |
| **SVG export** | Implemented | `useExport().exportSVG()`, serializes SVG element |
| **PNG export** | Implemented | `useExport().exportPNG()`, 2x scale canvas rendering |
| **Markdown export** | Implemented | `useExport().exportMarkdown()`, downloads text file |
| **PDF export** | Implemented | Executive dashboard via html2canvas + jspdf |
| **PNG export (dashboard)** | Implemented | Executive dashboard via html2canvas |
| **Data persistence** | Implemented | Mock data served from `dataset-de-pruebas/` volume-mounted into mock-api |
| **Assignee history** | Implemented | Backfilled for all 100 issues, tracked and displayed in IssueDetailView |

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
| **Page navigation** | Implemented | Jump to any page (22 routes) |
| **Actions** | Implemented | Create issue, toggle dark mode, toggle sidebar, clear filters |
| **Issue/Component search** | Implemented | Search by ID/title or name, opens detail panel |
| **Keyboard navigation** | Implemented | Arrow keys, Enter to select, Esc to close |
| i18n | Implemented | All labels translated |

---

## 21. Notifications System

| Feature | Status | Details |
|---|---|---|
| **Notification store** | Implemented | `notificationsStore` with localStorage persistence |
| **Mock data** | Implemented | 12 realistic notifications across 4 categories |
| **Categories** | Implemented | Mention, HITL, Constraint Violation, Agent Failure |
| **Read/unread state** | Implemented | Per-notification, visual distinction |
| **Requires action** | Implemented | Amber ACTION badge on actionable notifications |
| **Mark as read** | Implemented | Click notification to mark read |
| **Mark all read** | Implemented | Button in header |
| **Dismiss** | Implemented | Remove individual notifications |
| **Filtering** | Implemented | Tabs: All, Unread, Requires Action |
| **Unread count** | Implemented | Badge on notification bell |
| **Time-ago display** | Implemented | i18n-computed relative time |
| **Click-through** | Implemented | Navigate to linked issue |
| **NotificationCenter** | Implemented | Teleported dropdown with click-outside close |

---

## 22. Data Layer (Stores)

| Store | State | Key Actions |
|---|---|---|
| `authStore` | storedKey, isAuthenticated | setApiKey, clearApiKey |
| `uiStore` | darkMode, locale, sidebarExpanded, selectedProject, filters | toggleDarkMode, setLocale, toggleSidebar, clearFilters |
| `issuesStore` | issues[], pagination, loading, selectedIssue | fetchIssues, createIssue, updateIssue, deleteIssue, closeIssue |
| `componentsStore` | components[], loading | fetchComponents, createComponent, updateComponent, deleteComponent |
| `usersStore` | users[], loading | fetchUsers, createUser, updateUser, deleteUser |
| `policiesStore` | policies[], loading | fetchPolicies, createPolicy, updatePolicy, deletePolicy |
| `constraintsStore` | constraints[], loading, validationResult | fetchConstraints, createConstraint, updateConstraint, validateConstraints |
| `analysisStore` | impactResult, rootCauseResults[], testFailures[] | analyzeImpact, analyzeRootCause, fetchTestFailures |
| `notificationsStore` | notifications[], unreadCount | markAsRead, markAllAsRead, dismiss, getFiltered |
| `chatStore` | conversations[], activeConversationId, typingUsers[] | selectConversation, sendMessage, togglePin, createConversation |
| `sandboxStore` | rules[], selectedRule, simulationResult | Mock CRUD + simulation |
| `ragStore` | searchResults[], queryStats | Mock search, getContext |
| `mcpStore` | sessions[], selectedSession, isStreaming | Mock MCP session management |
| `hitlStore` | requests[], selectedRequest | Mock HITL approval workflow |
| `finopsStore` | models[], components[], tasks[], roi[], alerts[], caps[] | updateCap, toggleCap |
| `executiveStore` | kpis[], cycleTime[], debt[], compliance[] | formatTrend, complianceColor |
| `autoHealingStore` | runs[], logs[], fixAttempts[], selectedRunId | selectRun, stageColor, formatDuration |
| `agentReplayStore` | sessions[], currentTime, isPlaying, playSpeed | play, pause, stepForward, stepBackward, seekTo |
| `codeGraphStore` | nodes[], edges[] | Mock code graph data |

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
- `IssueStatus`: OPEN, IN_PROGRESS, BLOCKED, CLOSED
- `IssuePriority`: LOW, MEDIUM, HIGH, CRITICAL

### Type Aliases
- `ConstraintCategory`: ARCHITECTURE, TECHNOLOGY, NAMING, PATTERNS, DEPENDENCIES
- `ConstraintSeverity`: HARD, SOFT

### Core Entities (index.ts)
- `Issue`, `IssueCreateRequest`, `IssueUpdateRequest`
- `Component`, `ComponentCreateRequest`
- `Policy`, `PolicyCreateRequest`
- `User`, `UserCreateRequest`
- `AgentLog`, `AgentLogsBundle`
- `Constraint`, `ConstraintCreateRequest`, `ValidationResult`
- `SystemHealth`, `SyncQueue`, `ServiceStatus`, `SyncQueueItem`
- `ImpactAnalysis`, `CausalLink`, `TestFailure`
- `APIResponse<T>`, `PaginatedResponse<T>`, `PaginationMeta`

### Specialized Types
| File | Types |
|---|---|
| `sandbox.ts` | `SandboxRule`, `SimulationViolation`, `SimulationResult` |
| `rag.ts` | `RAGSearchResult`, `RAGSubGraph`, `RAGContext`, `RAGQueryStats` |
| `notifications.ts` | `Notification`, `NotificationType`, `NotificationPriority` |
| `mcp.ts` | `MCPSession`, `MCPTool`, `MCPStatus` |
| `hitl.ts` | `HITLRequest`, `HITLStatus`, `HITLSeverity`, `CodeChange` |
| `finops.ts` | `ROIMetric`, `CostByModel`, `CostByComponent`, `CostByTask`, `BudgetAlert`, `CostCap`, `FinOpsMetrics` |
| `executive.ts` | `ExecutiveKPI`, `CycleTimeData`, `DebtReduction`, `ComplianceItem` |
| `codeGraph.ts` | `CodeNode`, `CodeEdge`, `CodeStructureData` |
| `chat.ts` | `Conversation`, `ChatMessage`, `ChatMessageType`, `Participant`, `ConversationType` |
| `autoHealing.ts` | `PipelineStage`, `PipelineRun`, `LogEntry`, `FixAttempt` |
| `agentReplay.ts` | `AgentSession`, `ReplayEvent`, `EventType`, `EventSeverity` |
| `audit.ts` | `AuditEntry`, `AuditAction`, `AuditMetadata` |

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
| Notifications | — | Panel | Mark read | Dismiss | — | — |
| Conversations | Modal | ChatView / FloatingChat | — | — | — | — |
| Messages | Input | Chat bubbles | — | — | — | — |
| Sandbox Rules | — | List | — | — | Simulate | Report |
| MCP Sessions | — | List | — | — | Execute | — |
| HITL Requests | — | List | Approve/Reject | — | — | — |
| FinOps Caps | — | Dashboard | Toggle | — | — | — |

---

## 26. Interactions Matrix

| Interaction | Location |
|---|---|
| Drag-and-drop | KanbanView |
| Text search | ListView, ComponentsView, ConstraintsView, GraphView, CommandPalette, ChatSidebar, RAG Explorer |
| Dropdown filters | ListView (status, priority, component), ConstraintsView (category, severity), GraphView (status, component, max hops) |
| View mode toggle | ComponentsView (table/grid) |
| Layout toggle | GraphView (hierarchical/force-directed) |
| Dark mode toggle | UserMenu, KeyboardShortcut (D), CommandPalette |
| Language switch | UserMenu (EN/ES) |
| Click-to-detail | List rows, Kanban cards, Graph nodes, Component cards, Constraint rows, Notification items |
| Slide-in panels | IssueDetailView, Component detail, Constraint detail |
| Modal overlays | Create/Edit forms, Issue detail, User issues modal, Relationship modal, Command palette, Keyboard shortcuts help |
| Confirm dialogs | Delete actions, admin reset/seed, Kanban card delete |
| SVG chart rendering | TrendChart, DailyActivity, AvgResolution, ImpactSvgTree, AgentCostChart |
| Graph visualization | GraphView (vis-network) |
| Markdown rendering | IssueDetailView (reasoning/progress), RichTextEditor preview, RootCausePanel, ChatMessage |
| Mermaid diagrams | MarkdownRenderer renders Mermaid syntax |
| Validation workflow | ConstraintsView -> results banner |
| Admin operations | Seed/Reset with confirmation |
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
| Floating chat | Persistent Messenger-style widget, expand/collapse |
| Chat search | Filter conversations by name/participant |
| Chat pin/unpin | Pin conversations to top of list |
| Code sharing | Triple-backtick code blocks in chat messages |
| PII detection | Live detection in ChatInput, warning modal on critical PII |
| Code overlay | Toggle AST nodes in GraphView |
| Pipeline monitoring | Auto-healing 5-stage progress bar |
| Agent replay | Scrubber timeline with play/pause/step controls |
| FinOps heatmap | Cost by component bar charts |
| Executive export | PDF/PNG export via html2canvas + jspdf |

---

## 27. i18n Coverage

### Locale Files
- `en.json`: 1070+ lines, 48 top-level sections
- `es.json`: 1070+ lines, matching structure

### Sections
`kanban`, `nav`, `header`, `menu`, `dashboard`, `issues`, `components`, `policies`, `constraints`, `users`, `graph`, `codeOverlay`, `analysis`, `system`, `auth`, `common`, `dashboardStats`, `trendChart`, `statusDistribution`, `dailyActivity`, `avgResolution`, `statsCard`, `shortcuts`, `palette`, `editor`, `diff`, `hitl`, `audit`, `stream`, `tokens`, `notifications`, `agents`, `toast`, `chat`, `mcp`, `hitlCenter`, `floatingChat`, `presence`, `projects`, `export`, `bulkActions`, `profile`, `commandPalette`, `sandbox`, `rag`, `finops`, `autoHealing`, `replay`, `pii`, `executive`

### Coverage
- All user-visible text uses `t()` function
- All form labels, placeholders, and error messages translated
- All button text and aria-labels translated
- All status/priority/type labels translated
- Time-ago strings computed with i18n
- Audit trail descriptions use parameterized i18n
- Slash command labels translated
- Toast messages translated
- Chat labels translated
- Floating chat labels translated
- PII warning labels translated
- Executive dashboard labels translated
- FinOps labels translated
- Auto-healing pipeline labels translated
- Agent replay labels translated

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
| i18n | Implemented | All labels in chat section |

---

## 29. Floating Chat Widget

| Feature | Status | Details |
|---|---|---|
| **Persistent widget** | Implemented | Messenger-style bottom-right bubble, present in all views |
| **Expand/collapse** | Implemented | Toggle between compact icon and full 380px window |
| **Mini message list** | Implemented | Displays recent messages for active conversation |
| **Input** | Implemented | Mini input field at bottom of expanded window |
| i18n | Implemented | All labels in floatingChat section |

---

## 30. MCP Inspector (MCPInspectorView)

| Feature | Status | Details |
|---|---|---|
| **Session list** | Implemented | Cards showing session name, server, model, status badge |
| **Session detail** | Implemented | Slide-in panel with tools list, status, model info |
| **Mock data** | Implemented | 2 sessions: code-creator (active), data-analyst (idle) |
| **Store** | Implemented | mcpStore.ts |
| i18n | Implemented | All labels in mcp section |

---

## 31. HITL Command Center (HITLCommandCenter)

| Feature | Status | Details |
|---|---|---|
| **Request list** | Implemented | Cards showing request title, severity badge, status, agent info |
| **Request detail** | Implemented | Slide-in panel with description, approve/reject/modify actions |
| **Severity levels** | Implemented | CRITICAL (red), HIGH (orange), MEDIUM (blue), LOW (gray) |
| **Status tracking** | Implemented | PENDING to APPROVED/REJECTED/MODIFIED |
| **Mock data** | Implemented | 3 requests across multiple statuses |
| **Store** | Implemented | hitlStore.ts |
| i18n | Implemented | All labels in hitlCenter section |

---

## 32. Policy Sandbox (PolicySandboxView)

| Feature | Status | Details |
|---|---|---|
| **Rule list** | Implemented | Cards showing rule name, status badge, severity, scope |
| **Simulation** | Implemented | Click Simulate to run impact report |
| **Impact report** | Implemented | Pass/fail status, violation details with severity |
| **Rule promotion** | Implemented | Promote simulated rules to production (UI only) |
| **Mock data** | Implemented | 3 rules: dependency-depth-limit, technology-restriction, naming-convention |
| **Store** | Implemented | sandboxStore.ts |
| i18n | Implemented | All labels in sandbox section |

---

## 33. Graph RAG Explorer (GraphRAGExplorerView)

| Feature | Status | Details |
|---|---|---|
| **Search input** | Implemented | Text field with search button, Enter key support |
| **Results list** | Implemented | Cards showing entity name, type, score, sub-graph preview |
| **Query stats** | Implemented | Shows tokens, nodes, edges, sub-graph count |
| **Mock data** | Implemented | 2 results: authentication-service, payment-service |
| **Store** | Implemented | ragStore.ts |
| i18n | Implemented | All labels in rag section |

---

## 34. Agent FinOps Dashboard (AgentFinOpsView)

| Feature | Status | Details |
|---|---|---|
| **Summary cards** | Implemented | 5 cards: Total Cost, Avg/Task, Avg/Component, ROI, Active Models |
| **Cost by model** | Implemented | Horizontal bar chart with model name, cost, token count |
| **Cost by component** | Implemented | Bar chart with component name and task count |
| **ROI table** | Implemented | 7 ROI periods showing spend, savings, ROI %, time saved |
| **Budget alerts** | Implemented | Active alerts with model name, alert message, threshold |
| **Cost caps** | Implemented | Interactive toggle switches to enable/disable caps per model |
| **Cost cap sliders** | Implemented | Adjust monthly budget limit per model |
| **Mock data** | Implemented | 4 models, 7 components, 7 ROI periods, 3 alerts, 4 cost caps |
| **Store** | Implemented | finopsStore.ts |
| i18n | Implemented | All labels in finops section |

---

## 35. Auto-Healing Pipeline Monitor (AutoHealingMonitorView)

| Feature | Status | Details |
|---|---|---|
| **Summary cards** | Implemented | 5 cards: Total Runs, Healing Rate, Avg Duration, Active Fixes, Auto-Fix % |
| **Run list** | Implemented | Cards showing pipeline name, status badge, duration, stage progress |
| **Run detail** | Implemented | Slide-in panel with 5-stage pipeline progress bar |
| **Live terminal** | Implemented | Scrollable log output with colored stage indicators |
| **Fix attempts** | Implemented | Shows fix description, test output, diff preview |
| **Mock data** | Implemented | 3 runs, 12 log entries, 3 fix attempts |
| **Store** | Implemented | autoHealingStore.ts |
| i18n | Implemented | All labels in autoHealing section |

---

## 36. Agent Replay Player (AgentReplayView)

| Feature | Status | Details |
|---|---|---|
| **Session list** | Implemented | Cards showing session title, agent name, date, duration, event count |
| **Session detail** | Implemented | Slide-in panel with event stream, files affected, Cypher queries |
| **Scrubber timeline** | Implemented | Horizontal bar showing event progress, clickable to seek |
| **Playback controls** | Implemented | Play/Pause, Step Forward, Step Backward, Speed selector (1x/2x/4x) |
| **Event stream** | Implemented | Color-coded events with icons by type |
| **Files affected panel** | Implemented | Lists files modified during replay |
| **Cypher queries** | Implemented | Shows Neo4j queries executed during agent session |
| **Mock data** | Implemented | 2 sessions, 21 total replay events |
| **Store** | Implemented | agentReplayStore.ts |
| i18n | Implemented | All labels in replay section |

---

## 37. Executive Dashboard (ExecutiveDashboardView)

| Feature | Status | Details |
|---|---|---|
| **KPI cards** | Implemented | 4 cards: Velocity, Cycle Time, Agent ROI, Tech Debt Score |
| **Cycle time comparison** | Implemented | Table showing 7x speedup (human vs AI-assisted) |
| **Tech debt reduction** | Implemented | Bar chart showing 6-month debt reduction trend |
| **Architecture compliance** | Implemented | Ring gauges for 7 compliance areas (SRP, Dependency Rule, etc.) |
| **PDF export** | Implemented | html2canvas + jspdf, downloads executive-report.pdf |
| **PNG export** | Implemented | html2canvas, downloads executive-dashboard.png |
| **Mock data** | Implemented | 4 KPIs, 6 cycle time categories, 6 months debt, 7 compliance areas |
| **Store** | Implemented | executiveStore.ts |
| i18n | Implemented | All labels in executive section |

---

## 38. PII and Secrets Guardrail

| Feature | Status | Details |
|---|---|---|
| **PII detection engine** | Implemented | 10 regex patterns in piiDetector.ts |
| **Detection targets** | Implemented | API keys, JWT tokens, private keys, passwords, bearer tokens, emails, phones, SSN, credit cards, IP addresses |
| **Severity levels** | Implemented | Critical (API keys, private keys, passwords), High (tokens, SSN, credit cards), Medium (emails, phones), Low (IPs) |
| **Inline banner** | Implemented | PIIDetectionBanner.vue shows real-time warnings in ChatInput |
| **Warning modal** | Implemented | PIIWarningModal.vue with Cancel / Mask & Send / Send Anyway actions |
| **Live detection** | Implemented | Runs on every keystroke in ChatInput, blocks critical PII |
| **Text masking** | Implemented | redactText() masks sensitive patterns with asterisks |
| **Colors** | Implemented | getSeverityColor() and getSeverityBg() for UI styling |
| i18n | Implemented | All labels in pii section |
| **Integration** | Implemented | ChatInput.vue wires up PII detection with modal |

---

## 39. Code Graph Overlay

| Feature | Status | Details |
|---|---|---|
| **AST node types** | Implemented | File, Class, Function node shapes |
| **Node rendering** | Implemented | Database shape for files, Diamond for classes, Triangle for functions |
| **Color coding** | Implemented | Cyan (files), Teal (classes), Emerald (functions) |
| **Overlay toggle** | Implemented | Show/hide code nodes alongside issue nodes in GraphView |
| **Code node detail** | Implemented | Click shows file path, language, lines, type |
| **Types** | Implemented | codeGraph.ts: CodeNode, CodeEdge, CodeStructureData |
| **Store** | Implemented | codeGraphStore.ts with 13 mock nodes + 17 edges |
| **Graph algorithms** | Implemented | graphUtils.ts: BFS, cycle detection, blast radius, transitive deps |
| i18n | Implemented | All labels in codeOverlay section |

---

## 40. Known Gaps and Missing Features

### Not Implemented
- No real backend integration (mock mode only)
- No actual WebSocket/SSE connections to a live server
- No real user authentication (API key only)
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
- No test suite (no Jest/Vitest configuration)
- No CI/CD pipeline
- No Storybook / component documentation
- No E2E tests
- No accessibility audit (WCAG compliance)
- No performance monitoring / Lighthouse
- No service worker / offline support
- No internationalization for right-to-left languages
- No mobile responsive layout (desktop only)
