import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { applyTokens, clearSession } from '@/api/authSession'
import client, { setApiMode } from '@/api/client'

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

import { disconnectChatSocket } from '@/api/chatSocket'
import { useChatStore } from '@/stores/chatStore'

function handlerFor(event: string): ((...args: unknown[]) => void) | undefined {
  const call = fakeSocket.on.mock.calls.find(c => c[0] === event)
  return call?.[1]
}

function managerHandlerFor(event: string): ((...args: unknown[]) => void) | undefined {
  const call = fakeSocket.io.on.mock.calls.find(c => c[0] === event)
  return call?.[1]
}

function sessionToken(userId: string): string {
  const payload = btoa(JSON.stringify({ sub: userId }))
  return `header.${payload}.signature`
}

function envelope<T>(data: T) {
  return { data: { data, error: null } }
}

function convWire(id: string, type = 'direct') {
  return {
    id,
    title: null,
    type,
    participantIds: ['alice', 'bob'],
    pinnedBy: [],
    createdAt: '2026-10-01T00:00:00+00:00',
    updatedAt: '2026-10-01T00:00:00+00:00',
  }
}

function msgWire(id: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    conversationId: 'c1',
    senderId: 'bob',
    content: `contenido ${id}`,
    type: 'text',
    readBy: ['bob'],
    reactions: {},
    createdAt: '2026-10-01T00:01:00+00:00',
    ...overrides,
  }
}

function routeGet(url: string): Promise<unknown> {
  if (url === '/chat/conversations') {
    return Promise.resolve(envelope([convWire('c1'), convWire('c2', 'group')]))
  }
  if (url === '/chat/conversations/c1/messages') {
    return Promise.resolve(envelope({ messages: [msgWire('m1')] }))
  }
  if (url === '/chat/conversations/c2/messages') {
    return Promise.resolve(envelope({ messages: [] }))
  }
  return Promise.reject(new Error(`unexpected GET ${url}`))
}

function spyChatApi() {
  vi.spyOn(client, 'get').mockImplementation((url: string) => routeGet(url) as never)
  return vi.spyOn(client, 'post').mockResolvedValue(envelope(msgWire('m-post')) as never)
}

