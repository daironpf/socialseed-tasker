import client from './client'
import type { APIResponse, Issue } from '@/types'

export type ConflictResolution = 'local' | 'remote' | 'merge'

export async function resyncIssue(issueId: string): Promise<Issue> {
  const { data } = await client.post<APIResponse<Issue>>(`/issues/${issueId}/github-sync`)
  if (!data.data) throw new Error('GitHub re-sync failed')
  return data.data
}

export async function resolveConflict(
  issueId: string,
  resolution: ConflictResolution,
  fields?: Record<string, unknown>,
): Promise<Issue> {
  const { data } = await client.post<APIResponse<Issue>>(`/issues/${issueId}/github-sync/resolve`, {
    resolution,
    fields: fields ?? null,
  })
  if (!data.data) throw new Error('Conflict resolution failed')
  return data.data
}
