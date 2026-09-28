export type SandboxRuleFormat = 'json' | 'cypher' | 'yaml'

export type SandboxRuleSeverity = 'HARD' | 'SOFT'

export interface SandboxRule {
  id: string
  name: string
  description: string
  format: SandboxRuleFormat
  severity: SandboxRuleSeverity
  code: string
  scope: string
  category: string
  isDraft: boolean
  createdAt: string
  updatedAt: string
}

export type SimulationStatus = 'idle' | 'running' | 'completed' | 'failed'

export interface SimulationViolation {
  edgeFrom: string
  edgeTo: string
  edgeType: string
  constraint: string
  severity: SandboxRuleSeverity
  message: string
}

export interface MatchedNode {
  id: string
  title: string
  component: string | null
  status?: string
  priority?: string
}

export interface BlastRadiusSummary {
  direct: number
  total: number
  maxDepth: number
  critical: number
  high: number
}

export type SimulationDataSource = 'api' | 'fallback'

export interface SimulationResult {
  id: string
  ruleId: string
  ruleName: string
  status: SimulationStatus
  startedAt: string
  completedAt: string | null
  totalNodesChecked: number
  totalEdgesChecked: number
  violatingEdges: number
  violations: SimulationViolation[]
  matchedNodes: MatchedNode[]
  blastRadius: BlastRadiusSummary | null
  dataSource: SimulationDataSource
  truncated: boolean
  error?: string
}

export interface SandboxMetrics {
  totalRules: number
  draftRules: number
  activeRules: number
  totalSimulations: number
  lastSimulationAt: string | null
}
