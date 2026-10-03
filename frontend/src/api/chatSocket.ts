import { io, type Socket } from 'socket.io-client'
import { computed, ref } from 'vue'
import { isMockMode } from './client'
import { getAccessToken } from './authSession'

export type ChatConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting'

const chatConnectionState = ref<ChatConnectionState>('disconnected')

export function useChatConnectionState() {
  return computed(() => chatConnectionState.value)
}

export interface ChatSocketHandlers {
  onConnect?: () => void
  onReconnect?: () => void
  onNewMessage?: (payload: unknown) => void
  onTypingStart?: (payload: unknown) => void
  onTypingStop?: (payload: unknown) => void
  onMessagesRead?: (payload: unknown) => void
}

let socket: Socket | null = null
let handlers: ChatSocketHandlers = {}

function resolveSocketUrl(): string {
  const apiUrl = (window as unknown as { __API_URL__?: string }).__API_URL__ || '/api/v1'
  try {
    return new URL(apiUrl, window.location.origin).origin
  } catch {
    return window.location.origin
  }
}

function setState(state: ChatConnectionState): void {
  chatConnectionState.value = state
}

export function connectChatSocket(next?: ChatSocketHandlers): void {
  if (next) {
    handlers = { ...handlers, ...next }
  }
  // Gate por apiMode: en modo mock el socket nunca se conecta (issue #540).
  if (isMockMode() || socket) return
  const token = getAccessToken()
  if (!token) return
  setState('connecting')
  socket = io(resolveSocketUrl(), {
    path: '/socket.io/',
    auth: { token },
  })

  socket.on('connect', () => {
    setState('connected')
    handlers.onConnect?.()
  })
  socket.on('disconnect', (reason: string) => {
    setState(reason === 'io client disconnect' ? 'disconnected' : 'reconnecting')
  })
  socket.on('connect_error', () => {
    if (chatConnectionState.value !== 'disconnected') setState('reconnecting')
  })
  socket.io.on('reconnect', () => {
    setState('connected')
    handlers.onReconnect?.()
  })
  socket.on('new_message', (payload: unknown) => handlers.onNewMessage?.(payload))
  socket.on('typing_start', (payload: unknown) => handlers.onTypingStart?.(payload))
  socket.on('typing_stop', (payload: unknown) => handlers.onTypingStop?.(payload))
  socket.on('messages_read', (payload: unknown) => handlers.onMessagesRead?.(payload))
}

export function disconnectChatSocket(): void {
  const current = socket
  socket = null
  if (current) {
    current.removeAllListeners()
    current.io.removeAllListeners()
    current.disconnect()
  }
  setState('disconnected')
}

export function emitChatEvent(event: string, payload: Record<string, unknown>): boolean {
  if (!socket || !socket.connected) return false
  socket.emit(event, payload)
  return true
}
