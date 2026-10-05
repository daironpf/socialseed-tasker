import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia, type Pinia } from 'pinia'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { useAuthStore } from '@/stores/authStore'
import { setApiMode } from '@/api/client'
import { connectSSE, type SSEHandlers } from '@/api/realtime'
import * as notificationsApi from '@/api/notificationsApi'
import type { SessionUser } from '@/api/authSession'
import type { AppNotification } from '@/types/notifications'
import type { HITLRequest } from '@/types/hitl'

const STORAGE_KEY = 'socialseed-notifications'

const { playForCategoryMock } = vi.hoisted(() => ({ playForCategoryMock: vi.fn() }))

vi.mock('@/composables/useSoundEffects', () => ({
  useSoundEffects: () => ({ playForCategory: playForCategoryMock }),
}))

vi.mock('@/api/notificationsApi', async (importOriginal) => ({
  // normalizeNotification stays real (pure); only the HTTP calls are faked.
  ...(await importOriginal<typeof import('@/api/notificationsApi')>()),
  fetchNotifications: vi.fn(),
  markAsRead: vi.fn(),
  markAllAsRead: vi.fn(),
  deleteNotification: vi.fn(),
  clearAll: vi.fn(),
}))

vi.mock('@/api/realtime', () => ({
  connectSSE: vi.fn(() => ({ close: vi.fn() })),
}))

function makeNotification(
  overrides: Partial<Omit<AppNotification, 'id' | 'read' | 'createdAt'>> = {},
): Omit<AppNotification, 'id' | 'read' | 'createdAt'> {
  return {
    title: 'Test title',
    message: 'Test message',
    category: 'mention',
    requiresAction: false,
    ...overrides,
  }
}

function makeHitlRequest(status: HITLRequest['status'] = 'pending', id = 'hitl-1'): HITLRequest {
  return {
    id,
    title: 'Delete production table',
    description: '',
    type: 'delete_operation',
    severity: 'CRITICAL',
    status,
    agentId: 'agent-1',
    agentName: 'Backend Agent',
    agentAvatar: '🤖',
    issueId: 'ISS-42',
    issueTitle: 'Purge users',
    component: 'api',
    command: 'DELETE users',
    diffs: [],
    impact: {
      totalAffected: 3,
      directDeps: 1,
      transitiveDeps: 2,
      riskLevel: 'CRITICAL',
      affectedComponents: ['api'],
    },
    createdAt: '2026-09-26T10:00:00Z',
  }
}

function stored(): AppNotification[] {
  const raw = localStorage.getItem(STORAGE_KEY)
  return raw ? (JSON.parse(raw) as AppNotification[]) : []
}

const ALICE: SessionUser = { id: 'alice', username: 'alice', role: 'ADMIN', permissions: [] }

function serverNotif(overrides: Partial<AppNotification> & { id: string }): AppNotification {
  return {
    title: 'Server title',
    message: 'Server message',
    category: 'mention',
    read: false,
    requiresAction: false,
    createdAt: '2026-10-01T10:00:00Z',
    ...overrides,
  }
}

function sseHandlers(): SSEHandlers {
  return vi.mocked(connectSSE).mock.calls.at(-1)![1]
}

function lastClose(): ReturnType<typeof vi.fn> {
  return vi.mocked(connectSSE).mock.results.at(-1)!.value.close as ReturnType<typeof vi.fn>
}

// Every pinia used in this file is tracked so afterEach can null its auth
// user: stale stores would otherwise keep reacting to later apiMode flips.
const usedPinias: Pinia[] = []

function freshPinia(): Pinia {
  const p = createPinia()
  usedPinias.push(p)
  setActivePinia(p)
  return p
}

function createRealStore(user: SessionUser | null = ALICE): ReturnType<typeof useNotificationsStore> {
  setApiMode('real')
  const p = freshPinia()
  const auth = useAuthStore(p)
  if (user) auth.user = user
  return useNotificationsStore(p)
}

