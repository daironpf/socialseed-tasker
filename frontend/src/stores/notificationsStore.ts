import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { AppNotification, NotificationCategory } from '@/types/notifications'
import type { HITLRequest } from '@/types/hitl'
import { useSoundEffects } from '@/composables/useSoundEffects'
import { isMockMode, apiMode } from '@/api/client'
import { connectSSE, type SSEHandle } from '@/api/realtime'
import * as notificationsApi from '@/api/notificationsApi'
import { useAuthStore } from '@/stores/authStore'

const STORAGE_KEY = 'socialseed-notifications'
const SEED_VERSION = 3
const PREFS_KEY = 'socialseed-alert-prefs'
/** Client-only ids (mock seeds, local HITL inserts) are never server-backed. */
const LOCAL_ID_PREFIX = 'notif-'

export interface AlertPreferences {
  channels: Record<NotificationCategory, boolean>
}

function loadPreferences(): AlertPreferences {
  const defaults: AlertPreferences = {
    channels: {
      mention: false,
      hitl: true,
      constraint_violation: true,
      agent_failure: true,
      sla: true,
      welcome: true,
    },
  }
  try {
    const raw = localStorage.getItem(PREFS_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<AlertPreferences>
      if (parsed && parsed.channels) {
        return { channels: { ...defaults.channels, ...parsed.channels } }
      }
    }
  } catch {
    // corrupted prefs -> defaults
  }
  return defaults
}

function loadFromStorage(): AppNotification[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const version = parseInt(localStorage.getItem(`${STORAGE_KEY}-version`) || '0', 10)
    if (version < SEED_VERSION) {
      localStorage.removeItem(STORAGE_KEY)
      localStorage.setItem(`${STORAGE_KEY}-version`, String(SEED_VERSION))
      return []
    }
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveToStorage(notifications: AppNotification[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications))
}

