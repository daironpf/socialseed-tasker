import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ExecutiveKPI, CycleTimeData, DebtReduction, ComplianceItem } from '@/types/executive'

const MOCK_KPIS: ExecutiveKPI[] = [
  { label: 'Agent Autonomous Success Rate', value: 87.3, unit: '%', trend: 'up', trendValue: 4.2, icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', color: 'green' },
  { label: 'Technical Debt Reduction Rate', value: 23.1, unit: '%', trend: 'up', trendValue: 8.5, icon: 'M19 14l-7 7m0 0l-7-7m7 7V3', color: 'blue' },
  { label: 'Architecture Compliance Score', value: 94.6, unit: '/100', trend: 'stable', trendValue: 0.3, icon: 'M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z', color: 'purple' },
  { label: 'Mean Time to Resolution', value: 4.2, unit: 'min', trend: 'down', trendValue: 1.8, icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', color: 'amber' },
]

const MOCK_CYCLE_TIME: CycleTimeData[] = [
  { category: 'Bug Fix', humanMinutes: 45, agentMinutes: 8 },
  { category: 'Feature', humanMinutes: 120, agentMinutes: 22 },
  { category: 'Refactor', humanMinutes: 90, agentMinutes: 15 },
  { category: 'Test', humanMinutes: 30, agentMinutes: 5 },
  { category: 'Doc', humanMinutes: 20, agentMinutes: 3 },
  { category: 'Security', humanMinutes: 60, agentMinutes: 12 },
]

const MOCK_DEBT: DebtReduction[] = [
  { month: 'Apr', resolved: 18, created: 12, netReduction: 6 },
  { month: 'May', resolved: 22, created: 10, netReduction: 12 },
  { month: 'Jun', resolved: 28, created: 14, netReduction: 14 },
  { month: 'Jul', resolved: 15, created: 8, netReduction: 7 },
  { month: 'Aug', resolved: 32, created: 11, netReduction: 21 },
  { month: 'Sep', resolved: 25, created: 9, netReduction: 16 },
]

const MOCK_COMPLIANCE: ComplianceItem[] = [
  { area: 'Type Safety', score: 98, status: 'pass' },
  { area: 'Test Coverage', score: 92, status: 'pass' },
  { area: 'Documentation', score: 85, status: 'pass' },
  { area: 'Error Handling', score: 78, status: 'warn' },
  { area: 'Security Patches', score: 95, status: 'pass' },
  { area: 'Dependency Updates', score: 65, status: 'warn' },
  { area: 'Code Review', score: 100, status: 'pass' },
]

export const useExecutiveStore = defineStore('executive', () => {
  const kpis = ref<ExecutiveKPI[]>([...MOCK_KPIS])
  const cycleTime = ref<CycleTimeData[]>([...MOCK_CYCLE_TIME])
  const debt = ref<DebtReduction[]>([...MOCK_DEBT])
  const compliance = ref<ComplianceItem[]>([...MOCK_COMPLIANCE])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const overallCompliance = computed(() => {
    const total = compliance.value.reduce((s, c) => s + c.score, 0)
    return Math.round(total / compliance.value.length)
  })

  const totalDebtReduction = computed(() => debt.value.reduce((s, d) => s + d.netReduction, 0))

  const avgSpeedup = computed(() => {
    const totalHuman = cycleTime.value.reduce((s, c) => s + c.humanMinutes, 0)
    const totalAgent = cycleTime.value.reduce((s, c) => s + c.agentMinutes, 0)
    return totalAgent > 0 ? Math.round(totalHuman / totalAgent) : 0
  })

  function formatTrend(trend: string, value: number) {
    if (trend === 'up') return `+${value}%`
    if (trend === 'down') return `-${value}%`
    return `~${value}%`
  }

  function complianceColor(score: number) {
    if (score >= 90) return 'text-green-600 dark:text-green-400'
    if (score >= 75) return 'text-amber-600 dark:text-amber-400'
    return 'text-red-600 dark:text-red-400'
  }

  function complianceBg(score: number) {
    if (score >= 90) return 'bg-green-500'
    if (score >= 75) return 'bg-amber-500'
    return 'bg-red-500'
  }

  return {
    kpis, cycleTime, debt, compliance, loading, error,
    overallCompliance, totalDebtReduction, avgSpeedup,
    formatTrend, complianceColor, complianceBg,
  }
})
