export type GovernanceAgentType = 'CODING' | 'DEPLOY' | 'DATA' | 'OPS'

export type GovernanceRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type PermissionState = 'auto' | 'approval' | 'blocked'

export type GovernanceActionId =
  | 'write_code'
  | 'push_pr'
  | 'modify_db'
  | 'delete_resource'
  | 'deploy'
  | 'config_change'
  | 'external_api'

export const GOVERNANCE_ACTIONS: GovernanceActionId[] = [
  'write_code',
  'push_pr',
  'modify_db',
  'delete_resource',
  'deploy',
  'config_change',
  'external_api',
]

export const GOVERNANCE_AGENT_TYPES: GovernanceAgentType[] = ['CODING', 'DEPLOY', 'DATA', 'OPS']

export const GOVERNANCE_RISK_LEVELS: GovernanceRiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export type PermissionMatrix = Record<
  GovernanceAgentType,
  Record<GovernanceRiskLevel, Record<GovernanceActionId, PermissionState>>
>

export interface RestrictedActionAlert {
  id: string
  agentType: GovernanceAgentType
  agentName: string
  riskLevel: GovernanceRiskLevel
  action: GovernanceActionId
  issueId: string
  issueTitle: string
  command: string
  permissionState: PermissionState
  createdAt: string
  paused: boolean
  resolved: boolean
  decision: 'approved' | 'rejected' | null
}
