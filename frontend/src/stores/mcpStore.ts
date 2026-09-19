import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { MCPSession, MCPSessionStatus, MCPMetrics } from '@/types/mcp'

const MOCK_SESSIONS: MCPSession[] = [
  {
    id: 'mcp-sess-001',
    clientName: 'Cursor IDE',
    clientType: 'cursor',
    status: 'active',
    connectedAt: new Date(Date.now() - 3600000 * 2).toISOString(),
    lastActivityAt: new Date(Date.now() - 30000).toISOString(),
    uptime: 7200,
    contextConsumed: 145600,
    contextLimit: 524288,
    cypherQueries: 847,
    cypherQueriesPerMin: 12.4,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher', 'impact_analysis'],
    projectId: 'proj-001',
    userId: 'user-alice',
  },
  {
    id: 'mcp-sess-002',
    clientName: 'Claude Desktop',
    clientType: 'claude-desktop',
    status: 'active',
    connectedAt: new Date(Date.now() - 3600000 * 5).toISOString(),
    lastActivityAt: new Date(Date.now() - 120000).toISOString(),
    uptime: 18000,
    contextConsumed: 312400,
    contextLimit: 524288,
    cypherQueries: 2341,
    cypherQueriesPerMin: 8.7,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher', 'create_issue', 'update_issue'],
    projectId: 'proj-001',
    userId: 'user-bob',
  },
  {
    id: 'mcp-sess-003',
    clientName: 'Windsurf',
    clientType: 'windsurf',
    status: 'paused',
    connectedAt: new Date(Date.now() - 3600000 * 1).toISOString(),
    lastActivityAt: new Date(Date.now() - 600000).toISOString(),
    uptime: 3600,
    contextConsumed: 67200,
    contextLimit: 524288,
    cypherQueries: 234,
    cypherQueriesPerMin: 0,
    toolsUsed: ['read_file', 'search_graph'],
    projectId: 'proj-002',
    userId: 'user-alice',
  },
  {
    id: 'mcp-sess-004',
    clientName: 'VS Code Extension',
    clientType: 'vscode',
    status: 'active',
    connectedAt: new Date(Date.now() - 3600000 * 0.5).toISOString(),
    lastActivityAt: new Date(Date.now() - 10000).toISOString(),
    uptime: 1800,
    contextConsumed: 23400,
    contextLimit: 524288,
    cypherQueries: 89,
    cypherQueriesPerMin: 15.2,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher'],
    projectId: 'proj-001',
    userId: 'user-carol',
  },
  {
    id: 'mcp-sess-005',
    clientName: 'Custom Agent',
    clientType: 'custom',
    status: 'idle',
    connectedAt: new Date(Date.now() - 3600000 * 8).toISOString(),
    lastActivityAt: new Date(Date.now() - 3600000).toISOString(),
    uptime: 28800,
    contextConsumed: 498000,
    contextLimit: 524288,
    cypherQueries: 5672,
    cypherQueriesPerMin: 0.1,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher', 'create_issue', 'update_issue', 'impact_analysis'],
    projectId: 'proj-003',
    userId: 'user-dave',
  },
  {
    id: 'mcp-sess-006',
    clientName: 'Cursor IDE',
    clientType: 'cursor',
    status: 'revoked',
    connectedAt: new Date(Date.now() - 3600000 * 12).toISOString(),
    lastActivityAt: new Date(Date.now() - 3600000 * 3).toISOString(),
    uptime: 32400,
    contextConsumed: 512000,
    contextLimit: 524288,
    cypherQueries: 8934,
    cypherQueriesPerMin: 0,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher', 'create_issue'],
    projectId: 'proj-002',
    userId: 'user-eve',
  },
]

export const useMcpStore = defineStore('mcp', () => {
  const sessions = ref<MCPSession[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const streamConnected = ref(false)

  const activeSessions = computed(() => sessions.value.filter(s => s.status === 'active'))
  const pausedSessions = computed(() => sessions.value.filter(s => s.status === 'paused'))
  const revokedSessions = computed(() => sessions.value.filter(s => s.status === 'revoked'))
  const idleSessions = computed(() => sessions.value.filter(s => s.status === 'idle'))

  const metrics = computed<MCPMetrics>(() => {
    const all = sessions.value
    const active = activeSessions.value
    return {
      totalSessions: all.length,
      activeSessions: active.length,
      totalContextConsumed: all.reduce((sum, s) => sum + s.contextConsumed, 0),
      totalCypherQueries: all.reduce((sum, s) => sum + s.cypherQueries, 0),
      avgQueriesPerMin: active.length > 0
        ? active.reduce((sum, s) => sum + s.cypherQueriesPerMin, 0) / active.length
        : 0,
      avgContextPerSession: all.length > 0
        ? all.reduce((sum, s) => sum + s.contextConsumed, 0) / all.length
        : 0,
    }
  })

  async function fetchSessions() {
    loading.value = true
    error.value = null
    try {
      await new Promise(resolve => setTimeout(resolve, 300))
      sessions.value = [...MOCK_SESSIONS]
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function revokeSession(id: string): Promise<boolean> {
    const session = sessions.value.find(s => s.id === id)
    if (!session) return false
    session.status = 'revoked'
    session.lastActivityAt = new Date().toISOString()
    return true
  }

  async function pauseSession(id: string): Promise<boolean> {
    const session = sessions.value.find(s => s.id === id)
    if (!session || session.status !== 'active') return false
    session.status = 'paused'
    session.lastActivityAt = new Date().toISOString()
    session.cypherQueriesPerMin = 0
    return true
  }

  async function resumeSession(id: string): Promise<boolean> {
    const session = sessions.value.find(s => s.id === id)
    if (!session || session.status !== 'paused') return false
    session.status = 'active'
    session.lastActivityAt = new Date().toISOString()
    session.cypherQueriesPerMin = Math.random() * 15 + 1
    return true
  }

  function startStream() {
    streamConnected.value = true
    const interval = setInterval(() => {
      if (!streamConnected.value) {
        clearInterval(interval)
        return
      }
      sessions.value.forEach(session => {
        if (session.status === 'active') {
          session.cypherQueries += Math.floor(Math.random() * 3)
          session.cypherQueriesPerMin = Math.round((Math.random() * 15 + 1) * 10) / 10
          session.contextConsumed = Math.min(
            session.contextLimit,
            session.contextConsumed + Math.floor(Math.random() * 2048)
          )
          session.lastActivityAt = new Date().toISOString()
          session.uptime += 5
        }
      })
    }, 5000)
  }

  function stopStream() {
    streamConnected.value = false
  }

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1048576).toFixed(2)} MB`
  }

  function formatUptime(seconds: number): string {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    if (hrs > 0) return `${hrs}h ${mins}m`
    return `${mins}m`
  }

  function getClientIcon(type: string): string {
    const icons: Record<string, string> = {
      cursor: '⚡',
      'claude-desktop': '🤖',
      windsurf: '🏄',
      vscode: '💻',
      custom: '🔧',
    }
    return icons[type] || '🔌'
  }

  function getStatusColor(status: MCPSessionStatus): string {
    const colors: Record<MCPSessionStatus, string> = {
      active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      paused: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      revoked: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      idle: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    }
    return colors[status]
  }

  return {
    sessions,
    loading,
    error,
    streamConnected,
    activeSessions,
    pausedSessions,
    revokedSessions,
    idleSessions,
    metrics,
    fetchSessions,
    revokeSession,
    pauseSession,
    resumeSession,
    startStream,
    stopStream,
    formatBytes,
    formatUptime,
    getClientIcon,
    getStatusColor,
  }
})
