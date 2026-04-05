import client from './client'
import type { APIResponse, Issue, DependencyRequest } from '@/types'

export async function addDependency(
  issueId: string,
  body: DependencyRequest,
): Promise<void> {
  await client.post(`/issues/${issueId}/dependencies`, body)
}

export async function removeDependency(
  issueId: string,
  dependsOnId: string,
): Promise<void> {
  await client.delete(`/issues/${issueId}/dependencies/${dependsOnId}`)
}

export async function fetchDependencies(issueId: string): Promise<Issue[]> {
  const { data } = await client.get<APIResponse<Issue[]>>(`/issues/${issueId}/dependencies`)
  return data.data ?? []
}

export async function fetchDependents(issueId: string): Promise<Issue[]> {
  const { data } = await client.get<APIResponse<Issue[]>>(`/issues/${issueId}/dependents`)
  return data.data ?? []
}

export async function fetchDependencyChain(issueId: string): Promise<Issue[]> {
  const { data } = await client.get<APIResponse<Issue[]>>(`/issues/${issueId}/dependency-chain`)
  return data.data ?? []
}
