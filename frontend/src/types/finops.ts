export interface ROIMetric {
  label: string
  tokenCost: number
  humanHoursSaved: number
  humanCostEquivalent: number
  roi: number
  period: string
}

export interface CostByModel {
  model: string
  provider: string
  promptTokens: number
  completionTokens: number
  totalTokens: number
  cost: number
  requests: number
}

export interface CostByComponent {
  component: string
  totalCost: number
  requests: number
  avgCostPerRequest: number
}

export interface CostByTask {
  issueId: string
  issueTitle: string
  model: string
  cost: number
  tokensUsed: number
  executionTimeMs: number
}

export interface CostHeatmapCell {
  row: string
  col: string
  value: number
}

export interface BudgetAlert {
  id: string
  type: 'issue' | 'project' | 'organizational'
  name: string
  currentCost: number
  threshold: number
  severity: 'warning' | 'critical'
  triggeredAt: string
}

export interface CostCap {
  id: string
  scope: 'project' | 'organizational'
  name: string
  limit: number
  used: number
  period: 'daily' | 'weekly' | 'monthly'
  isActive: boolean
}

export interface FinOpsMetrics {
  totalCost: number
  totalTokens: number
  totalRequests: number
  avgCostPerRequest: number
  estimatedHumanHoursSaved: number
  estimatedHumanCostSaved: number
  overallROI: number
}
