import client from './client'
import type { APIResponse, Issue } from '@/types'

export type UserIssueKind = 'assigned' | 'created' | 'completed'

export interface UserIssueStats {
  assigned: number
  created: number
  completed: number
}

export async function fetchUserIssueStats(userId: string): Promise<UserIssueStats> {
  const { data } = await client.get<APIResponse<UserIssueStats>>(`/users/${userId}/issue-stats`)
  if (!data.data) throw new Error('Failed to fetch issue stats')
  return data.data
}

export async function fetchUserIssues(userId: string, kind: UserIssueKind): Promise<Issue[]> {
  const { data } = await client.get<APIResponse<Issue[]>>(`/users/${userId}/issues`, {
    params: { kind },
  })
  return data.data ?? []
}
