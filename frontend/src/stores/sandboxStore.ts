import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  SandboxRule,
  SandboxRuleFormat,
  SimulationDataSource,
  SimulationResult,
  SandboxMetrics,
} from '@/types/sandbox'
import type { EngineResult, GraphData, RuleEvaluationTarget } from '@/utils/ruleEngine'
import { evaluateRule } from '@/utils/ruleEngine'
import { buildGraphFromIssues, fetchDependencyGraph } from '@/api/graphApi'
import { fetchIssues } from '@/api/issuesApi'
import { fetchComponents } from '@/api/componentsApi'

const RULES_STORAGE_KEY = 'socialseed-sandbox-rules'

const MOCK_RULES: SandboxRule[] = [
  {
    id: 'sbx-001',
    name: 'No Circular Layer Dependencies',
    description: 'Ensures frontend components cannot depend on backend services directly',
    format: 'cypher',
    severity: 'HARD',
    code: `MATCH (a:Component)-[r:DEPENDS_ON]->(b:Component)\nWHERE a.layer = 'frontend' AND b.layer = 'backend'\nRETURN a.name AS violator, b.name AS dependency`,
    scope: 'project',
    category: 'ARCHITECTURE',
    isDraft: false,
    createdAt: '2026-09-15T10:00:00Z',
    updatedAt: '2026-09-15T10:00:00Z',
  },
  {
    id: 'sbx-002',
    name: 'Max Dependencies per Component',
    description: 'No component should depend on more than 5 other components',
    format: 'cypher',
    severity: 'SOFT',
    code: `MATCH (c:Component)-[r:DEPENDS_ON]->(d:Component)\nWITH c, COUNT(d) AS depCount\nWHERE depCount > 5\nRETURN c.name AS component, depCount`,
    scope: 'component',
    category: 'DEPENDENCIES',
    isDraft: true,
    createdAt: '2026-09-18T14:30:00Z',
    updatedAt: '2026-09-18T14:30:00Z',
  },
  {
    id: 'sbx-003',
    name: 'Required Label: priority',
    description: 'All issues must have a priority label assigned',
    format: 'yaml',
    severity: 'SOFT',
    code: `constraint:\n  name: required-priority-label\n  target: issue\n  field: labels\n  condition: contains\n  value: priority\n  message: "Issue must have a priority label"`,
    scope: 'issue',
    category: 'NAMING',
    isDraft: true,
    createdAt: '2026-09-19T09:15:00Z',
    updatedAt: '2026-09-19T09:15:00Z',
  },
  {
    id: 'sbx-004',
    name: 'No Self-Referencing Dependencies',
    description: 'Issues cannot depend on themselves',
    format: 'cypher',
    severity: 'HARD',
    code: `MATCH (i:Issue)-[r:DEPENDS_ON]->(i)\nRETURN i.name AS self_referencing_issue`,
    scope: 'project',
    category: 'DEPENDENCIES',
    isDraft: false,
    createdAt: '2026-09-10T08:00:00Z',
    updatedAt: '2026-09-10T08:00:00Z',
  },
]

const MOCK_SIMULATIONS: SimulationResult[] = [
  {
    id: 'sim-001',
    ruleId: 'sbx-001',
    ruleName: 'No Circular Layer Dependencies',
    status: 'completed',
    startedAt: '2026-09-19T10:00:00Z',
    completedAt: '2026-09-19T10:00:03Z',
    totalNodesChecked: 12,
    totalEdgesChecked: 47,
    violatingEdges: 2,
    violations: [
      {
        edgeFrom: 'TaskerBoard',
        edgeTo: 'FastAPI',
        edgeType: 'DEPENDS_ON',
        constraint: 'No Circular Layer Dependencies',
        severity: 'HARD',
        message: 'Frontend component TaskerBoard depends on backend service FastAPI',
      },
      {
        edgeFrom: 'MockAPI',
        edgeTo: 'Neo4jDriver',
        edgeType: 'DEPENDS_ON',
        constraint: 'No Circular Layer Dependencies',
        severity: 'HARD',
        message: 'Frontend component MockAPI depends on backend service Neo4jDriver',
      },
    ],
    matchedNodes: [],
    blastRadius: null,
    dataSource: 'fallback',
    truncated: false,
  },
  {
    id: 'sim-002',
    ruleId: 'sbx-004',
    ruleName: 'No Self-Referencing Dependencies',
    status: 'completed',
    startedAt: '2026-09-19T11:00:00Z',
    completedAt: '2026-09-19T11:00:01Z',
    totalNodesChecked: 12,
    totalEdgesChecked: 47,
    violatingEdges: 0,
    violations: [],
    matchedNodes: [],
    blastRadius: null,
    dataSource: 'fallback',
    truncated: false,
  },
]

