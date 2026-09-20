export interface ExecutiveKPI {
  label: string
  value: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  trendValue: number
  icon: string
  color: string
}

export interface CycleTimeData {
  category: string
  humanMinutes: number
  agentMinutes: number
}

export interface DebtReduction {
  month: string
  resolved: number
  created: number
  netReduction: number
}

export interface ComplianceItem {
  area: string
  score: number
  status: 'pass' | 'warn' | 'fail'
}