describe('chatStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fakeSocket.connected = false
    setActivePinia(createPinia())
    applyTokens({ access_token: sessionToken('alice') })
    setApiMode('mock')
  })

  afterEach(() => {
    disconnectChatSocket()
    vi.useRealTimers()
    clearSession()
    setApiMode('mock')
  })

  describe('mock mode', () => {
    it('loads fixtures without opening a socket', () => {
      const store = useChatStore()
      expect(ioMock).not.toHaveBeenCalled()
      expect(store.conversations).toHaveLength(7)
      expect(store.conversations.find(c => c.id === 'conv-1')?.unreadCount).toBe(2)
      expect(store.messages['conv-3']).toHaveLength(5)
      expect(store.isRealtimeApi).toBe(false)
      expect(store.currentUserId).toBe('alice')
    })

    it('selects conversations and sends messages locally without socket events', () => {
      const store = useChatStore()
      store.selectConversation('conv-6')
      expect(store.activeConversationId).toBe('conv-6')
      expect(store.activeMessages).toHaveLength(3)

      const before = store.messages['conv-6'].length
      store.sendMessage('conv-6', 'hola mock')
      expect(store.messages['conv-6']).toHaveLength(before + 1)
      const last = store.messages['conv-6'][store.messages['conv-6'].length - 1]
      expect(last.content).toBe('hola mock')
      expect(store.activeConversation?.lastMessage?.content).toBe('hola mock')
      expect(fakeSocket.emit).not.toHaveBeenCalled()
      expect(ioMock).not.toHaveBeenCalled()
    })

    it('ignores typing notifications while mocked', () => {
      const store = useChatStore()
      store.selectConversation('conv-6')
      store.notifyTyping()
      store.stopTyping()
      expect(fakeSocket.emit).not.toHaveBeenCalled()
      expect(store.typingUsers).toHaveLength(0)
    })

    it('switches to real mode connecting the socket and hydrating the API', async () => {
      spyChatApi()
      const store = useChatStore()
      expect(store.conversations).toHaveLength(7)

      setApiMode('real')
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))
      expect(ioMock).toHaveBeenCalledTimes(1)
      expect(store.isRealtimeApi).toBe(true)
    })
  })

  describe('real mode', () => {
    let postSpy: ReturnType<typeof spyChatApi>

    beforeEach(() => {
      setApiMode('real')
      postSpy = spyChatApi()
    })

    it('opens the socket and hydrates conversations from the API', async () => {
      const store = useChatStore()
      expect(ioMock).toHaveBeenCalledTimes(1)
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))
      expect(client.get).toHaveBeenCalledWith('/chat/conversations', { suppressErrorToast: true })
      expect(store.conversations[0].id).toBe('c1')
      expect(store.conversations[0].name).toBe('bob')
      expect(store.conversations[0].unreadCount).toBe(0)
      expect(store.isRealtimeApi).toBe(true)
    })

    it('selects a conversation joining the room, marking read and loading history', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))
      fakeSocket.connected = true

      store.selectConversation('c1')
      expect(store.activeConversationId).toBe('c1')
      expect(store.activeConversation?.unreadCount).toBe(0)
      expect(fakeSocket.emit).toHaveBeenCalledWith('join_room', { conversation_id: 'c1' })
      expect(fakeSocket.emit).toHaveBeenCalledWith('mark_as_read', { conversation_id: 'c1' })
      await vi.waitFor(() =>
        expect(client.get).toHaveBeenCalledWith('/chat/conversations/c1/messages', {
          params: { limit: 50 },
          suppressErrorToast: false,
        }),
      )
      expect(store.messages['c1']).toHaveLength(1)

      fakeSocket.emit.mockClear()
      handlerFor('connect')?.()
      expect(fakeSocket.emit).toHaveBeenCalledWith('join_room', { conversation_id: 'c1' })
      expect(fakeSocket.emit).toHaveBeenCalledWith('mark_as_read', { conversation_id: 'c1' })
    })

    it('leaves the previous room when switching conversations', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))
      fakeSocket.connected = true

      store.selectConversation('c1')
      store.selectConversation('c2')
      expect(fakeSocket.emit).toHaveBeenCalledWith('leave_room', { conversation_id: 'c1' })
      expect(fakeSocket.emit).toHaveBeenCalledWith('join_room', { conversation_id: 'c2' })
      expect(store.activeConversationId).toBe('c2')
    })

    it('applies incoming new_message, updates the preview, unread and dedupes echoes', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))

      const wire = msgWire('m42', { content: 'mensaje entrante' })
      handlerFor('new_message')?.(wire)
      expect(store.messages['c1']).toHaveLength(1)
      expect(store.messages['c1'][0].senderName).toBe('bob')
      expect(store.conversations[0].lastMessage?.content).toBe('mensaje entrante')
      expect(store.conversations[0].unreadCount).toBe(1)
      expect(fakeSocket.emit).not.toHaveBeenCalled()

      handlerFor('new_message')?.(wire)
      expect(store.messages['c1']).toHaveLength(1)
      expect(store.conversations[0].unreadCount).toBe(1)
    })

    it('marks the active conversation read without raising the unread badge', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))
      fakeSocket.connected = true
      store.selectConversation('c1')
      await vi.waitFor(() => expect(store.messages['c1']).toHaveLength(1))
      fakeSocket.emit.mockClear()

      handlerFor('new_message')?.(msgWire('m43', { content: 'en la sala activa' }))
      expect(store.conversations[0].unreadCount).toBe(0)
      expect(fakeSocket.emit).toHaveBeenCalledWith('mark_as_read', { conversation_id: 'c1' })
    })

    it('tracks typing users from the room events', async () => {
      const store = useChatStore()
      handlerFor('typing_start')?.({ conversationId: 'c1', userId: 'bob' })
      expect(store.typingUsers.map(t => t.userId)).toEqual(['bob'])

      handlerFor('typing_start')?.({ conversationId: 'c1', userId: 'bob' })
      expect(store.typingUsers).toHaveLength(1)

      handlerFor('typing_stop')?.({ conversationId: 'c1', userId: 'bob' })
      expect(store.typingUsers).toHaveLength(0)

      handlerFor('typing_start')?.({})
      handlerFor('typing_stop')?.({})
      expect(store.typingUsers).toHaveLength(0)
    })

    it('clears stale typing indicators after the timeout', async () => {
      const store = useChatStore()
      vi.useFakeTimers()
      handlerFor('typing_start')?.({ conversationId: 'c1', userId: 'bob' })
      expect(store.typingUsers).toHaveLength(1)
      vi.advanceTimersByTime(7000)
      expect(store.typingUsers).toHaveLength(0)
    })

    it('applies messages_read to the conversation history', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))

      handlerFor('new_message')?.(msgWire('m44', { readBy: [] }))
      expect(store.messages['c1'][0].readBy).toEqual([])

      handlerFor('messages_read')?.({ conversationId: 'c1', userId: 'bob' })
      expect(store.messages['c1'][0].readBy).toEqual(['bob'])
    })

    it('reconnects to the room and resyncs history after a transport drop', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))
      fakeSocket.connected = true
      store.selectConversation('c1')
      await vi.waitFor(() => expect(store.messages['c1']).toHaveLength(1))

      handlerFor('disconnect')?.('transport close')
      expect(store.connectionState).toBe('reconnecting')

      managerHandlerFor('reconnect')?.()
      await vi.waitFor(() =>
        expect(client.get).toHaveBeenCalledWith('/chat/conversations/c1/messages', {
          params: { limit: 100 },
          suppressErrorToast: true,
        }),
      )
    })

    it('sends through the API and deduplicates the socket echo', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))
      fakeSocket.connected = true
      store.selectConversation('c1')
      await vi.waitFor(() => expect(store.messages['c1']).toHaveLength(1))

      const wire = msgWire('m50', { senderId: 'alice', content: 'por REST', readBy: ['alice'] })
      postSpy.mockResolvedValue(envelope(wire) as never)
      store.sendMessage('c1', 'por REST')
      await vi.waitFor(() =>
        expect(client.post).toHaveBeenCalledWith('/chat/conversations/c1/messages', {
          text: 'por REST',
          type: 'text',
        }),
      )
      await vi.waitFor(() => expect(store.messages['c1']).toHaveLength(2))

      handlerFor('new_message')?.(wire)
      expect(store.messages['c1'].filter(m => m.id === 'm50')).toHaveLength(1)
    })

    it('keeps the message locally when the API is unreachable', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))
      postSpy.mockRejectedValue(new Error('offline'))

      store.sendMessage('c1', 'sin red')
      await vi.waitFor(() =>
        expect(store.messages['c1'].some(m => m.content === 'sin red')).toBe(true),
      )
      const local = store.messages['c1'].find(m => m.content === 'sin red')
      expect(local?.senderId).toBe('alice')
      expect(local?.readBy).toEqual(['alice'])
    })

    it('emits typing_start once and typing_stop after the idle window', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))
      fakeSocket.connected = true
      store.selectConversation('c1')
      await vi.waitFor(() => expect(store.messages['c1']).toHaveLength(1))

      vi.useFakeTimers()
      store.notifyTyping()
      store.notifyTyping()
      const starts = fakeSocket.emit.mock.calls.filter(c => c[0] === 'typing_start')
      expect(starts).toHaveLength(1)
      expect(starts[0][1]).toEqual({ conversation_id: 'c1' })

      vi.advanceTimersByTime(2000)
      expect(fakeSocket.emit).toHaveBeenCalledWith('typing_stop', { conversation_id: 'c1' })
    })

    it('disconnects and restores the mock fixtures when apiMode switches back', async () => {
      const store = useChatStore()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(2))

      setApiMode('mock')
      await nextTick()
      await vi.waitFor(() => expect(store.conversations).toHaveLength(7))
      expect(fakeSocket.disconnect).toHaveBeenCalled()
      expect(store.conversations.some(c => c.id === 'c1')).toBe(false)
      expect(store.isRealtimeApi).toBe(false)
    })
  })
})
