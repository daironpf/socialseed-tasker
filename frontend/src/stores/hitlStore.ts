import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { HITLRequest, HITLRequestSeverity, HITLRequestStatus } from '@/types/hitl'

const MOCK_DIFF_1 = `@@ -12,8 +12,12 @@
 import { validateSchema } from './ validators'
 import { logger } from '../utils/logger'
 
-export function deleteUsers(ids: string[]) {
-  return db.query('DELETE FROM users WHERE id IN $1', [ids])
+export async function deleteUsers(ids: string[], options?: { soft?: boolean }) {
+  if (options?.soft) {
+    logger.warn('Soft deleting users', { ids })
+    return db.query('UPDATE users SET deleted_at = NOW() WHERE id IN $1', [ids])
+  }
+  logger.error('Hard deleting users', { ids })
+  return db.query('DELETE FROM users WHERE id IN $1', [ids])
 }`

const MOCK_DIFF_2 = `@@ -45,6 +45,18 @@
   const schema = await getSchema('main')
   const validator = new SchemaValidator(schema)
 
+  // Add migration step for new relationship
+  await session.run(\`
+    MATCH (a:Component)-[r:DEPENDS_ON]->(b:Component)
+    WHERE r.weight IS NULL
+    SET r.weight = 1.0
+    RETURN count(r) as updated
+  \`)
+
+  logger.info('Migration completed: added weight to DEPENDS_ON relationships')
+
   return validator.validate()
 }`

const MOCK_DIFF_3 = `@@ -1,5 +1,5 @@
-// Schema version: 3.2.1
+// Schema version: 3.3.0
 
 CREATE CONSTRAINT component_name IF NOT EXISTS
 FOR (c:Component) REQUIRE c.name IS UNIQUE`

