import client from './client'
import type {
  APIResponse,
  Issue,
  IssueCreateRequest,
  IssueUpdateRequest,
  PaginatedResponse,
} from '@/types'

export async function fetchIssues(
  page = 1,
  limit = 50,
  status?: string,
  component?: string,
  project?: string,
): Promise<Issue[]> {
  const params: Record<string, string | number> = { page, limit }
  if (status) params.status = status
  if (component) params.component = component
  if (project) params.project = project
  const { data } = await client.get<APIResponse<PaginatedResponse<Issue>>>('/issues', { params })
  return data.data?.items ?? []
}

export async function fetchIssue(id: string): Promise<Issue> {
  const { data } = await client.get<APIResponse<Issue>>(`/issues/${id}`)
  if (!data.data) throw new Error('Issue not found')
  return data.data
}

export async function createIssue(body: IssueCreateRequest): Promise<Issue> {
  const { data } = await client.post<APIResponse<Issue>>('/issues', body)
  if (!data.data) throw new Error('Failed to create issue')
  return data.data
}

export async function updateIssue(id: string, body: IssueUpdateRequest): Promise<Issue> {
  const { data } = await client.patch<APIResponse<Issue>>(`/issues/${id}`, body)
  if (!data.data) throw new Error('Failed to update issue')
  return data.data
}

export async function deleteIssue(id: string): Promise<void> {
  await client.delete(`/issues/${id}`)
}

export async function closeIssue(id: string): Promise<Issue> {
  const { data } = await client.post<APIResponse<Issue>>(`/issues/${id}/close`)
  if (!data.data) throw new Error('Failed to close issue')
  return data.data
}

export async function fetchBlockedIssues(): Promise<Issue[]> {
  const { data } = await client.get<APIResponse<Issue[]>>('/blocked-issues')
  return data.data ?? []
}