describe('notificationsStore', () => {
  let store: ReturnType<typeof useNotificationsStore>

  beforeEach(() => {
    vi.clearAllMocks()
    setApiMode('mock')
    vi.mocked(notificationsApi.fetchNotifications).mockResolvedValue([])
    vi.mocked(notificationsApi.markAsRead).mockResolvedValue(null)
    vi.mocked(notificationsApi.markAllAsRead).mockResolvedValue(0)
    vi.mocked(notificationsApi.deleteNotification).mockResolvedValue(undefined)
    freshPinia()
    store = useNotificationsStore()
  })

  afterEach(() => {
    for (const p of usedPinias) useAuthStore(p).user = null
    usedPinias.length = 0
    setApiMode('mock')
  })

  it('adds a notification at the top, persists it and counts it as unread', () => {
    store.addNotification(makeNotification({ title: 'First' }))
    store.addNotification(makeNotification({ title: 'Second' }))

    expect(store.notifications[0].title).toBe('Second')
    expect(store.notifications[0].read).toBe(false)
    expect(store.unreadCount).toBe(2)
    expect(stored()).toHaveLength(2)
    expect(store.notifications[0].id).toMatch(/^notif-/)
    expect(store.notifications[0].createdAt).toBeTruthy()
  })

  it('marks one, many or all notifications as read', () => {
    store.addNotification(makeNotification({ title: 'A' }))
    store.addNotification(makeNotification({ title: 'B' }))
    store.addNotification(makeNotification({ title: 'C' }))

    store.markAsRead(store.notifications[2].id)
    expect(store.unreadCount).toBe(2)

    store.markManyRead([store.notifications[0].id])
    expect(store.unreadCount).toBe(1)

    store.markAllAsRead()
    expect(store.unreadCount).toBe(0)
    expect(stored().every(n => n.read)).toBe(true)
  })

  it('dismisses single and multiple notifications with persistence', () => {
    store.addNotification(makeNotification({ title: 'A' }))
    store.addNotification(makeNotification({ title: 'B' }))
    store.addNotification(makeNotification({ title: 'C' }))
    const [a, b] = store.notifications

    store.dismiss(a.id)
    expect(store.notifications.map(n => n.title)).toEqual(['B', 'A'])
    expect(stored()).toHaveLength(2)

    store.dismissMany([b.id])
    expect(store.notifications.map(n => n.title)).toEqual(['A'])
    expect(stored()).toHaveLength(1)
  })

  it('filters by unread, action-required and category', () => {
    store.addNotification(makeNotification({ title: 'mention unread', category: 'mention', requiresAction: true }))
    store.addNotification(makeNotification({ title: 'hitl unread', category: 'hitl', requiresAction: true }))
    store.addNotification(makeNotification({ title: 'mention read', category: 'mention' }))
    store.markAsRead(store.notifications[2].id)

    expect(store.getFiltered('unread')).toHaveLength(2)
    expect(store.getFiltered('action')).toHaveLength(2)
    expect(store.getFiltered('all', 'mention')).toHaveLength(2)
    expect(store.getFiltered('unread', 'mention')).toHaveLength(1)
    expect(store.getFiltered('action', 'hitl')[0].title).toBe('hitl unread')
  })

  it('tracks unread counts per category', () => {
    store.addNotification(makeNotification({ category: 'hitl' }))
    store.addNotification(makeNotification({ category: 'hitl' }))
    store.addNotification(makeNotification({ category: 'sla' }))

    expect(store.unreadByCategory.hitl).toBe(2)
    expect(store.unreadByCategory.sla).toBe(1)
    expect(store.unreadByCategory.mention).toBe(0)
  })

  it('persists per-category sound preferences', () => {
    store.setChannelSound('mention', true)
    expect(store.preferences.channels.mention).toBe(true)

    const prefs = JSON.parse(localStorage.getItem('socialseed-alert-prefs')!)
    expect(prefs.channels.mention).toBe(true)
  })

  it('seeds mock notifications once', () => {
    store.seedMockNotifications()
    expect(store.notifications).toHaveLength(12)
    expect(localStorage.getItem(`${STORAGE_KEY}-version`)).toBe('3')

    store.addNotification(makeNotification({ title: 'extra' }))
    store.seedMockNotifications()
    expect(store.notifications).toHaveLength(13)
  })

  it('never seeds mock notifications in real mode', () => {
    setApiMode('real')
    store.seedMockNotifications()
    expect(store.notifications).toHaveLength(0)
  })

  it('ensures HITL notifications for pending requests without duplicating', () => {
    store.ensureHitlNotifications([makeHitlRequest('pending')])

    expect(store.notifications).toHaveLength(1)
    expect(store.notifications[0].hitlRequestId).toBe('hitl-1')
    expect(store.notifications[0].requiresAction).toBe(true)
    expect(store.notifications[0].category).toBe('hitl')

    store.ensureHitlNotifications([makeHitlRequest('pending')])
    expect(store.notifications).toHaveLength(1)

    store.ensureHitlNotifications([makeHitlRequest('pending', 'hitl-2'), makeHitlRequest('approved', 'hitl-3')])
    expect(store.notifications).toHaveLength(2)
  })

  it('ignores corrupted storage instead of throwing', () => {
    localStorage.setItem(STORAGE_KEY, '{not json')
    localStorage.setItem(`${STORAGE_KEY}-version`, '2')
    freshPinia()

    const fresh = useNotificationsStore()

    expect(fresh.notifications).toEqual([])
  })

  it('drops stale seed versions from storage', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([{ id: 'old' }]))
    localStorage.setItem(`${STORAGE_KEY}-version`, '1')
    freshPinia()

    const fresh = useNotificationsStore()

    expect(fresh.notifications).toEqual([])
    expect(localStorage.getItem(`${STORAGE_KEY}-version`)).toBe('3')
  })

  describe('real mode (#551)', () => {
    it('hydrates server notifications from the REST API without touching localStorage', async () => {
      vi.mocked(notificationsApi.fetchNotifications).mockResolvedValue([
        serverNotif({
          id: '64c100000000000000000001',
          title: 'Welcome',
          category: 'welcome',
          createdAt: '2026-10-02T10:00:00Z',
        }),
        serverNotif({ id: '64c100000000000000000002', title: 'Mention' }),
      ])

      const real = createRealStore()
      expect(notificationsApi.fetchNotifications).toHaveBeenCalledTimes(1)
      await flushPromises()

      expect(real.notifications.map(n => n.title)).toEqual(['Welcome', 'Mention'])
      expect(real.notifications[0].category).toBe('welcome')
      expect(real.notifications[0].linkTo).toBeUndefined()
      expect(stored()).toEqual([])
    })

    it('persists read state and deletions to the API for server ids only', async () => {
      const real = createRealStore()
      await flushPromises()
      const first = '64c1000000000000000000aa'
      const second = '64c1000000000000000000bb'
      real.notifications.push(serverNotif({ id: first }), serverNotif({ id: second }))

      real.markAsRead(first)
      expect(real.notifications.find(n => n.id === first)?.read).toBe(true)
      expect(notificationsApi.markAsRead).toHaveBeenCalledWith(first)
      expect(stored()).toEqual([])

      real.dismissMany([second, 'notif-local'])
      expect(notificationsApi.deleteNotification).toHaveBeenCalledTimes(1)
      expect(notificationsApi.deleteNotification).toHaveBeenCalledWith(second)
      expect(real.notifications.map(n => n.id)).toEqual([first])

      real.markAllAsRead()
      expect(notificationsApi.markAllAsRead).toHaveBeenCalledTimes(1)
      expect(stored()).toEqual([])
    })

    it('subscribes to the #550 stream with query-token auth', async () => {
      createRealStore()
      await flushPromises()

      expect(connectSSE).toHaveBeenCalledTimes(1)
      expect(connectSSE).toHaveBeenCalledWith(
        '/notifications/stream',
        expect.any(Object),
        expect.objectContaining({
          authenticate: true,
          events: expect.arrayContaining(['connected', 'notification_created']),
        }),
      )
    })

    it('hydrates from the connected snapshot keeping local HITL items', async () => {
      const real = createRealStore()
      await flushPromises()
      real.ensureHitlNotifications([makeHitlRequest()])

      sseHandlers().onEvent('connected', {
        userId: 'alice',
        snapshot: [
          {
            id: '64c10000000000000000000a',
            title: 'Newest',
            message: 'm',
            category: 'sla',
            read: false,
            requiresAction: false,
            createdAt: '2026-10-03T00:00:00Z',
          },
          {
            id: '64c10000000000000000000b',
            title: 'Older',
            message: 'm',
            category: 'mention',
            read: true,
            requiresAction: false,
            createdAt: '2026-10-01T00:00:00Z',
          },
        ],
      })

      expect(real.notifications.map(n => n.title)).toEqual(['Newest', 'Older', 'HITL Approval Required'])
      const local = real.notifications[2]
      expect(local.id).toMatch(/^notif-/)
      expect(local.hitlRequestId).toBe('hitl-1')
      // Snapshot never duplicates the local item on a second connected frame.
      sseHandlers().onEvent('connected', { userId: 'alice', snapshot: [] })
      expect(real.notifications).toHaveLength(1)
    })

    it('inserts notification_created events with dedupe and welcome sound', async () => {
      const real = createRealStore()
      await flushPromises()
      const wire = {
        id: '64c1000000000000000000c1',
        title: 'Bienvenido',
        message: 'instalado',
        category: 'welcome',
        read: false,
        requiresAction: true,
        linkTo: '/users',
        createdAt: '2026-10-04T00:00:00Z',
      }

      sseHandlers().onEvent('notification_created', wire)
      expect(real.notifications).toHaveLength(1)
      expect(real.notifications[0].category).toBe('welcome')
      expect(real.notifications[0].linkTo).toEqual({ path: '/users' })
      expect(real.unreadByCategory.welcome).toBe(1)
      expect(playForCategoryMock).toHaveBeenCalledWith('welcome')

      sseHandlers().onEvent('notification_created', wire)
      expect(real.notifications).toHaveLength(1)
    })

    it('tracks live connection state through onState', async () => {
      const real = createRealStore()
      await flushPromises()
      expect(real.streamConnected).toBe(false)

      sseHandlers().onState?.('live')
      expect(real.streamConnected).toBe(true)

      real.stopStream()
      expect(lastClose()).toHaveBeenCalledTimes(1)
      expect(real.streamConnected).toBe(false)
      expect(connectSSE).toHaveBeenCalledTimes(1)
    })

    it('counts and filters the welcome category like any other channel', async () => {
      vi.mocked(notificationsApi.fetchNotifications).mockResolvedValue([
        serverNotif({
          id: '64c1000000000000000000f1',
          title: 'Welcome',
          category: 'welcome',
          requiresAction: true,
        }),
      ])
      const real = createRealStore()
      await flushPromises()

      expect(real.unreadByCategory.welcome).toBe(1)
      expect(real.getFiltered('all', 'welcome')).toHaveLength(1)
      expect(real.getFiltered('action')).toHaveLength(1)
      expect(real.preferences.channels.welcome).toBe(true)
    })

    it('starts fetch and stream when a session appears', async () => {
      setApiMode('real')
      freshPinia()
      const auth = useAuthStore()
      const real = useNotificationsStore()
      expect(connectSSE).not.toHaveBeenCalled()
      expect(notificationsApi.fetchNotifications).not.toHaveBeenCalled()

      auth.user = ALICE
      await nextTick()

      expect(connectSSE).toHaveBeenCalledTimes(1)
      expect(notificationsApi.fetchNotifications).toHaveBeenCalledTimes(1)
      expect(real.notifications).toEqual([])
    })

    it('disconnects the stream and drops the previous user data on session loss', async () => {
      const real = createRealStore()
      await flushPromises()
      real.addNotification(makeNotification({ title: 'local leftover' }))
      expect(real.notifications).toHaveLength(1)

      useAuthStore().user = null
      await nextTick()

      expect(lastClose()).toHaveBeenCalledTimes(1)
      expect(real.streamConnected).toBe(false)
      expect(real.notifications).toEqual([])
      await nextTick()
      expect(connectSSE).toHaveBeenCalledTimes(1)
    })

    it('stops the stream and reseeds fixtures when switching back to mock', async () => {
      const real = createRealStore()
      await flushPromises()
      expect(real.notifications).toEqual([])

      setApiMode('mock')
      await nextTick()

      expect(lastClose()).toHaveBeenCalledTimes(1)
      expect(real.streamConnected).toBe(false)
      expect(real.notifications).toHaveLength(12)
      expect(localStorage.getItem(`${STORAGE_KEY}-version`)).toBe('3')
    })

    it('clears fixtures, fetches and connects when switching from mock to real', async () => {
      store.seedMockNotifications()
      expect(store.notifications).toHaveLength(12)
      useAuthStore().user = ALICE

      setApiMode('real')
      await nextTick()
      await flushPromises()

      expect(store.notifications).toEqual([])
      expect(notificationsApi.fetchNotifications).toHaveBeenCalledTimes(1)
      expect(connectSSE).toHaveBeenCalledTimes(1)
    })
  })
})
