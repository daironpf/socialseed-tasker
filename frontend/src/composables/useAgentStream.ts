import { ref, watch, onUnmounted } from 'vue'
import type { AgentLog } from '@/types'
import { connectSSE, type SSEHandle } from '@/api/realtime'
import { isMockMode, apiMode } from '@/api/client'

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting'

export interface StreamEvent {
  type: 'reasoning' | 'progress' | 'files' | 'debt' | 'error' | 'connected' | 'done'
  data?: AgentLog
  message?: string
}

export function useAgentStream() {
  const logs = ref<AgentLog[]>([])
  const status = ref<ConnectionStatus>('disconnected')
  const error = ref<string | null>(null)

  let handle: SSEHandle | null = null
  let currentIssueId: string | null = null

  function connect(issueId: string) {
    disconnect()
    currentIssueId = issueId

    // Mock mode: the view drives logs with useMockStream, no network stream.
    if (isMockMode()) {
      status.value = 'disconnected'
      return
    }

    error.value = null
    handle = connectSSE(
      `/issues/${issueId}/agent-logs/stream`,
      {
        onEvent: (type, data) => {
          if (type === 'log') {
            logs.value.push(data as AgentLog)
          } else if (type === 'error') {
            error.value = typeof data === 'string' ? data : 'Stream error'
          }
        },
        onState: (state) => {
          switch (state) {
            case 'connecting':
              status.value = 'connecting'
              break
            case 'live':
              status.value = 'connected'
              break
            case 'reconnecting':
              status.value = 'reconnecting'
              break
            case 'offline':
              status.value = 'disconnected'
              error.value = error.value || 'Max reconnection attempts reached'
              break
            default:
              status.value = 'disconnected'
          }
        },
      },
      { events: ['connected', 'log', 'done', 'ping', 'error'] },
    )
  }

  function disconnect() {
    handle?.close()
    handle = null
    currentIssueId = null
    status.value = 'disconnected'
  }

  // Runtime data-source switch (mock <-> real), issue #517
  watch(apiMode, () => {
    if (isMockMode()) {
      handle?.close()
      handle = null
      status.value = 'disconnected'
    } else if (currentIssueId) {
      connect(currentIssueId)
    }
  })

  function clearLogs() {
    logs.value = []
  }

  function addLog(log: AgentLog) {
    logs.value.push(log)
  }

  onUnmounted(() => {
    handle?.close()
    handle = null
    status.value = 'disconnected'
  })

  return {
    logs,
    status,
    error,
    connect,
    disconnect,
    clearLogs,
    addLog,
  }
}
