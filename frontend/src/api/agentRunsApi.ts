import client from './client'
import type { APIResponse } from '@/types'

/** Lifecycle status of a persistent run (issue #574). */
export type AgentRunStatus = 'running' | 'completed' | 'failed' | 'cancelled'

/** Log entry kinds persisted in `agent_run_logs` (issue #574). */
export type AgentRunLogType =
  | 'reasoning'
  | 'progress'
  | 'files'
  | 'debt'
  | 'tool_call'
  | 'error'
  | 'violation'

/** One row of `GET /agents/{id}/runs` (issue #574). */
export interface AgentRun {
  id: string
  agent_id: string
  issue_id?: string | null
  status: AgentRunStatus
  model?: string | null
  started_at?: string | null
  finished_at?: string | null
  total_tokens?: number | null
  total_tool_calls?: number | null
  duration_ms?: number | null
  summary?: string | null
}

/** One row of `GET /runs/{id}/logs` (issue #574). */
export interface AgentRunLog {
  run_id: string
  seq: number
  timestamp?: string | null
  type: AgentRunLogType
  content_markdown?: string | null
  metadata?: Record<string, unknown> | null
}

/** Body of `POST /agents/{id}/runs` (issue #574). */
export interface AgentRunCreatePayload {
  issue_id?: string | null
  model?: string | null
}

/** Body of `POST /runs/{id}/logs` (issue #574). */
export interface AgentRunLogCreatePayload {
  type: AgentRunLogType
  content_markdown?: string | null
  metadata?: Record<string, unknown> | null
}

export async function fetchAgentRuns(agentId: string, limit = 50): Promise<AgentRun[]> {
  const { data } = await client.get<APIResponse<AgentRun[]>>(`/agents/${encodeURIComponent(agentId)}/runs`, {
    params: { limit },
  })
  return data.data ?? []
}

export async function fetchRunLogs(runId: string): Promise<AgentRunLog[]> {
  const { data } = await client.get<APIResponse<AgentRunLog[]>>(`/runs/${encodeURIComponent(runId)}/logs`)
  return data.data ?? []
}

export async function createAgentRun(agentId: string, payload: AgentRunCreatePayload = {}): Promise<AgentRun> {
  const { data } = await client.post<APIResponse<AgentRun>>(`/agents/${encodeURIComponent(agentId)}/runs`, payload)
  return data.data as AgentRun
}

export async function appendRunLog(runId: string, payload: AgentRunLogCreatePayload): Promise<AgentRunLog> {
  const { data } = await client.post<APIResponse<AgentRunLog>>(`/runs/${encodeURIComponent(runId)}/logs`, payload)
  return data.data as AgentRunLog
}

export async function updateAgentRun(
  runId: string,
  payload: Partial<Pick<AgentRun, 'status' | 'finished_at' | 'total_tokens' | 'total_tool_calls' | 'duration_ms' | 'summary' | 'model'>>,
): Promise<AgentRun> {
  const { data } = await client.patch<APIResponse<AgentRun>>(`/runs/${encodeURIComponent(runId)}`, payload)
  return data.data as AgentRun
}

export async function deleteAgentRun(runId: string): Promise<void> {
  await client.delete(`/runs/${encodeURIComponent(runId)}`)
}
