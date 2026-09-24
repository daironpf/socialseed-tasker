import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useIssuesStore } from '@/stores/issuesStore'
import type {
  GovernanceActionId,
  GovernanceAgentType,
  GovernanceRiskLevel,
  PermissionMatrix,
  PermissionState,
  RestrictedActionAlert,
} from '@/types/governance'
import {
  GOVERNANCE_ACTIONS,
  GOVERNANCE_AGENT_TYPES,
  GOVERNANCE_RISK_LEVELS,
} from '@/types/governance'

const LS_KEY = 'governance-matrix-v1'

function defaultMatrix(): PermissionMatrix {
  const m = {} as PermissionMatrix
  for (const agent of GOVERNANCE_AGENT_TYPES) {
    m[agent] = {} as PermissionMatrix[GovernanceAgentType]
    for (const risk of GOVERNANCE_RISK_LEVELS) {
      m[agent][risk] = {} as PermissionMatrix[GovernanceAgentType][GovernanceRiskLevel]
      for (const action of GOVERNANCE_ACTIONS) {
        m[agent][risk][action] = 'auto'
      }
    }
  }
  const set = (
    agent: GovernanceAgentType,
    risk: GovernanceRiskLevel,
    action: GovernanceActionId,
    state: PermissionState,
  ) => {
    m[agent][risk][action] = state
  }
  for (const risk of GOVERNANCE_RISK_LEVELS) {
    set('CODING', risk, 'write_code', 'auto')
    set('DATA', risk, 'external_api', 'auto')
  }
  set('CODING', 'MEDIUM', 'push_pr', 'approval')
  set('CODING', 'HIGH', 'push_pr', 'approval')
  set('CODING', 'CRITICAL', 'push_pr', 'approval')
  set('CODING', 'HIGH', 'modify_db', 'approval')
  set('CODING', 'CRITICAL', 'modify_db', 'blocked')
  set('CODING', 'CRITICAL', 'delete_resource', 'blocked')
  set('DEPLOY', 'LOW', 'deploy', 'approval')
  set('DEPLOY', 'MEDIUM', 'deploy', 'approval')
  set('DEPLOY', 'HIGH', 'deploy', 'approval')
  set('DEPLOY', 'CRITICAL', 'deploy', 'blocked')
  set('DEPLOY', 'HIGH', 'config_change', 'approval')
  set('DEPLOY', 'CRITICAL', 'config_change', 'approval')
  set('DEPLOY', 'MEDIUM', 'delete_resource', 'approval')
  set('DEPLOY', 'HIGH', 'delete_resource', 'blocked')
  set('DEPLOY', 'CRITICAL', 'delete_resource', 'blocked')
  set('DATA', 'MEDIUM', 'modify_db', 'approval')
  set('DATA', 'HIGH', 'modify_db', 'approval')
  set('DATA', 'CRITICAL', 'modify_db', 'blocked')
  set('DATA', 'HIGH', 'delete_resource', 'approval')
  set('DATA', 'CRITICAL', 'delete_resource', 'blocked')
  set('OPS', 'LOW', 'config_change', 'approval')
  set('OPS', 'MEDIUM', 'config_change', 'approval')
  set('OPS', 'HIGH', 'config_change', 'approval')
  set('OPS', 'CRITICAL', 'config_change', 'blocked')
  set('OPS', 'HIGH', 'delete_resource', 'blocked')
  set('OPS', 'CRITICAL', 'delete_resource', 'blocked')
  set('OPS', 'CRITICAL', 'external_api', 'blocked')
  for (const risk of GOVERNANCE_RISK_LEVELS) {
    set('CODING', risk, 'delete_resource', risk === 'LOW' ? 'approval' : m['CODING'][risk]['delete_resource'])
    set('DEPLOY', risk, 'push_pr', 'approval')
    set('DATA', risk, 'push_pr', 'approval')
    set('OPS', risk, 'deploy', 'approval')
  }
  return m
}

