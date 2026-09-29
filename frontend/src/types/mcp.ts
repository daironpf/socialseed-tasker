export type MCPSessionStatus = 'active' | 'paused' | 'revoked' | 'idle'

export type MCPClientType = 'cursor' | 'claude-desktop' | 'windsurf' | 'vscode' | 'custom'

export interface MCPSession {
  id: string
  clientName: string
  clientType: MCPClientType
  status: MCPSessionStatus
  connectedAt: string
  lastActivityAt: string
  uptime: number
  contextConsumed: number
  contextLimit: number
  cypherQueries: number
  cypherQueriesPerMin: number
  toolsUsed: string[]
  projectId: string
  userId: string
  server?: string | null
}

export interface MCPServer {
  id: string
  name: string
  transport: string
  url: string | null
  tools: string[]
  status: string
  lastSeen: string
}

export type MCPToolCallStatus = 'running' | 'success' | 'error'

export interface MCPToolCall {
  id: string
  sessionId: string | null
  server: string | null
  tool: string
  arguments: Record<string, unknown>
  status: MCPToolCallStatus
  startedAt: string
  durationMs: number | null
  resultSummary: string | null
  error: string | null
  rerunOf: string | null
}

export interface MCPToolMetric {
  tool: string
  calls: number
  successes: number
  errors: number
  avgMs: number
  maxMs: number
  slow: boolean
}

export interface MCPMetrics {
  totalSessions: number
  activeSessions: number
  totalContextConsumed: number
  totalCypherQueries: number
  avgQueriesPerMin: number
  avgContextPerSession: number
}

export interface MCPStreamEvent {
  type: 'session_update' | 'metrics_update' | 'session_revoked' | 'session_paused'
  sessionId: string
  data: Partial<MCPSession> | MCPMetrics
  timestamp: string
}
