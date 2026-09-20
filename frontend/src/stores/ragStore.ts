import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RAGResult, RAGSearchResponse, RAGMetrics } from '@/types/rag'

const MOCK_RESULTS: RAGResult[] = [
  {
    id: 'rag-001',
    issueId: 'ISS-042',
    issueTitle: 'Fix circular dependency in auth module',
    issueStatus: 'CLOSED',
    similarity: 0.94,
    solutionSummary: 'Resolved by introducing an AuthGateway interface that both AuthService and UserService implement. The circular dependency was broken by inverting the dependency direction through the gateway pattern, ensuring neither module directly imports the other.',
    solutionDate: '2026-08-15',
    component: 'Auth',
    keywords: ['circular-dependency', 'gateway-pattern', 'auth', 'dependency-inversion'],
    contextNodes: [
      { id: 'n1', label: 'AuthService', type: 'Class', relevance: 0.95 },
      { id: 'n2', label: 'UserService', type: 'Class', relevance: 0.88 },
      { id: 'n3', label: 'AuthGateway', type: 'Interface', relevance: 0.92 },
      { id: 'n4', label: 'ISS-042', type: 'Issue', relevance: 1.0 },
      { id: 'n5', label: 'Auth Module', type: 'Component', relevance: 0.85 },
    ],
    contextEdges: [
      { from: 'n1', to: 'n3', type: 'IMPLEMENTS' },
      { from: 'n2', to: 'n3', type: 'IMPLEMENTS' },
      { from: 'n4', to: 'n1', type: 'REFERENCES' },
      { from: 'n4', to: 'n2', type: 'REFERENCES' },
      { from: 'n5', to: 'n1', type: 'CONTAINS' },
      { from: 'n5', to: 'n2', type: 'CONTAINS' },
    ],
  },
  {
    id: 'rag-002',
    issueId: 'ISS-078',
    issueTitle: 'Optimize Neo4j query performance for dependency graph',
    issueStatus: 'CLOSED',
    similarity: 0.87,
    solutionSummary: 'Added composite indexes on (Issue.status, Issue.priority) and (Dependency.type, Dependency.from_id). Reduced average query time from 450ms to 12ms for dependency chain traversal by using parameterized Cypher queries with depth limiting.',
    solutionDate: '2026-08-22',
    component: 'Neo4j',
    keywords: ['performance', 'neo4j', 'cypher', 'indexing', 'query-optimization'],
    contextNodes: [
      { id: 'n1', label: 'Neo4j Driver', type: 'Module', relevance: 0.90 },
      { id: 'n2', label: 'DependencyService', type: 'Class', relevance: 0.88 },
      { id: 'n3', label: 'ISS-078', type: 'Issue', relevance: 1.0 },
      { id: 'n4', label: 'Graph DB', type: 'Component', relevance: 0.82 },
    ],
    contextEdges: [
      { from: 'n2', to: 'n1', type: 'USES' },
      { from: 'n3', to: 'n2', type: 'REFERENCES' },
      { from: 'n4', to: 'n1', type: 'HOSTED_ON' },
    ],
  },
  {
    id: 'rag-003',
    issueId: 'ISS-112',
    issueTitle: 'Implement rate limiting for API endpoints',
    issueStatus: 'CLOSED',
    similarity: 0.82,
    solutionSummary: 'Implemented token bucket algorithm using Redis as backing store. Applied per-user and per-endpoint rate limits with configurable thresholds. Added X-RateLimit-* headers to all responses. Created middleware that integrates with the existing FastAPI dependency injection system.',
    solutionDate: '2026-09-01',
    component: 'API',
    keywords: ['rate-limiting', 'redis', 'middleware', 'fastapi', 'security'],
    contextNodes: [
      { id: 'n1', label: 'RateLimitMiddleware', type: 'Class', relevance: 0.93 },
      { id: 'n2', label: 'TokenBucket', type: 'Class', relevance: 0.89 },
      { id: 'n3', label: 'ISS-112', type: 'Issue', relevance: 1.0 },
      { id: 'n4', label: 'API Server', type: 'Component', relevance: 0.80 },
      { id: 'n5', label: 'Redis Cache', type: 'Component', relevance: 0.78 },
    ],
    contextEdges: [
      { from: 'n1', to: 'n2', type: 'USES' },
      { from: 'n1', to: 'n5', type: 'STORES_IN' },
      { from: 'n3', to: 'n1', type: 'REFERENCES' },
      { from: 'n4', to: 'n1', type: 'CONTAINS' },
    ],
  },
  {
    id: 'rag-004',
    issueId: 'ISS-055',
    issueTitle: 'Fix memory leak in WebSocket connection handler',
    issueStatus: 'CLOSED',
    similarity: 0.78,
    solutionSummary: 'Identified that event listeners were not being cleaned up on disconnect. Added proper cleanup in the disconnect handler using AbortController for fetch requests and explicit removeEventListener calls. Also added connection timeout (30s idle) to prevent zombie connections.',
    solutionDate: '2026-08-10',
    component: 'WebSocket',
    keywords: ['memory-leak', 'websocket', 'cleanup', 'event-listener', 'connection'],
    contextNodes: [
      { id: 'n1', label: 'WSHandler', type: 'Class', relevance: 0.91 },
      { id: 'n2', label: 'ConnectionManager', type: 'Class', relevance: 0.85 },
      { id: 'n3', label: 'ISS-055', type: 'Issue', relevance: 1.0 },
    ],
    contextEdges: [
      { from: 'n1', to: 'n2', type: 'MANAGES' },
      { from: 'n3', to: 'n1', type: 'REFERENCES' },
    ],
  },
  {
    id: 'rag-005',
    issueId: 'ISS-134',
    issueTitle: 'Add i18n support for notification messages',
    issueStatus: 'CLOSED',
    similarity: 0.75,
    solutionSummary: 'Extended the notification store to accept i18n keys instead of raw strings. Created a translateNotification() helper that resolves keys at display time. Updated all toast calls across 12 files to use translated keys. Added locale-aware date formatting for notification timestamps.',
    solutionDate: '2026-09-10',
    component: 'Notifications',
    keywords: ['i18n', 'notifications', 'localization', 'toast', 'translation'],
    contextNodes: [
      { id: 'n1', label: 'notificationStore', type: 'Module', relevance: 0.90 },
      { id: 'n2', label: 'useI18n', type: 'Function', relevance: 0.88 },
      { id: 'n3', label: 'ISS-134', type: 'Issue', relevance: 1.0 },
      { id: 'n4', label: 'NotificationCenter', type: 'Class', relevance: 0.82 },
    ],
    contextEdges: [
      { from: 'n1', to: 'n2', type: 'USES' },
      { from: 'n4', to: 'n1', type: 'READS_FROM' },
      { from: 'n3', to: 'n1', type: 'REFERENCES' },
    ],
  },
  {
    id: 'rag-006',
    issueId: 'ISS-091',
    issueTitle: 'Implement drag-and-drop for Kanban board',
    issueStatus: 'CLOSED',
    similarity: 0.71,
    solutionSummary: 'Used HTML5 Drag and Drop API with custom ghost elements. Implemented optimistic UI updates with rollback on API failure. Added touch support via pointer events for mobile. Created reusable useDragDrop composable with status transition validation.',
    solutionDate: '2026-08-28',
    component: 'Frontend',
    keywords: ['drag-and-drop', 'kanban', 'html5', 'touch', 'composable'],
    contextNodes: [
      { id: 'n1', label: 'useDragDrop', type: 'Function', relevance: 0.92 },
      { id: 'n2', label: 'KanbanColumn', type: 'Class', relevance: 0.87 },
      { id: 'n3', label: 'ISS-091', type: 'Issue', relevance: 1.0 },
      { id: 'n4', label: 'IssueCard', type: 'Class', relevance: 0.83 },
    ],
    contextEdges: [
      { from: 'n2', to: 'n1', type: 'USES' },
      { from: 'n4', to: 'n1', type: 'USES' },
      { from: 'n3', to: 'n2', type: 'REFERENCES' },
    ],
  },
]

