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

export async function createPolicy(policy: PolicyCreateRequest): Promise<Policy> {
  const { data } = await client.post<APIResponse<Policy>>('/policies', policy)
  return data.data!
}
