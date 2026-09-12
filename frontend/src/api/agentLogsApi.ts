import client from './client'
import type { APIResponse, AgentLogsBundle } from '@/types'

export async function fetchAgentLogs(issueId: string): Promise<AgentLogsBundle> {
  const { data } = await client.get<APIResponse<AgentLogsBundle>>(`/issues/${issueId}/agent-logs`)
  return data.data || { issue_id: issueId, logs: [] }
}