function loadMatrix(): PermissionMatrix {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (raw) return JSON.parse(raw) as PermissionMatrix
  } catch {
    // corrupted -> fall through to defaults
  }
  return defaultMatrix()
}

export const useGovernanceStore = defineStore('governance', () => {
  const matrix = ref<PermissionMatrix>(loadMatrix())
  const alerts = ref<RestrictedActionAlert[]>([])

  const activeAlerts = computed(() => alerts.value.filter((a) => !a.resolved))
  const resolvedAlerts = computed(() => alerts.value.filter((a) => a.resolved))
  const pausedCount = computed(() => activeAlerts.value.filter((a) => a.paused).length)

  function getCell(
    agent: GovernanceAgentType,
    risk: GovernanceRiskLevel,
    action: GovernanceActionId,
  ): PermissionState {
    return matrix.value[agent]?.[risk]?.[action] ?? 'auto'
  }

  function cycleState(current: PermissionState): PermissionState {
    if (current === 'auto') return 'approval'
    if (current === 'approval') return 'blocked'
    return 'auto'
  }

  function setCell(
    agent: GovernanceAgentType,
    risk: GovernanceRiskLevel,
    action: GovernanceActionId,
    state: PermissionState,
  ) {
    matrix.value[agent][risk][action] = state
    persist()
  }

  function toggleCell(
    agent: GovernanceAgentType,
    risk: GovernanceRiskLevel,
    action: GovernanceActionId,
  ): PermissionState {
    const next = cycleState(getCell(agent, risk, action))
    setCell(agent, risk, action, next)
    return next
  }

  function persist() {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(matrix.value))
    } catch {
      // storage full/unavailable; keep in-memory copy
    }
  }

  function resetMatrix() {
    matrix.value = defaultMatrix()
    persist()
  }

  function simulateRestrictedAction(params: {
    agentType: GovernanceAgentType
    riskLevel: GovernanceRiskLevel
    action: GovernanceActionId
    agentName?: string
    issueId?: string
    issueTitle?: string
    command?: string
  }): RestrictedActionAlert {
    const state = getCell(params.agentType, params.riskLevel, params.action)
    const issuesStore = useIssuesStore()
    const issueId = params.issueId || ''
    const alert: RestrictedActionAlert = {
      id: `alert-${Date.now()}`,
      agentType: params.agentType,
      agentName: params.agentName || `${params.agentType.toLowerCase()}-agent`,
      riskLevel: params.riskLevel,
      action: params.action,
      issueId,
      issueTitle: params.issueTitle || '',
      command: params.command || `${params.action} @ ${params.riskLevel}`,
      permissionState: state,
      createdAt: new Date().toISOString(),
      paused: state === 'approval',
      resolved: state !== 'approval',
      decision: state === 'blocked' ? 'rejected' : state === 'auto' ? 'approved' : null,
    }
    alerts.value.unshift(alert)

    if (alert.paused && issueId) {
      issuesStore.updateIssue(issueId, { agent_working: false }).catch(() => undefined)
    }
    return alert
  }

  function resolveAlert(
    id: string,
    decision: 'approved' | 'rejected',
  ): RestrictedActionAlert | null {
    const alert = alerts.value.find((a) => a.id === id)
    if (!alert) return null
    alert.resolved = true
    alert.decision = decision
    alert.paused = false

    if (alert.issueId) {
      const issuesStore = useIssuesStore()
      if (decision === 'approved') {
        issuesStore.updateIssue(alert.issueId, { agent_working: true }).catch(() => undefined)
      } else {
        issuesStore.updateIssue(alert.issueId, { agent_working: false }).catch(() => undefined)
      }
    }
    return alert
  }

  return {
    matrix,
    alerts,
    activeAlerts,
    resolvedAlerts,
    pausedCount,
    getCell,
    setCell,
    toggleCell,
    cycleState,
    resetMatrix,
    simulateRestrictedAction,
    resolveAlert,
  }
})
