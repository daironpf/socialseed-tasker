import client from './client'
import type { APIResponse } from '@/types'
import type {
  MCPServer,
  MCPSession,
  MCPSessionStatus,
  MCPClientType,
  MCPToolCall,
  MCPToolCallStatus,
} from '@/types/mcp'

const CLIENT_TYPES: MCPClientType[] = ['cursor', 'claude-desktop', 'windsurf', 'vscode', 'custom']
const SESSION_STATUSES: MCPSessionStatus[] = ['active', 'paused', 'revoked', 'idle']
const CALL_STATUSES: MCPToolCallStatus[] = ['running', 'success', 'error']

export interface MCPSessionInput {
  id?: string
  clientName: string
  clientType?: string
  status?: string
  contextConsumed?: number
  cypherQueries?: number
  cypherQueriesPerMin?: number
  toolsUsed?: string[]
  projectId?: string | null
  userId?: string | null
  server?: string | null
}

export interface MCPServerInput {
  id?: string
  name: string
  transport?: string
  url?: string | null
  tools?: string[]
  status?: string
}

export interface MCPToolCallInput {
  id?: string
  sessionId?: string | null
  server?: string | null
  tool: string
  arguments?: Record<string, unknown>
  status?: string
  durationMs?: number | null
  resultSummary?: string | null
  error?: string | null
  rerunOf?: string | null
}

type Wire = Record<string, unknown>

export function normalizeSession(raw: Wire): MCPSession {
  const clientType = String(raw.clientType ?? 'custom')
  const status = String(raw.status ?? 'active')
  return {
    id: String(raw.id ?? ''),
    clientName: String(raw.clientName ?? raw.id ?? ''),
    clientType: (CLIENT_TYPES.includes(clientType as MCPClientType)
      ? clientType
      : 'custom') as MCPClientType,
    status: (SESSION_STATUSES.includes(status as MCPSessionStatus)
      ? status
      : 'active') as MCPSessionStatus,
    connectedAt: String(raw.connectedAt ?? ''),
    lastActivityAt: String(raw.lastActivityAt ?? ''),
    uptime: Number(raw.uptime ?? 0),
    contextConsumed: Number(raw.contextConsumed ?? 0),
    contextLimit: Number(raw.contextLimit ?? 524288),
    cypherQueries: Number(raw.cypherQueries ?? 0),
    cypherQueriesPerMin: Number(raw.cypherQueriesPerMin ?? 0),
    toolsUsed: Array.isArray(raw.toolsUsed) ? (raw.toolsUsed as string[]) : [],
    projectId: String(raw.projectId ?? ''),
    userId: String(raw.userId ?? ''),
    server: (raw.server as string | null) ?? null,
  }
}

export function normalizeServer(raw: Wire): MCPServer {
  return {
    id: String(raw.id ?? ''),
    name: String(raw.name ?? raw.id ?? ''),
    transport: String(raw.transport ?? 'http'),
    url: (raw.url as string | null) ?? null,
    tools: Array.isArray(raw.tools) ? (raw.tools as string[]) : [],
    status: String(raw.status ?? 'online'),
    lastSeen: String(raw.lastSeen ?? ''),
  }
}

export function normalizeToolCall(raw: Wire): MCPToolCall {
  const status = String(raw.status ?? 'running')
  return {
    id: String(raw.id ?? ''),
    sessionId: (raw.sessionId as string | null) ?? null,
    server: (raw.server as string | null) ?? null,
    tool: String(raw.tool ?? ''),
    arguments: (raw.arguments as Record<string, unknown> | null) ?? {},
    status: (CALL_STATUSES.includes(status as MCPToolCallStatus)
      ? status
      : 'running') as MCPToolCallStatus,
    startedAt: String(raw.startedAt ?? ''),
    durationMs: raw.durationMs === null || raw.durationMs === undefined ? null : Number(raw.durationMs),
    resultSummary: (raw.resultSummary as string | null) ?? null,
    error: (raw.error as string | null) ?? null,
    rerunOf: (raw.rerunOf as string | null) ?? null,
  }
}

// --------------------------------------------------------------- servers

export async function fetchServers(): Promise<MCPServer[]> {
  const { data } = await client.get<APIResponse<Wire[]>>('/mcp/servers')
  return (data.data ?? []).map(normalizeServer)
}

export async function registerServer(input: MCPServerInput): Promise<MCPServer> {
  const { data } = await client.post<APIResponse<Wire>>('/mcp/servers', input)
  if (!data.data) throw new Error('Server registration failed')
  return normalizeServer(data.data)
}

// ------------------------------------------------------------- sessions

export async function fetchSessions(): Promise<MCPSession[]> {
  const { data } = await client.get<APIResponse<Wire[]>>('/mcp/sessions')
  return (data.data ?? []).map(normalizeSession)
}

export async function saveSession(input: MCPSessionInput): Promise<MCPSession> {
  const { data } = await client.post<APIResponse<Wire>>('/mcp/sessions', input)
  if (!data.data) throw new Error('Session update failed')
  return normalizeSession(data.data)
}

export async function removeSession(sessionId: string): Promise<void> {
  await client.delete(`/mcp/sessions/${sessionId}`)
}

// ----------------------------------------------------------- tool calls

export async function fetchToolCalls(limit = 50): Promise<MCPToolCall[]> {
  const { data } = await client.get<APIResponse<Wire[]>>('/mcp/tool-calls', {
    params: { limit },
  })
  return (data.data ?? []).map(normalizeToolCall)
}

export async function recordToolCall(input: MCPToolCallInput): Promise<MCPToolCall> {
  const { data } = await client.post<APIResponse<Wire>>('/mcp/tool-calls', input)
  if (!data.data) throw new Error('Tool call record failed')
  return normalizeToolCall(data.data)
}

export async function rerunToolCall(callId: string): Promise<MCPToolCall> {
  const { data } = await client.post<APIResponse<Wire>>(`/mcp/tool-calls/${callId}/rerun`)
  if (!data.data) throw new Error('Tool call re-run failed')
  return normalizeToolCall(data.data)
}
