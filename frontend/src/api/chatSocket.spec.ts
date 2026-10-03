import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { applyTokens, clearSession } from './authSession'

const { ioMock, fakeSocket } = vi.hoisted(() => {
  const socket = {
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
    removeAllListeners: vi.fn(),
    connected: false,
    io: { on: vi.fn(), removeAllListeners: vi.fn() },
  }
  return { ioMock: vi.fn(() => socket), fakeSocket: socket }
})

vi.mock('socket.io-client', () => ({ io: ioMock }))

import { setApiMode } from './client'
import {
  connectChatSocket,
  disconnectChatSocket,
  emitChatEvent,
  useChatConnectionState,
} from './chatSocket'

function handlerFor(event: string): ((...args: unknown[]) => void) | undefined {
  const call = fakeSocket.on.mock.calls.find(c => c[0] === event)
  return call?.[1]
}

describe('chatSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fakeSocket.connected = false
    applyTokens({ access_token: 'header.payload.signature' })
    setApiMode('mock')
  })

  afterEach(() => {
    disconnectChatSocket()
    clearSession()
    setApiMode('mock')
  })

  it('never opens a socket while apiMode is mock', () => {
    connectChatSocket({ onNewMessage: vi.fn() })
    expect(ioMock).not.toHaveBeenCalled()
    expect(useChatConnectionState().value).toBe('disconnected')
  })

  it('connects once in real mode with the active JWT in auth', () => {
    setApiMode('real')
    connectChatSocket()
    expect(ioMock).toHaveBeenCalledTimes(1)
    const [url, options] = ioMock.mock.calls[0] as unknown as [
      string,
      { path: string; auth: { token: string } },
    ]
    expect(url).toBe(window.location.origin)
    expect(options.path).toBe('/socket.io/')
    expect(options.auth).toEqual({ token: 'header.payload.signature' })
    expect(useChatConnectionState().value).toBe('connecting')

    connectChatSocket()
    expect(ioMock).toHaveBeenCalledTimes(1)
  })

  it('does not connect in real mode without a token', () => {
    clearSession()
    setApiMode('real')
    connectChatSocket()
    expect(ioMock).not.toHaveBeenCalled()
    expect(useChatConnectionState().value).toBe('disconnected')
  })

  it('forwards server events to the registered handlers', () => {
    setApiMode('real')
    const onNewMessage = vi.fn()
    const onTypingStart = vi.fn()
    const onTypingStop = vi.fn()
    const onMessagesRead = vi.fn()
    const onConnect = vi.fn()
    const onReconnect = vi.fn()
    connectChatSocket({ onNewMessage, onTypingStart, onTypingStop, onMessagesRead, onConnect, onReconnect })

    const payload = { id: 'msg-1', conversationId: 'conv-1' }
    handlerFor('new_message')?.(payload)
    handlerFor('typing_start')?.({ conversationId: 'conv-1', userId: 'alice' })
    handlerFor('typing_stop')?.({ conversationId: 'conv-1', userId: 'alice' })
    handlerFor('messages_read')?.({ conversationId: 'conv-1', userId: 'alice' })

    expect(onNewMessage).toHaveBeenCalledWith(payload)
    expect(onTypingStart).toHaveBeenCalledWith({ conversationId: 'conv-1', userId: 'alice' })
    expect(onTypingStop).toHaveBeenCalledWith({ conversationId: 'conv-1', userId: 'alice' })
    expect(onMessagesRead).toHaveBeenCalledWith({ conversationId: 'conv-1', userId: 'alice' })

    fakeSocket.connected = true
    handlerFor('connect')?.()
    expect(useChatConnectionState().value).toBe('connected')
    expect(onConnect).toHaveBeenCalledTimes(1)

    const managerReconnect = fakeSocket.io.on.mock.calls.find(c => c[0] === 'reconnect')?.[1]
    managerReconnect?.()
    expect(onReconnect).toHaveBeenCalledTimes(1)
  })

  it('tracks disconnect and reconnect states', () => {
    setApiMode('real')
    connectChatSocket()
    handlerFor('disconnect')?.('transport close')
    expect(useChatConnectionState().value).toBe('reconnecting')
    handlerFor('connect_error')?.()
    expect(useChatConnectionState().value).toBe('reconnecting')
    handlerFor('disconnect')?.('io client disconnect')
    expect(useChatConnectionState().value).toBe('disconnected')
  })

  it('emits events only while the socket is connected', () => {
    expect(emitChatEvent('join_room', { conversation_id: 'conv-1' })).toBe(false)
    setApiMode('real')
    connectChatSocket()
    expect(emitChatEvent('join_room', { conversation_id: 'conv-1' })).toBe(false)
    fakeSocket.connected = true
    expect(emitChatEvent('join_room', { conversation_id: 'conv-1' })).toBe(true)
    expect(fakeSocket.emit).toHaveBeenCalledWith('join_room', { conversation_id: 'conv-1' })
  })

  it('tears down on disconnect and allows a fresh connect', () => {
    setApiMode('real')
    connectChatSocket()
    disconnectChatSocket()
    expect(fakeSocket.disconnect).toHaveBeenCalled()
    expect(useChatConnectionState().value).toBe('disconnected')
    connectChatSocket()
    expect(ioMock).toHaveBeenCalledTimes(2)
  })
})