function generateId(): string {
  return `${LOCAL_ID_PREFIX}${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function isServerId(id: string): boolean {
  return !id.startsWith(LOCAL_ID_PREFIX)
}

export const useNotificationsStore = defineStore('notifications', () => {
  // Real mode starts empty: history lives in Mongo and is hydrated by
  // fetchNotifications/the stream snapshot (#551).
  const notifications = ref<AppNotification[]>(isMockMode() ? loadFromStorage() : [])
  const preferences = ref<AlertPreferences>(loadPreferences())
  const streamConnected = ref(false)

  const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

  const unreadByCategory = computed(() => {
    const counts: Record<NotificationCategory, number> = {
      mention: 0,
      hitl: 0,
      constraint_violation: 0,
      agent_failure: 0,
      sla: 0,
      welcome: 0,
    }
    for (const n of notifications.value) {
      if (!n.read) counts[n.category]++
    }
    return counts
  })

  function persist() {
    // Real mode never writes localStorage: read state lives server-side.
    if (!isMockMode()) return
    saveToStorage(notifications.value)
  }

  function insertNotification(notif: AppNotification): boolean {
    if (notifications.value.some(n => n.id === notif.id)) return false
    notifications.value.unshift(notif)
    persist()
    if (preferences.value.channels[notif.category]) {
      useSoundEffects().playForCategory(notif.category)
    }
    return true
  }

  function addNotification(data: Omit<AppNotification, 'id' | 'read' | 'createdAt'>) {
    insertNotification({
      id: generateId(),
      read: false,
      createdAt: new Date().toISOString(),
      ...data,
    })
  }

  function setChannelSound(category: NotificationCategory, on: boolean) {
    preferences.value.channels[category] = on
    localStorage.setItem(PREFS_KEY, JSON.stringify(preferences.value))
  }

  function markAsRead(id: string) {
    const n = notifications.value.find(n => n.id === id)
    if (!n) return
    n.read = true
    persist()
    if (!isMockMode() && isServerId(id)) {
      void notificationsApi.markAsRead(id).catch(() => {})
    }
  }

  function markAllAsRead() {
    for (const n of notifications.value) {
      n.read = true
    }
    persist()
    if (!isMockMode()) {
      void notificationsApi.markAllAsRead().catch(() => {})
    }
  }

  function dismiss(id: string) {
    notifications.value = notifications.value.filter(n => n.id !== id)
    persist()
    if (!isMockMode() && isServerId(id)) {
      void notificationsApi.deleteNotification(id).catch(() => {})
    }
  }

  function markManyRead(ids: string[]) {
    for (const id of ids) {
      markAsRead(id)
    }
  }

  function dismissMany(ids: string[]) {
    const idSet = new Set(ids)
    notifications.value = notifications.value.filter(n => !idSet.has(n.id))
    persist()
    if (!isMockMode()) {
      const serverIds = ids.filter(isServerId)
      if (serverIds.length > 0) {
        void Promise.all(serverIds.map(id => notificationsApi.deleteNotification(id))).catch(
          () => {},
        )
      }
    }
  }

  function getFiltered(filter: 'all' | 'unread' | 'action', category?: NotificationCategory) {
    return notifications.value.filter(n => {
      if (category && n.category !== category) return false
      if (filter === 'unread' && n.read) return false
      if (filter === 'action' && !n.requiresAction) return false
      return true
    })
  }

  function ensureHitlNotifications(hitlRequests: HITLRequest[]) {
    for (const req of hitlRequests) {
      if (req.status !== 'pending') continue
      const exists = notifications.value.some(n => n.hitlRequestId === req.id)
      if (exists) continue
      const notif: AppNotification = {
        id: generateId(),
        read: false,
        createdAt: req.createdAt,
        title: 'HITL Approval Required',
        message: `${req.agentAvatar} ${req.agentName}: ${req.title}`,
        category: 'hitl',
        requiresAction: true,
        hitlRequestId: req.id,
        linkTo: { name: 'HITLCommandCenter' },
      }
      notifications.value.unshift(notif)
    }
    persist()
  }

  function seedMockNotifications() {
    if (!isMockMode()) return
    if (notifications.value.length > 0) return
    const now = Date.now()
    const hour = 3600000
    const mocks: (Omit<AppNotification, 'id' | 'read' | 'createdAt'> & { read: boolean; createdAt: string })[] = [
      {
        title: '@alice mentioned you',
        message: 'Can you review the auth flow before we merge?',
        category: 'mention',
        requiresAction: true,
        linkTo: { name: 'issues' },
        read: false,
        createdAt: new Date(now - hour * 0.5).toISOString(),
      },
      {
        title: 'HITL Approval Required',
        message: 'Agent requests DELETE on production users table',
        category: 'hitl',
        requiresAction: true,
        linkTo: { name: 'issues', params: { id: 'ISS-042' } },
        read: false,
        createdAt: new Date(now - hour * 1).toISOString(),
      },
      {
        title: 'Constraint Violation',
        message: 'Rate limit exceeded: 500 req/min on /api/auth',
        category: 'constraint_violation',
        requiresAction: false,
        linkTo: { name: 'constraints' },
        read: false,
        createdAt: new Date(now - hour * 2).toISOString(),
      },
      {
        title: 'Agent Failed',
        message: 'Impact analysis agent crashed on ISS-038',
        category: 'agent_failure',
        requiresAction: false,
        linkTo: { name: 'issues', params: { id: 'ISS-038' } },
        read: true,
        createdAt: new Date(now - hour * 3).toISOString(),
      },
      {
        title: '@bob mentioned you',
        message: 'The dependency graph looks wrong after the last merge',
        category: 'mention',
        requiresAction: false,
        linkTo: { name: 'graph' },
        read: true,
        createdAt: new Date(now - hour * 5).toISOString(),
      },
      {
        title: 'HITL Approval Required',
        message: 'Agent requests push to main branch',
        category: 'hitl',
        requiresAction: true,
        linkTo: { name: 'issues', params: { id: 'ISS-051' } },
        read: false,
        createdAt: new Date(now - hour * 6).toISOString(),
      },
      {
        title: 'Constraint Violation',
        message: 'Circular dependency detected: ISS-015 -> ISS-034 -> ISS-015',
        category: 'constraint_violation',
        requiresAction: true,
        linkTo: { name: 'constraints' },
        read: false,
        createdAt: new Date(now - hour * 8).toISOString(),
      },
      {
        title: '@carol mentioned you',
        message: 'PR #247 needs your review before release',
        category: 'mention',
        requiresAction: true,
        linkTo: { name: 'issues', params: { id: 'ISS-100' } },
        read: false,
        createdAt: new Date(now - hour * 10).toISOString(),
      },
      {
        title: 'Agent Completed',
        message: 'Root cause analysis finished for ISS-061',
        category: 'agent_failure',
        requiresAction: false,
        linkTo: { name: 'issues', params: { id: 'ISS-061' } },
        read: true,
        createdAt: new Date(now - hour * 12).toISOString(),
      },
      {
        title: 'HITL Approval Required',
        message: 'Agent requests schema migration on production DB',
        category: 'hitl',
        requiresAction: true,
        linkTo: { name: 'issues', params: { id: 'ISS-081' } },
        read: true,
        createdAt: new Date(now - hour * 24).toISOString(),
      },
      {
        title: 'Constraint Violation',
        message: 'Max dependencies exceeded for component: API Gateway (12/10)',
        category: 'constraint_violation',
        requiresAction: false,
        linkTo: { name: 'constraints' },
        read: true,
        createdAt: new Date(now - hour * 36).toISOString(),
      },
      {
        title: '@dave mentioned you',
        message: 'Can you check the blast radius for ISS-003?',
        category: 'mention',
        requiresAction: false,
        linkTo: { name: 'graph' },
        read: true,
        createdAt: new Date(now - hour * 48).toISOString(),
      },
    ]
    for (const m of mocks) {
      const notif: AppNotification = {
        id: generateId(),
        read: m.read,
        createdAt: m.createdAt,
        title: m.title,
        message: m.message,
        category: m.category,
        requiresAction: m.requiresAction,
        linkTo: m.linkTo,
      }
      notifications.value.push(notif)
    }
    localStorage.setItem(`${STORAGE_KEY}-version`, String(SEED_VERSION))
    persist()
  }

  // ------------------------------------------------------------------
  // Real mode: REST hydration + #550 SSE stream (#551)
  // ------------------------------------------------------------------

  /** Server items replace the server set; local `notif-` items (HITL) survive. */
  function hydrate(items: AppNotification[]) {
    const locals = notifications.value.filter(n => !isServerId(n.id))
    const serverIds = new Set(items.map(n => n.id))
    const merged = [...items, ...locals.filter(n => !serverIds.has(n.id))]
    merged.sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    notifications.value = merged
    persist()
  }

  async function fetchNotifications() {
    if (isMockMode()) {
      seedMockNotifications()
      return
    }
    try {
      const items = await notificationsApi.fetchNotifications()
      hydrate(items)
    } catch {
      // client.ts already surfaced the error toast; keep the last known list.
    }
  }

  let sseHandle: SSEHandle | null = null

  function handleStreamEvent(event: string, data: unknown) {
    if (event === 'connected') {
      const payload = (data ?? {}) as { snapshot?: unknown }
      if (Array.isArray(payload.snapshot)) {
        hydrate(
          payload.snapshot.map(item =>
            notificationsApi.normalizeNotification(item as Record<string, unknown>),
          ),
        )
      }
      return
    }
    if (event === 'notification_created') {
      insertNotification(
        notificationsApi.normalizeNotification((data ?? {}) as Record<string, unknown>),
      )
    }
  }

  function startStream() {
    if (isMockMode() || sseHandle) return
    sseHandle = connectSSE(
      '/notifications/stream',
      {
        onEvent: handleStreamEvent,
        onState: state => {
          streamConnected.value = state === 'live'
        },
      },
      { events: ['connected', 'notification_created', 'ping'], authenticate: true },
    )
  }

  function stopStream() {
    if (!sseHandle) return
    sseHandle.close()
    sseHandle = null
    streamConnected.value = false
  }

  function startRealtime() {
    // Idempotent: the auth and apiMode watchers can both fire in one flush.
    if (sseHandle) return
    void fetchNotifications()
    startStream()
  }

  const authStore = useAuthStore()

  // Session restored before the store exists (router guard awaits
  // initSession): connect right away; otherwise the watcher below fires
  // when the login lands (pattern of chatStore #540).
  if (!isMockMode() && authStore.user) {
    startRealtime()
  }

  watch(
    () => authStore.user,
    user => {
      if (isMockMode()) return
      if (user) {
        startRealtime()
      } else {
        // Session lost: tear the stream down and drop the previous user's data.
        stopStream()
        notifications.value = []
      }
    },
  )

  watch(apiMode, () => {
    if (isMockMode()) {
      stopStream()
      notifications.value = []
      seedMockNotifications()
    } else {
      notifications.value = []
      if (authStore.user) startRealtime()
    }
  })

  return {
    notifications,
    preferences,
    unreadCount,
    unreadByCategory,
    streamConnected,
    addNotification,
    markAsRead,
    markAllAsRead,
    markManyRead,
    dismiss,
    dismissMany,
    setChannelSound,
    getFiltered,
    ensureHitlNotifications,
    seedMockNotifications,
    fetchNotifications,
    startStream,
    stopStream,
  }
})
