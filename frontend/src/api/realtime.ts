import { ref, computed } from 'vue'
import { getAccessToken } from './authSession'

export type RealtimeState = 'idle' | 'connecting' | 'live' | 'reconnecting' | 'offline'

interface Conn {
  state: RealtimeState
}

const connections: Conn[] = []
const realtimeState = ref<RealtimeState>('idle')
const realtimeLastEvent = ref<number>(0)

function recompute() {
  if (connections.length === 0) {
    realtimeState.value = 'idle'
    return
  }
  const states = connections.map((c) => c.state)
  realtimeState.value = states.includes('live')
    ? 'live'
    : states.includes('connecting')
      ? 'connecting'
      : states.includes('reconnecting')
        ? 'reconnecting'
        : 'offline'
}

export function useRealtimeStatus() {
  return {
    realtimeState: computed(() => realtimeState.value),
    realtimeLastEvent: computed(() => realtimeLastEvent.value),
  }
}

export interface SSEHandlers {
  onEvent: (type: string, data: unknown) => void
  onState?: (state: RealtimeState) => void
}

export interface SSEHandle {
  close: () => void
}

export interface SSEOptions {
  /** Watchdog timeout: force reconnect if no event arrives within this window. */
  heartbeatTimeoutMs?: number
  /** Max consecutive failed attempts before giving up (`offline`). */
  maxAttempts?: number
  /** Named SSE events to subscribe to (plus `message`). */
  events?: string[]
  /**
   * Append the in-memory JWT as `?access_token=` on every (re)connect.
   * `EventSource` cannot send the Authorization header; the backend accepts
   * the query token on endpoints documented for it (issue #551).
   */
  authenticate?: boolean
}

const DEFAULT_EVENTS = ['message', 'connected', 'log', 'done', 'ping', 'viewers']

function parseData(raw: string): unknown {
  try {
    return JSON.parse(raw)
  } catch {
    return raw
  }
}

/**
 * SSE client with exponential backoff + jitter, heartbeat watchdog and
 * aggregated connection state (issue #517).
 */
export function connectSSE(path: string, handlers: SSEHandlers, options: SSEOptions = {}): SSEHandle {
  const heartbeatTimeoutMs = options.heartbeatTimeoutMs ?? 45000
  const maxAttempts = options.maxAttempts ?? 8
  const eventNames = options.events ?? DEFAULT_EVENTS

  const apiUrl = (window as unknown as { __API_URL__?: string }).__API_URL__ || '/api/v1'
  const baseUrl = `${apiUrl}${path.startsWith('/') ? path : `/${path}`}`

  const conn: Conn = { state: 'connecting' }
  connections.push(conn)
  recompute()

  let eventSource: EventSource | null = null
  let attempt = 0
  let closed = false
  let watchdog: ReturnType<typeof setTimeout> | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function setState(state: RealtimeState) {
    conn.state = state
    recompute()
    handlers.onState?.(state)
  }

  function clearTimers() {
    if (watchdog) {
      clearTimeout(watchdog)
      watchdog = null
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function armWatchdog() {
    if (watchdog) clearTimeout(watchdog)
    watchdog = setTimeout(() => {
      // No heartbeat within the window: force a reconnect cycle.
      eventSource?.close()
      eventSource = null
      scheduleReconnect()
    }, heartbeatTimeoutMs)
  }

  function scheduleReconnect() {
    if (closed) return
    clearTimers()
    if (attempt >= maxAttempts) {
      setState('offline')
      return
    }
    setState('reconnecting')
    const base = Math.min(1000 * Math.pow(2, attempt), 30000)
    const delay = Math.round(base * (0.5 + Math.random()))
    attempt++
    reconnectTimer = setTimeout(open, delay)
  }

  function open() {
    if (closed) return
    clearTimers()
    setState(attempt === 0 ? 'connecting' : 'reconnecting')
    // Token is read on every attempt so reconnects never reuse an expired JWT.
    const token = options.authenticate ? getAccessToken() : null
    const url = token
      ? `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}access_token=${encodeURIComponent(token)}`
      : baseUrl
    try {
      eventSource = new EventSource(url)
    } catch {
      scheduleReconnect()
      return
    }
    const es = eventSource

    es.onopen = () => {
      attempt = 0
      realtimeLastEvent.value = Date.now()
      setState('live')
      armWatchdog()
    }

    es.onerror = () => {
      es.close()
      if (eventSource === es) eventSource = null
      scheduleReconnect()
    }

    const handle = (name: string) => (ev: Event) => {
      realtimeLastEvent.value = Date.now()
      armWatchdog()
      handlers.onEvent(name, parseData((ev as MessageEvent).data))
    }

    es.onmessage = handle('message')
    for (const name of eventNames) {
      if (name === 'message') continue
      es.addEventListener(name, handle(name))
    }

    es.addEventListener('done', () => {
      // Stream finished server-side: close without retrying.
      closed = true
      clearTimers()
      es.close()
      if (eventSource === es) eventSource = null
      const idx = connections.indexOf(conn)
      if (idx >= 0) connections.splice(idx, 1)
      setState('idle')
      recompute()
    })
  }

  open()

  return {
    close: () => {
      closed = true
      clearTimers()
      eventSource?.close()
      eventSource = null
      const idx = connections.indexOf(conn)
      if (idx >= 0) connections.splice(idx, 1)
      recompute()
    },
  }
}
