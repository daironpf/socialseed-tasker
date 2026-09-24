import type { IssuePriority } from '@/types'

export type SLAStatus = 'on_track' | 'at_risk' | 'breached'

export const SLA_HOURS: Record<IssuePriority, number> = {
  CRITICAL: 4,
  HIGH: 24,
  MEDIUM: 72,
  LOW: 168,
}

export interface SLAIssueMetric {
  issueId: string
  title: string
  priority: IssuePriority
  projectId: string
  ageHours: number
  slaHours: number
  hoursLeft: number
  percentUsed: number
  dueAt: string
  status: SLAStatus
}

export interface MTTRPoint {
  period: string
  before: number
  after: number | null
}

export interface HealingPoint {
  period: string
  successRate: number
  completed: number
  failed: number
}

export interface ProjectBudget {
  projectId: string
  label: string
  spent: number
  budget: number
}

export interface PeriodComparison {
  resolved: { current: number; previous: number; deltaPct: number }
  mttr: { current: number; previous: number; deltaPct: number }
}

export interface ReportKPI {
  label: string
  value: string
  sub: string
  tone: 'good' | 'warn' | 'bad' | 'neutral'
}

export type ReportExceptionKind = 'sla_breach' | 'sla_risk' | 'budget' | 'healing_failure'

export interface ReportException {
  id: string
  kind: ReportExceptionKind
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  title: string
  detail: string
}

export interface ExecutiveReport {
  id: string
  type: 'weekly' | 'monthly'
  generatedAt: string
  periodStart: string
  periodEnd: string
  kpis: ReportKPI[]
  exceptions: ReportException[]
}
