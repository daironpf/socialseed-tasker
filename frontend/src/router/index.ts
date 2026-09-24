import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/board' },
    { path: '/board', name: 'Board', component: () => import('@/views/BoardView.vue') },
    { path: '/system', name: 'System', component: () => import('@/views/DashboardSystemView.vue') },
    { path: '/kanban', name: 'Kanban', component: () => import('@/views/KanbanView.vue') },
    { path: '/list', name: 'List', component: () => import('@/views/ListView.vue') },
    { path: '/graph', name: 'Graph', component: () => import('@/views/GraphView.vue') },
    { path: '/components', name: 'Components', component: () => import('@/views/ComponentsView.vue') },
    { path: '/policies', name: 'Policies', component: () => import('@/views/PoliciesView.vue') },
    { path: '/constraints', name: 'Constraints', component: () => import('@/views/ConstraintsView.vue') },
    { path: '/sandbox', name: 'PolicySandbox', component: () => import('@/views/PolicySandboxView.vue') },
    { path: '/rag', name: 'GraphRAGExplorer', component: () => import('@/views/GraphRAGExplorerView.vue') },
    { path: '/finops', name: 'AgentFinOps', component: () => import('@/views/AgentFinOpsView.vue') },
    { path: '/auto-healing', name: 'AutoHealing', component: () => import('@/views/AutoHealingMonitorView.vue') },
    { path: '/replay', name: 'AgentReplay', component: () => import('@/views/AgentReplayView.vue') },
    { path: '/executive', name: 'ExecutiveDashboard', component: () => import('@/views/ExecutiveDashboardView.vue') },
    { path: '/users', name: 'Users', component: () => import('@/views/UsersView.vue') },
    { path: '/chat', name: 'Chat', component: () => import('@/views/ChatView.vue') },
    { path: '/profile', name: 'Profile', component: () => import('@/views/ProfileView.vue') },
    { path: '/analysis', name: 'Analysis', component: () => import('@/views/AnalysisView.vue') },
    { path: '/mcp', name: 'MCPInspector', component: () => import('@/views/MCPInspectorView.vue') },
    { path: '/hitl', name: 'HITLCommandCenter', component: () => import('@/views/HITLCommandCenter.vue') },
    { path: '/organization', name: 'OrganizationSettings', component: () => import('@/views/OrganizationSettingsView.vue') },
    { path: '/governance-matrix', name: 'GovernanceMatrix', component: () => import('@/views/GovernanceMatrixView.vue') },
    { path: '/audit-log', name: 'AuditLog', component: () => import('@/views/AuditLogView.vue') },
    { path: '/agents/studio', name: 'AgentStudio', component: () => import('@/views/AgentStudioView.vue') },
    { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/NotFoundView.vue') },
  ],
})

router.afterEach(() => {
  window.scrollTo(0, 0)
})

export default router
