import client from './client'
import type { APIResponse, PaginatedResponse, Policy } from '@/types'

export async function fetchPolicies(): Promise<Policy[]> {
  const { data } = await client.get<APIResponse<PaginatedResponse<Policy>>>('/policies')
  const responseData = data.data
  if (Array.isArray(responseData)) {
    return responseData
  }
  return responseData?.items ?? []
}

export interface PolicyCreateRequest {
  name: string
  description?: string
  rule: string
  level?: string
  target_scope?: string
}

const SEVERITY_BY_LEVEL: Record<string, string> = {
  HARD: 'BLOCKER',
  SOFT: 'WARNING',
  INFO: 'INFO',
  WARNING: 'WARNING',
  BLOCKER: 'BLOCKER',
}

const SCOPE_BY_TARGET: Record<string, string> = {
  project: 'PROJECT',
  component: 'COMPONENT',
  issue: 'CODE_SYMBOL',
  PROJECT: 'PROJECT',
  COMPONENT: 'COMPONENT',
  COMMIT: 'COMMIT',
  CODE_SYMBOL: 'CODE_SYMBOL',
}

export async function createPolicy(policy: PolicyCreateRequest): Promise<Policy> {
  const body = {
    ...policy,
    target_scope: SCOPE_BY_TARGET[policy.target_scope ?? 'project'] ?? 'PROJECT',
    logic_definition: policy.rule,
    severity: SEVERITY_BY_LEVEL[policy.level ?? 'SOFT'] ?? 'WARNING',
  }
  const { data } = await client.post<APIResponse<Policy>>('/policies', body)
  return data.data!
}

export async function deletePolicy(id: string): Promise<void> {
  await client.delete(`/policies/${id}`)
}

export async function updatePolicy(id: string, body: Partial<PolicyCreateRequest>): Promise<Policy> {
  const { data } = await client.patch<APIResponse<Policy>>(`/policies/${id}`, body)
  return data.data!
}