const FALLBACK_GRAPH: GraphData = {
  nodes: [
    { id: 'fb-1', title: 'TaskerBoard UI', component: 'Frontend', status: 'OPEN', priority: 'HIGH', labels: ['ui'] },
    { id: 'fb-2', title: 'Auth flow', component: 'Frontend', status: 'IN_PROGRESS', priority: 'CRITICAL', labels: [] },
    { id: 'fb-3', title: 'REST API', component: 'Backend', status: 'OPEN', priority: 'HIGH', labels: ['api'] },
    { id: 'fb-4', title: 'Graph analysis', component: 'Backend', status: 'BLOCKED', priority: 'CRITICAL', labels: [] },
    { id: 'fb-5', title: 'Neo4j driver', component: 'Database', status: 'OPEN', priority: 'MEDIUM', labels: ['db'] },
    { id: 'fb-6', title: 'Mock API', component: 'Frontend', status: 'OPEN', priority: 'LOW', labels: ['mock'] },
  ],
  edges: [
    { from: 'fb-1', to: 'fb-3', type: 'DEPENDS_ON' },
    { from: 'fb-2', to: 'fb-3', type: 'DEPENDS_ON' },
    { from: 'fb-6', to: 'fb-5', type: 'DEPENDS_ON' },
    { from: 'fb-3', to: 'fb-5', type: 'DEPENDS_ON' },
    { from: 'fb-4', to: 'fb-5', type: 'DEPENDS_ON' },
    { from: 'fb-3', to: 'fb-4', type: 'DEPENDS_ON' },
  ],
}

function loadPersistedRules(): SandboxRule[] | null {
  try {
    const raw = localStorage.getItem(RULES_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed) && parsed.every(item => item && typeof item.id === 'string' && typeof item.code === 'string')) {
      return parsed as SandboxRule[]
    }
    return null
  } catch {
    return null
  }
}

function persistRules(rules: SandboxRule[]): void {
  try {
    localStorage.setItem(RULES_STORAGE_KEY, JSON.stringify(rules))
  } catch {
    return
  }
}

function nextRuleId(existing: SandboxRule[]): string {
  let candidate = `sbx-${Date.now().toString(36)}`
  while (existing.some(rule => rule.id === candidate)) {
    candidate = `sbx-${Math.random().toString(36).slice(2, 8)}`
  }
  return candidate
}

