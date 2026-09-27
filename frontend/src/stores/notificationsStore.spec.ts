import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia, type Pinia } from 'pinia'
import { useNotificationsStore } from '@/stores/notificationsStore'
import type { AppNotification } from '@/types/notifications'
import type { HITLRequest } from '@/types/hitl'

const STORAGE_KEY = 'socialseed-notifications'

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

describe('notificationsStore', () => {
  let pinia: Pinia
  let store: ReturnType<typeof useNotificationsStore>

  beforeEach(() => {
    vi.clearAllMocks()
    pinia = createPinia()
    setActivePinia(pinia)
    store = useNotificationsStore()
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
    expect(localStorage.getItem(`${STORAGE_KEY}-version`)).toBe('2')

    store.addNotification(makeNotification({ title: 'extra' }))
    store.seedMockNotifications()
    expect(store.notifications).toHaveLength(13)
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
    setActivePinia(createPinia())

    const fresh = useNotificationsStore()

    expect(fresh.notifications).toEqual([])
  })

  it('drops stale seed versions from storage', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([{ id: 'old' }]))
    localStorage.setItem(`${STORAGE_KEY}-version`, '1')
    setActivePinia(createPinia())

    const fresh = useNotificationsStore()

    expect(fresh.notifications).toEqual([])
    expect(localStorage.getItem(`${STORAGE_KEY}-version`)).toBe('2')
  })
})