export const useRagStore = defineStore('rag', () => {
  const results = ref<RAGResult[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastQuery = ref('')
  const searchResponse = ref<RAGSearchResponse | null>(null)
  const selectedResult = ref<RAGResult | null>(null)

  const metrics = computed<RAGMetrics>(() => ({
    totalEmbeddings: MOCK_RESULTS.length,
    avgSimilarity: results.value.length > 0
      ? results.value.reduce((sum, r) => sum + r.similarity, 0) / results.value.length
      : 0,
    topComponents: [
      { name: 'Auth', count: 2 },
      { name: 'API', count: 3 },
      { name: 'Frontend', count: 4 },
      { name: 'Neo4j', count: 2 },
    ],
    lastIndexedAt: '2026-09-20T08:00:00Z',
  }))

  async function search(query: string, threshold: number = 0.5, maxResults: number = 10): Promise<RAGSearchResponse> {
    loading.value = true
    error.value = null
    return new Promise((resolve) => {
      setTimeout(() => {
        const filtered = MOCK_RESULTS
          .filter(r => r.similarity >= threshold)
          .sort((a, b) => b.similarity - a.similarity)
          .slice(0, maxResults)

        const response: RAGSearchResponse = {
          query,
          results: filtered,
          totalMatches: filtered.length,
          searchTimeMs: Math.floor(Math.random() * 50) + 20,
          embeddingModel: 'text-embedding-3-small',
        }

        results.value = filtered
        searchResponse.value = response
        lastQuery.value = query
        loading.value = false
        resolve(response)
      }, 800)
    })
  }

  function selectResult(result: RAGResult | null) {
    selectedResult.value = result
  }

  return {
    results,
    loading,
    error,
    lastQuery,
    searchResponse,
    selectedResult,
    metrics,
    search,
    selectResult,
  }
})
