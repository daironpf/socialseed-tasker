export type EnterpriseRole = 'ENTERPRISE_ADMIN' | 'SECURITY_MANAGER' | 'DEVELOPER' | 'AUDITOR'

export type OrganizationPlan = 'STARTUP' | 'BUSINESS' | 'ENTERPRISE'

export interface OrganizationQuota {
  computeLimit: number
  computeUsed: number
  storageLimitGb: number
  storageUsedGb: number
  tokenLimit: number
  tokenUsed: number
}

export interface DataRetentionPolicy {
  days: number
  autoDelete: boolean
  exportBeforeDelete: boolean
}

export interface Workspace {
  id: string
  name: string
  department: string
  description: string
  projectIds: string[]
  members: number
  activeIssues: number
}

export interface EnterpriseAccount {
  id: string
  name: string
  email: string
  role: EnterpriseRole
  avatar: string
  isActive: boolean
}

export interface Organization {
  id: string
  name: string
  industry: string
  plan: OrganizationPlan
  defaultRole: EnterpriseRole
  workspaces: Workspace[]
  accounts: EnterpriseAccount[]
  quota: OrganizationQuota
  retention: DataRetentionPolicy
  createdAt: string
  updatedAt: string
}

export interface OrganizationCreateRequest {
  name: string
  industry?: string
  plan?: OrganizationPlan
  defaultRole?: EnterpriseRole
}