export const useSandboxStore = defineStore('sandbox', () => {
  const rules = ref<SandboxRule[]>(loadPersistedRules() ?? [...MOCK_RULES])
  const simulations = ref<SimulationResult[]>([...MOCK_SIMULATIONS])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeRule = ref<SandboxRule | null>(null)
  const currentSimulation = ref<SimulationResult | null>(null)
  const graphData = ref<GraphData | null>(null)
  const graphSource = ref<SimulationDataSource>('fallback')
  const graphLoading = ref(false)

  const metrics = computed<SandboxMetrics>(() => ({
    totalRules: rules.value.length,
    draftRules: rules.value.filter(r => r.isDraft).length,
    activeRules: rules.value.filter(r => !r.isDraft).length,
    totalSimulations: simulations.value.length,
    lastSimulationAt: simulations.value.length > 0
      ? simulations.value[simulations.value.length - 1].startedAt
      : null,
  }))

  const latestSimulation = computed(() => {
    if (simulations.value.length === 0) return null
    return [...simulations.value].sort(
      (a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime()
    )[0]
  })

  async function loadGraph(options?: { force?: boolean }): Promise<GraphData> {
    if (graphData.value && !options?.force) return graphData.value
    graphLoading.value = true
    try {
      const live = await fetchDependencyGraph()
      if (live) {
        graphData.value = live
        graphSource.value = 'api'
        return live
      }
      try {
        const [issuesResult, components] = await Promise.all([
          fetchIssues(1, 200),
          fetchComponents().catch(() => []),
        ])
        if (issuesResult.items.length > 0) {
          const built = buildGraphFromIssues(issuesResult.items, components)
          graphData.value = built
          graphSource.value = 'fallback'
          return built
        }
      } catch {
        graphData.value = FALLBACK_GRAPH
        graphSource.value = 'fallback'
        return FALLBACK_GRAPH
      }
      graphData.value = FALLBACK_GRAPH
      graphSource.value = 'fallback'
      return FALLBACK_GRAPH
    } finally {
      graphLoading.value = false
    }
  }

  async function createRule(data: Partial<SandboxRule>): Promise<SandboxRule> {
    loading.value = true
    error.value = null
    try {
      const now = new Date().toISOString()
      const newRule: SandboxRule = {
        id: nextRuleId(rules.value),
        name: data.name || 'Untitled Rule',
        description: data.description || '',
        format: (data.format || 'json') as SandboxRuleFormat,
        severity: data.severity || 'SOFT',
        code: data.code || '',
        scope: data.scope || 'project',
        category: data.category || 'ARCHITECTURE',
        isDraft: true,
        createdAt: now,
        updatedAt: now,
      }
      rules.value.push(newRule)
      persistRules(rules.value)
      return newRule
    } finally {
      loading.value = false
    }
  }

  async function updateRule(id: string, data: Partial<SandboxRule>): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const idx = rules.value.findIndex(r => r.id === id)
      if (idx !== -1) {
        rules.value[idx] = { ...rules.value[idx], ...data, updatedAt: new Date().toISOString() }
        persistRules(rules.value)
      }
    } finally {
      loading.value = false
    }
  }

  async function deleteRule(id: string): Promise<void> {
    loading.value = true
    try {
      rules.value = rules.value.filter(r => r.id !== id)
      if (activeRule.value?.id === id) activeRule.value = null
      persistRules(rules.value)
    } finally {
      loading.value = false
    }
  }

  function toSimulationResult(
    rule: SandboxRule,
    engineResult: EngineResult,
    source: SimulationDataSource,
  ): SimulationResult {
    const now = new Date().toISOString()
    return {
      id: `sim-${simulations.value.length + 1}-${Date.now().toString(36)}`,
      ruleId: rule.id,
      ruleName: rule.name,
      status: engineResult.status,
      startedAt: now,
      completedAt: now,
      totalNodesChecked: engineResult.totalNodesChecked,
      totalEdgesChecked: engineResult.totalEdgesChecked,
      violatingEdges: engineResult.violations.length,
      violations: engineResult.violations,
      matchedNodes: engineResult.matchedNodes,
      blastRadius: engineResult.blastRadius,
      dataSource: source,
      truncated: engineResult.truncated,
      error: engineResult.error,
    }
  }

  async function simulateRule(ruleId: string): Promise<SimulationResult> {
    loading.value = true
    error.value = null
    try {
      const rule = rules.value.find(r => r.id === ruleId)
      if (!rule) {
        throw new Error('Rule not found')
      }
      const graph = await loadGraph()
      const engineResult = evaluateRule(rule, graph)
      const result = toSimulationResult(rule, engineResult, graphSource.value)
      simulations.value.push(result)
      currentSimulation.value = result
      return result
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function simulatePreview(
    target: RuleEvaluationTarget,
  ): Promise<{ result: EngineResult; dataSource: SimulationDataSource }> {
    loading.value = true
    error.value = null
    try {
      const graph = await loadGraph()
      const result = evaluateRule(target, graph)
      return { result, dataSource: graphSource.value }
    } catch (e) {
      error.value = (e as Error).message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function promoteRule(id: string): Promise<void> {
    loading.value = true
    try {
      const idx = rules.value.findIndex(r => r.id === id)
      if (idx !== -1) {
        rules.value[idx] = { ...rules.value[idx], isDraft: false, updatedAt: new Date().toISOString() }
        persistRules(rules.value)
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchRules(): Promise<void> {
    const stored = loadPersistedRules()
    if (stored && stored.length > 0) {
      rules.value = stored
    } else {
      persistRules(rules.value)
    }
  }

  return {
    rules,
    simulations,
    loading,
    error,
    activeRule,
    currentSimulation,
    graphData,
    graphSource,
    graphLoading,
    metrics,
    latestSimulation,
    loadGraph,
    createRule,
    updateRule,
    deleteRule,
    simulateRule,
    simulatePreview,
    promoteRule,
    fetchRules,
  }
})
