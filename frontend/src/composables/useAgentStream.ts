import { ref, onUnmounted } from 'vue'
import type { AgentLog } from '@/types'

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

  let eventSource: EventSource | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0
  const MAX_RECONNECT_ATTEMPTS = 5
  const BASE_DELAY = 1000

  function connect(issueId: string) {
    if (eventSource) {
      disconnect()
    }

    status.value = 'connecting'
    error.value = null
    reconnectAttempts = 0

    try {
      const apiUrl = (window as any).__API_URL__ || '/api/v1'
      const url = `${apiUrl}/issues/${issueId}/agent-logs/stream`

      eventSource = new EventSource(url)

      eventSource.onopen = () => {
        status.value = 'connected'
        reconnectAttempts = 0
      }

      eventSource.addEventListener('log', (event) => {
        try {
          const data = JSON.parse(event.data) as AgentLog
          logs.value.push(data)
        } catch {
          // ignore parse errors
        }
      })

      eventSource.addEventListener('done', () => {
        status.value = 'disconnected'
        eventSource?.close()
        eventSource = null
      })

      eventSource.onerror = () => {
        status.value = 'disconnected'
        eventSource?.close()
        eventSource = null
        attemptReconnect(issueId)
      }
    } catch {
      status.value = 'disconnected'
      attemptReconnect(issueId)
    }
  }

  function attemptReconnect(issueId: string) {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      error.value = 'Max reconnection attempts reached'
      return
    }

    status.value = 'reconnecting'
    const delay = BASE_DELAY * Math.pow(2, reconnectAttempts)
    reconnectAttempts++

    reconnectTimer = setTimeout(() => {
      connect(issueId)
    }, delay)
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    status.value = 'disconnected'
  }

  function clearLogs() {
    logs.value = []
  }

  function addLog(log: AgentLog) {
    logs.value.push(log)
  }

  onUnmounted(() => {
    disconnect()
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
