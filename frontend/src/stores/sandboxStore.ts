import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SandboxRule, SimulationResult, SandboxMetrics } from '@/types/sandbox'

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
  },
  {
    id: 'sim-002',
    ruleId: 'sbx-004',
    ruleName: 'No Self-Referencing Dependencies',
    status: 'completed',
    startedAt: '2026-09-19T11:00:00Z',
    completedAt: '2026-09-19T11:00:01Z',
    totalEdgesChecked: 47,
    violatingEdges: 0,
    violations: [],
  },
]

export const useSandboxStore = defineStore('sandbox', () => {
  const rules = ref<SandboxRule[]>([...MOCK_RULES])
  const simulations = ref<SimulationResult[]>([...MOCK_SIMULATIONS])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeRule = ref<SandboxRule | null>(null)
  const currentSimulation = ref<SimulationResult | null>(null)

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

  async function createRule(data: Partial<SandboxRule>): Promise<SandboxRule> {
    loading.value = true
    error.value = null
    return new Promise((resolve) => {
      setTimeout(() => {
        const newRule: SandboxRule = {
          id: `sbx-${String(rules.value.length + 1).padStart(3, '0')}`,
          name: data.name || 'Untitled Rule',
          description: data.description || '',
          format: data.format || 'cypher',
          severity: data.severity || 'SOFT',
          code: data.code || '',
          scope: data.scope || 'project',
          category: data.category || 'ARCHITECTURE',
          isDraft: true,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
        rules.value.push(newRule)
        loading.value = false
        resolve(newRule)
      }, 300)
    })
  }

  async function updateRule(id: string, data: Partial<SandboxRule>): Promise<void> {
    loading.value = true
    error.value = null
    return new Promise((resolve) => {
      setTimeout(() => {
        const idx = rules.value.findIndex(r => r.id === id)
        if (idx !== -1) {
          rules.value[idx] = { ...rules.value[idx], ...data, updatedAt: new Date().toISOString() }
        }
        loading.value = false
        resolve()
      }, 300)
    })
  }

  async function deleteRule(id: string): Promise<void> {
    loading.value = true
    return new Promise((resolve) => {
      setTimeout(() => {
        rules.value = rules.value.filter(r => r.id !== id)
        if (activeRule.value?.id === id) activeRule.value = null
        loading.value = false
        resolve()
      }, 300)
    })
  }

  async function simulateRule(ruleId: string): Promise<SimulationResult> {
    loading.value = true
    error.value = null
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const rule = rules.value.find(r => r.id === ruleId)
        if (!rule) {
          error.value = 'Rule not found'
          loading.value = false
          reject(new Error('Rule not found'))
          return
        }

        const totalEdges = 47
        const violationsCount = rule.severity === 'HARD' ? Math.floor(Math.random() * 5) : Math.floor(Math.random() * 10)
        const violations = Array.from({ length: violationsCount }, (_, i) => ({
          edgeFrom: `Component-${String.fromCharCode(65 + i)}`,
          edgeTo: `Component-${String.fromCharCode(65 + ((i + 1) % 26))}`,
          edgeType: 'DEPENDS_ON',
          constraint: rule.name,
          severity: rule.severity,
          message: `Edge violates ${rule.name} constraint`,
        }))

        const result: SimulationResult = {
          id: `sim-${String(simulations.value.length + 1).padStart(3, '0')}`,
          ruleId,
          ruleName: rule.name,
          status: 'completed',
          startedAt: new Date().toISOString(),
          completedAt: new Date(Date.now() + 2000).toISOString(),
          totalEdgesChecked: totalEdges,
          violatingEdges: violationsCount,
          violations,
        }

        simulations.value.push(result)
        currentSimulation.value = result
        loading.value = false
        resolve(result)
      }, 1500)
    })
  }

  async function promoteRule(id: string): Promise<void> {
    loading.value = true
    return new Promise((resolve) => {
      setTimeout(() => {
        const idx = rules.value.findIndex(r => r.id === id)
        if (idx !== -1) {
          rules.value[idx] = { ...rules.value[idx], isDraft: false, updatedAt: new Date().toISOString() }
        }
        loading.value = false
        resolve()
      }, 500)
    })
  }

  async function fetchRules(): Promise<void> {
    loading.value = true
    return new Promise((resolve) => {
      setTimeout(() => {
        rules.value = [...MOCK_RULES]
        loading.value = false
        resolve()
      }, 200)
    })
  }

  return {
    rules,
    simulations,
    loading,
    error,
    activeRule,
    currentSimulation,
    metrics,
    latestSimulation,
    createRule,
    updateRule,
    deleteRule,
    simulateRule,
    promoteRule,
    fetchRules,
  }
})
