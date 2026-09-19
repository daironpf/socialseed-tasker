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