const MOCK_REQUESTS: HITLRequest[] = [
  {
    id: 'hitl-001',
    title: 'Delete production users table',
    description: 'Agent requests DELETE operation on the production users table. This is a destructive operation that will permanently remove all user records.',
    type: 'delete_operation',
    severity: 'CRITICAL',
    status: 'pending',
    agentId: 'agent-arch',
    agentName: 'Arch-Bot',
    agentAvatar: '🤖',
    issueId: 'ISS-042',
    issueTitle: 'Database schema optimization',
    component: 'database',
    command: 'DELETE FROM users WHERE deleted_at IS NOT NULL',
    target: 'production-db',
    diffs: [{ filename: 'src/db/users.ts', content: MOCK_DIFF_1 }],
    impact: {
      totalAffected: 12,
      directDeps: 4,
      transitiveDeps: 8,
      riskLevel: 'CRITICAL',
      affectedComponents: ['auth-service', 'user-api', 'notification-hub', 'analytics'],
    },
    createdAt: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: 'hitl-002',
    title: 'Push to main branch',
    description: 'Agent requests push to main branch with schema migration changes affecting DEPENDS_ON relationships.',
    type: 'deploy',
    severity: 'HIGH',
    status: 'pending',
    agentId: 'agent-coder',
    agentName: 'CodeReviewer',
    agentAvatar: '👨‍💻',
    issueId: 'ISS-051',
    issueTitle: 'Add relationship weight metadata',
    component: 'neo4j-schema',
    command: 'git push origin main',
    target: 'github/tasker-backend',
    diffs: [
      { filename: 'src/schema/migration.ts', content: MOCK_DIFF_2 },
      { filename: 'schema/version.txt', content: MOCK_DIFF_3 },
    ],
    impact: {
      totalAffected: 7,
      directDeps: 3,
      transitiveDeps: 4,
      riskLevel: 'HIGH',
      affectedComponents: ['graph-engine', 'neo4j-adapter', 'migration-runner'],
    },
    createdAt: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: 'hitl-003',
    title: 'Schema migration on production DB',
    description: 'Agent requests schema migration that adds new constraints and indexes to the production Neo4j database.',
    type: 'schema_migration',
    severity: 'HIGH',
    status: 'pending',
    agentId: 'agent-arch',
    agentName: 'Arch-Bot',
    agentAvatar: '🤖',
    issueId: 'ISS-081',
    issueTitle: 'Add cascade delete constraints',
    component: 'neo4j-schema',
    command: 'CREATE CONSTRAINT cascade_delete IF NOT EXISTS',
    target: 'neo4j-production',
    diffs: [{ filename: 'migrations/003_constraints.cypher', content: MOCK_DIFF_3 }],
    impact: {
      totalAffected: 5,
      directDeps: 2,
      transitiveDeps: 3,
      riskLevel: 'MEDIUM',
      affectedComponents: ['neo4j-adapter', 'graph-engine'],
    },
    createdAt: new Date(Date.now() - 14400000).toISOString(),
  },
  {
    id: 'hitl-004',
    title: 'Update API rate limits',
    description: 'Agent requests configuration change to increase API rate limits from 100 to 500 requests per minute.',
    type: 'config_change',
    severity: 'MEDIUM',
    status: 'pending',
    agentId: 'agent-ops',
    agentName: 'OpsAgent',
    agentAvatar: '🔧',
    issueId: 'ISS-103',
    issueTitle: 'API rate limit optimization',
    component: 'api-gateway',
    command: 'UPDATE config SET rate_limit = 500 WHERE service = \'api\'',
    target: 'config-store',
    diffs: [{ filename: 'config/rate-limits.yaml', content: MOCK_DIFF_3 }],
    impact: {
      totalAffected: 3,
      directDeps: 1,
      transitiveDeps: 2,
      riskLevel: 'LOW',
      affectedComponents: ['api-gateway'],
    },
    createdAt: new Date(Date.now() - 28800000).toISOString(),
  },
  {
    id: 'hitl-005',
    title: 'Refactor authentication module',
    description: 'Agent requests refactoring of the authentication module to support OAuth2 providers.',
    type: 'code_change',
    severity: 'MEDIUM',
    status: 'pending',
    agentId: 'agent-coder',
    agentName: 'CodeReviewer',
    agentAvatar: '👨‍💻',
    issueId: 'ISS-067',
    issueTitle: 'OAuth2 provider integration',
    component: 'auth-service',
    command: 'REFACTOR src/auth/providers/*',
    target: 'src/auth/',
    diffs: [{ filename: 'src/auth/providers/oauth2.ts', content: MOCK_DIFF_1 }],
    impact: {
      totalAffected: 6,
      directDeps: 2,
      transitiveDeps: 4,
      riskLevel: 'MEDIUM',
      affectedComponents: ['auth-service', 'user-api', 'session-manager'],
    },
    createdAt: new Date(Date.now() - 43200000).toISOString(),
  },
  {
    id: 'hitl-006',
    title: 'Deploy new caching layer',
    description: 'Agent requests deployment of a new Redis caching layer for the graph query results.',
    type: 'deploy',
    severity: 'LOW',
    status: 'approved',
    agentId: 'agent-ops',
    agentName: 'OpsAgent',
    agentAvatar: '🔧',
    issueId: 'ISS-078',
    issueTitle: 'Graph query caching',
    component: 'cache-service',
    command: 'docker-compose up -d redis-cache',
    target: 'production-cluster',
    diffs: [{ filename: 'docker-compose.cache.yml', content: MOCK_DIFF_3 }],
    impact: {
      totalAffected: 2,
      directDeps: 1,
      transitiveDeps: 1,
      riskLevel: 'LOW',
      affectedComponents: ['cache-service'],
    },
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    reviewedAt: new Date(Date.now() - 82800000).toISOString(),
    reviewedBy: 'admin',
  },
  {
    id: 'hitl-007',
    title: 'Rollback migration 003',
    description: 'Agent requests rollback of migration 003 due to detected compatibility issues with legacy clients.',
    type: 'schema_migration',
    severity: 'CRITICAL',
    status: 'rejected',
    agentId: 'agent-arch',
    agentName: 'Arch-Bot',
    agentAvatar: '🤖',
    issueId: 'ISS-081',
    issueTitle: 'Rollback failed migration',
    component: 'neo4j-schema',
    command: 'ROLLBACK MIGRATION 003',
    target: 'neo4j-production',
    diffs: [{ filename: 'migrations/003_rollback.cypher', content: MOCK_DIFF_3 }],
    impact: {
      totalAffected: 15,
      directDeps: 5,
      transitiveDeps: 10,
      riskLevel: 'CRITICAL',
      affectedComponents: ['neo4j-adapter', 'graph-engine', 'api-gateway', 'auth-service'],
    },
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    reviewedAt: new Date(Date.now() - 169200000).toISOString(),
    reviewedBy: 'admin',
    feedback: 'Rollback not approved - legacy clients have been updated. Proceed with forward migration instead.',
  },
]

