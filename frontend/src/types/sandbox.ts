export type SandboxRuleFormat = 'cypher' | 'yaml'

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

export interface SimulationResult {
  id: string
  ruleId: string
  ruleName: string
  status: SimulationStatus
  startedAt: string
  completedAt: string | null
  totalEdgesChecked: number
  violatingEdges: number
  violations: SimulationViolation[]
  error?: string
}

export interface SandboxMetrics {
  totalRules: number
  draftRules: number
  activeRules: number
  totalSimulations: number
  lastSimulationAt: string | null
}
