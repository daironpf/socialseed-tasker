# UI Mock Enterprise Backlog — Issue Index

**Source:** `notas.md` (prioridad absoluta a UI/UX Enterprise sobre API mockeada)
**Created:** 2026-09-24
**Status:** TODO

> Las issues de `notas.md` usaban números #501–#508, ya ocupados en `.issues/done`.
> Se renumeraron a **#509–#516** conservando el orden y contenido del plan original.

---

## Issue Index

| # | Issue | Priority | Type | Status | notas.md |
|---|---|---|---|---|---|
| #509 | Multi-Tenancy & Enterprise Organization Management (Mock-Enabled) | CRITICAL | feat / enterprise | TODO | #501 |
| #510 | Advanced Agent Governance, RBAC & Granular HITL Approval UI | HIGH | feat / governance | TODO | #502 |
| #511 | Interactive Graph Visualization with Mock Graph Exploration & Filters | HIGH | feat / visualization | TODO | #503 |
| #512 | Comprehensive Audit Log, Compliance & PII Redaction Suite | HIGH | feat / compliance | TODO | #504 |
| #513 | Mock Agent Simulator & Custom Agent Builder Studio | MEDIUM | feat / agents | TODO | #505 |
| #514 | Custom Dashboards, Reporting Engine & SLA Metric Tracking | MEDIUM | feat / analytics | TODO | #506 |
| #515 | Offline First Capabilities & Mock Sync Queue Management | MEDIUM | feat / ux | TODO | #507 |
| #516 | UI Sound Effects, Notifications Center & Toast Theme System | LOW | feat / polish | TODO | #508 |

---

## Feature Summary

### Enterprise Foundation
- **#509 Multi-Tenancy:** OrganizationSwitcher, org → department → workspace hierarchy, enterprise roles, quotas & retention policies

### Governance & Risk
- **#510 Governance Matrix & RBAC:** Permission matrix by agent type/risk, Pending Approvals Queue with Diff Viewer, live restricted-action alerts

### Visualization
- **#511 Graph Exploration:** Zoom/pan/clusters/impact paths, filters by criticality & node type, side inspector with blast-radius

### Compliance
- **#512 Audit & PII:** AuditLogView (filter + CSV/JSON/PDF export), real-time PII redaction preview in agent console and issue comments

### Agent Platform
- **#513 Agent Studio:** Visual agent builder, Sandbox Tester, corporate agent library (save/clone/enable)

### Analytics
- **#514 Dashboards & SLA:** MTTR comparison, auto-healing rate, budget by project, SLA gap panel, weekly/monthly executive reports

### Resilience
- **#515 Offline First:** Network mode simulator, mutation queue in LocalStorage, SyncQueueDrawer with conflict resolution

### Delight / Polish
- **#516 Sound & Notifications:** NotificationCenter grouped by criticality, configurable sound effects, alert preferences, toast themes

---

## Dependencies (suggested order)

1. **#509** (CRITICAL) — roles/org context feeds later features
2. **#510, #511, #512** (HIGH) — parallelizable after #509 roles exist for RBAC display
3. **#513, #514, #515** (MEDIUM)
4. **#516** (LOW) — can integrate notifications from #510/#514/#515

---

## Related Done Issues

| Done | Relevant to |
|---|---|
| #479, #498 | Project/org selector → #509 |
| #489, #501, #507, #471 | HITL/Governance → #510 |
| #80, #480–#482, #492 | Graph → #511 |
| #478, #496 | Audit/PII → #512 |
| #474, #487, #488 | Agents → #513 |
| #493, #494, #497 | Analytics → #514 |
| #499, #91, #94 | Offline/sync → #515 |
| #475, #476, #503, #508 | Notifications/polish → #516 |

---

## Release Checklist (backlog)

- [ ] 8 issues implemented in `.issues/to-do` order (or by priority)
- [ ] Each issue: `npm run build` green, i18n EN+ES, `features.md` updated
- [ ] Move issue file to `.issues/done/` with `Status: DONE` when complete
- [ ] Commit message references `#NNN`