export const useHitlStore = defineStore('hitl', () => {
  const requests = ref<HITLRequest[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedRequestId = ref<string | null>(null)

  const pendingRequests = computed(() => requests.value.filter(r => r.status === 'pending'))
  const approvedRequests = computed(() => requests.value.filter(r => r.status === 'approved'))
  const rejectedRequests = computed(() => requests.value.filter(r => r.status === 'rejected'))
  const modifiedRequests = computed(() => requests.value.filter(r => r.status === 'modified'))

  const selectedRequest = computed(() =>
    requests.value.find(r => r.id === selectedRequestId.value) || null
  )

  const pendingCount = computed(() => pendingRequests.value.length)
  const criticalCount = computed(() => pendingRequests.value.filter(r => r.severity === 'CRITICAL').length)

  async function fetchRequests() {
    loading.value = true
    error.value = null
    try {
      await new Promise(resolve => setTimeout(resolve, 300))
      requests.value = [...MOCK_REQUESTS]
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function approveRequest(id: string): Promise<boolean> {
    const req = requests.value.find(r => r.id === id)
    if (!req || req.status !== 'pending') return false
    req.status = 'approved'
    req.reviewedAt = new Date().toISOString()
    req.reviewedBy = 'admin'
    if (selectedRequestId.value === id) selectedRequestId.value = null
    return true
  }

  async function rejectRequest(id: string, feedback: string): Promise<boolean> {
    const req = requests.value.find(r => r.id === id)
    if (!req || req.status !== 'pending') return false
    req.status = 'rejected'
    req.reviewedAt = new Date().toISOString()
    req.reviewedBy = 'admin'
    req.feedback = feedback
    if (selectedRequestId.value === id) selectedRequestId.value = null
    return true
  }

  async function modifyRequest(id: string, feedback: string): Promise<boolean> {
    const req = requests.value.find(r => r.id === id)
    if (!req || req.status !== 'pending') return false
    req.status = 'modified'
    req.reviewedAt = new Date().toISOString()
    req.reviewedBy = 'admin'
    req.feedback = feedback
    if (selectedRequestId.value === id) selectedRequestId.value = null
    return true
  }

  function selectRequest(id: string) {
    selectedRequestId.value = id
  }

  function getSeverityColor(severity: HITLRequestSeverity): string {
    const colors: Record<HITLRequestSeverity, string> = {
      CRITICAL: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      HIGH: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      MEDIUM: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      LOW: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    }
    return colors[severity]
  }

  function getStatusColor(status: HITLRequestStatus): string {
    const colors: Record<HITLRequestStatus, string> = {
      pending: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      modified: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    }
    return colors[status]
  }

  function getTypeIcon(type: string): string {
    const icons: Record<string, string> = {
      code_change: '📝',
      schema_migration: '🗃️',
      delete_operation: '🗑️',
      deploy: '🚀',
      config_change: '⚙️',
    }
    return icons[type] || '📋'
  }

  function formatTimeAgo(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return `${Math.floor(hrs / 24)}d ago`
  }

  return {
    requests,
    loading,
    error,
    selectedRequestId,
    pendingRequests,
    approvedRequests,
    rejectedRequests,
    modifiedRequests,
    selectedRequest,
    pendingCount,
    criticalCount,
    fetchRequests,
    approveRequest,
    rejectRequest,
    modifyRequest,
    selectRequest,
    getSeverityColor,
    getStatusColor,
    getTypeIcon,
    formatTimeAgo,
  }
})
