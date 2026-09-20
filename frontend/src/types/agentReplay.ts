export type EventType = 'tool_call' | 'file_read' | 'file_edit' | 'cypher_query' | 'error' | 'violation' | 'decision' | 'thought'
export type EventSeverity = 'info' | 'warning' | 'error' | 'success'

export interface ReplayEvent {
  id: string
  timestamp: number
  type: EventType
  severity: EventSeverity
  title: string
  detail: string
  duration?: number
  metadata?: Record<string, string>
}

export interface AgentSession {
  id: string
  issueId: string
  issueTitle: string
  agent: string
  model: string
  startedAt: string
  totalDurationMs: number
  events: ReplayEvent[]
  status: 'completed' | 'failed' | 'interrupted'
  totalTokens: number
  totalToolCalls: number
}
