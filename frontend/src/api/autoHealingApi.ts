import client from './client'
import type { APIResponse } from '@/types'
import type { LogEntry, PatchMeta, PipelineRun } from '@/types/autoHealing'

const BASE = '/auto-healing/runs'

export async function fetchPipelineRuns(): Promise<PipelineRun[]> {
  const { data } = await client.get<APIResponse<PipelineRun[]>>(BASE)
  return data.data ?? []
}

export async function fetchPipelineRun(runId: string): Promise<PipelineRun> {
  const { data } = await client.get<APIResponse<PipelineRun>>(`${BASE}/${runId}`)
  if (!data.data) throw new Error('Run not found')
  return data.data
}

export async function startPipelineRun(issueId: string): Promise<PipelineRun> {
  const { data } = await client.post<APIResponse<PipelineRun>>(BASE, { issueId })
  if (!data.data) throw new Error('Failed to start pipeline run')
  return data.data
}

export async function cancelPipelineRun(runId: string): Promise<PipelineRun> {
  const { data } = await client.post<APIResponse<PipelineRun>>(`${BASE}/${runId}/cancel`)
  if (!data.data) throw new Error('Failed to cancel pipeline run')
  return data.data
}

export async function restartPipelineRun(runId: string, stageId?: string): Promise<PipelineRun> {
  const { data } = await client.post<APIResponse<PipelineRun>>(`${BASE}/${runId}/restart`, stageId ? { stageId } : {})
  if (!data.data) throw new Error('Failed to restart pipeline run')
  return data.data
}

export async function fetchPipelineLogs(runId: string): Promise<LogEntry[]> {
  const { data } = await client.get<APIResponse<LogEntry[]>>(`${BASE}/${runId}/logs`)
  return data.data ?? []
}

export async function fetchRunPatches(runId: string): Promise<PatchMeta[]> {
  const { data } = await client.get<APIResponse<PatchMeta[]>>(`${BASE}/${runId}/patches`)
  return data.data ?? []
}

export async function fetchPatchContent(runId: string, patchId: string): Promise<string> {
  const { data } = await client.get<string>(`${BASE}/${runId}/patches/${patchId}`, { responseType: 'text' })
  return typeof data === 'string' ? data : String(data ?? '')
}

export function patchDownloadUrl(runId: string, patchId: string): string {
  return `${BASE}/${runId}/patches/${patchId}`
}
