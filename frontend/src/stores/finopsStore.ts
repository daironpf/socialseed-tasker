import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ROIMetric, CostByModel, CostByComponent, CostByTask,
  BudgetAlert, CostCap, FinOpsMetrics
} from '@/types/finops'

const MOCK_MODELS: CostByModel[] = [
  { model: 'claude-3.5-sonnet', provider: 'Anthropic', promptTokens: 1250000, completionTokens: 890000, totalTokens: 2140000, cost: 42.80, requests: 340 },
  { model: 'gpt-4o', provider: 'OpenAI', promptTokens: 980000, completionTokens: 620000, totalTokens: 1600000, cost: 38.40, requests: 280 },
  { model: 'deepseek-chat', provider: 'DeepSeek', promptTokens: 2100000, completionTokens: 1500000, totalTokens: 3600000, cost: 10.80, requests: 520 },
  { model: 'claude-3-haiku', provider: 'Anthropic', promptTokens: 450000, completionTokens: 310000, totalTokens: 760000, cost: 2.28, requests: 190 },
]

const MOCK_COMPONENTS: CostByComponent[] = [
  { component: 'Auth Module', totalCost: 18.50, requests: 145, avgCostPerRequest: 0.128 },
  { component: 'API Server', totalCost: 25.30, requests: 210, avgCostPerRequest: 0.120 },
  { component: 'Frontend', totalCost: 15.20, requests: 180, avgCostPerRequest: 0.084 },
  { component: 'Neo4j', totalCost: 12.40, requests: 95, avgCostPerRequest: 0.131 },
  { component: 'WebSocket', totalCost: 8.60, requests: 78, avgCostPerRequest: 0.110 },
  { component: 'Notifications', totalCost: 5.80, requests: 62, avgCostPerRequest: 0.094 },
  { component: 'Tasker Core', totalCost: 7.58, requests: 69, avgCostPerRequest: 0.110 },
]

const MOCK_TASKS: CostByTask[] = [
  { issueId: 'ISS-001', issueTitle: 'Fix login validation', model: 'claude-3.5-sonnet', cost: 3.20, tokensUsed: 160000, executionTimeMs: 4200 },
  { issueId: 'ISS-003', issueTitle: 'Implement rate limiting', model: 'gpt-4o', cost: 4.80, tokensUsed: 240000, executionTimeMs: 6100 },
  { issueId: 'ISS-005', issueTitle: 'Refactor auth module', model: 'claude-3.5-sonnet', cost: 5.50, tokensUsed: 275000, executionTimeMs: 7800 },
  { issueId: 'ISS-008', issueTitle: 'Add WebSocket handler', model: 'deepseek-chat', cost: 1.20, tokensUsed: 120000, executionTimeMs: 3100 },
  { issueId: 'ISS-012', issueTitle: 'Fix memory leak', model: 'claude-3.5-sonnet', cost: 2.90, tokensUsed: 145000, executionTimeMs: 3800 },
  { issueId: 'ISS-015', issueTitle: 'Write unit tests', model: 'deepseek-chat', cost: 0.80, tokensUsed: 80000, executionTimeMs: 2200 },
  { issueId: 'ISS-018', issueTitle: 'Update documentation', model: 'claude-3-haiku', cost: 0.45, tokensUsed: 45000, executionTimeMs: 1200 },
  { issueId: 'ISS-020', issueTitle: 'Optimize Cypher queries', model: 'gpt-4o', cost: 3.60, tokensUsed: 180000, executionTimeMs: 5200 },
  { issueId: 'ISS-025', issueTitle: 'Add i18n support', model: 'claude-3.5-sonnet', cost: 2.10, tokensUsed: 105000, executionTimeMs: 2800 },
  { issueId: 'ISS-030', issueTitle: 'Implement drag-and-drop', model: 'deepseek-chat', cost: 1.50, tokensUsed: 150000, executionTimeMs: 4000 },
]

const MOCK_ROI: ROIMetric[] = [
  { label: 'This Month', tokenCost: 94.28, humanHoursSaved: 47.2, humanCostEquivalent: 3540, roi: 3755, period: '2026-09' },
  { label: 'Last Month', tokenCost: 82.15, humanHoursSaved: 41.1, humanCostEquivalent: 3082, roi: 3652, period: '2026-08' },
  { label: 'All Time', tokenCost: 412.50, humanHoursSaved: 206.3, humanCostEquivalent: 15472, roi: 3652, period: 'all' },
]

const MOCK_ALERTS: BudgetAlert[] = [
  { id: 'alert-001', type: 'issue', name: 'ISS-005: Refactor auth module', currentCost: 5.50, threshold: 5.00, severity: 'critical', triggeredAt: '2026-09-19T14:30:00Z' },
  { id: 'alert-002', type: 'issue', name: 'ISS-003: Implement rate limiting', currentCost: 4.80, threshold: 5.00, severity: 'warning', triggeredAt: '2026-09-19T15:00:00Z' },
]

const MOCK_CAPS: CostCap[] = [
  { id: 'cap-001', scope: 'project', name: 'SocialSeed Tasker', limit: 150, used: 94.28, period: 'monthly', isActive: true },
  { id: 'cap-002', scope: 'organizational', name: 'SocialSeed Org', limit: 500, used: 312.40, period: 'monthly', isActive: true },
  { id: 'cap-003', scope: 'project', name: 'Daily Budget', limit: 10, used: 6.20, period: 'daily', isActive: true },
]

export const useFinopsStore = defineStore('finops', () => {
  const models = ref<CostByModel[]>([...MOCK_MODELS])
  const components = ref<CostByComponent[]>([...MOCK_COMPONENTS])
  const tasks = ref<CostByTask[]>([...MOCK_TASKS])
  const roi = ref<ROIMetric[]>([...MOCK_ROI])
  const alerts = ref<BudgetAlert[]>([...MOCK_ALERTS])
  const caps = ref<CostCap[]>([...MOCK_CAPS])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const metrics = computed<FinOpsMetrics>(() => {
    const totalCost = models.value.reduce((s, m) => s + m.cost, 0)
    const totalTokens = models.value.reduce((s, m) => s + m.totalTokens, 0)
    const totalRequests = models.value.reduce((s, m) => s + m.requests, 0)
    const avgCost = totalRequests > 0 ? totalCost / totalRequests : 0
    const hoursSaved = roi.value[0]?.humanHoursSaved || 0
    const humanCost = roi.value[0]?.humanCostEquivalent || 0
    const overallROI = totalCost > 0 ? ((humanCost - totalCost) / totalCost) * 100 : 0
    return { totalCost, totalTokens, totalRequests, avgCostPerRequest: avgCost, estimatedHumanHoursSaved: hoursSaved, estimatedHumanCostSaved: humanCost, overallROI }
  })

  const criticalAlerts = computed(() => alerts.value.filter(a => a.severity === 'critical'))
  const warningAlerts = computed(() => alerts.value.filter(a => a.severity === 'warning'))

  async function updateCap(id: string, data: Partial<CostCap>) {
    loading.value = true
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        const idx = caps.value.findIndex(c => c.id === id)
        if (idx !== -1) caps.value[idx] = { ...caps.value[idx], ...data }
        loading.value = false
        resolve()
      }, 300)
    })
  }

  async function toggleCap(id: string) {
    const cap = caps.value.find(c => c.id === id)
    if (cap) await updateCap(id, { isActive: !cap.isActive })
  }

  return {
    models, components, tasks, roi, alerts, caps, loading, error,
    metrics, criticalAlerts, warningAlerts,
    updateCap, toggleCap,
  }
})
