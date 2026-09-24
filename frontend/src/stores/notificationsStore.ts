import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AppNotification, NotificationCategory } from '@/types/notifications'
import type { HITLRequest } from '@/types/hitl'
import { useSoundEffects } from '@/composables/useSoundEffects'

const STORAGE_KEY = 'socialseed-notifications'
const SEED_VERSION = 2
const PREFS_KEY = 'socialseed-alert-prefs'

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
  return `notif-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<AppNotification[]>(loadFromStorage())
  const preferences = ref<AlertPreferences>(loadPreferences())

  const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

  const unreadByCategory = computed(() => {
    const counts: Record<NotificationCategory, number> = {
      mention: 0,
      hitl: 0,
      constraint_violation: 0,
      agent_failure: 0,
      sla: 0,
    }
    for (const n of notifications.value) {
      if (!n.read) counts[n.category]++
    }
    return counts
  })

  function persist() {
    saveToStorage(notifications.value)
  }

  function addNotification(data: Omit<AppNotification, 'id' | 'read' | 'createdAt'>) {
    const notif: AppNotification = {
      id: generateId(),
      read: false,
      createdAt: new Date().toISOString(),
      ...data,
    }
    notifications.value.unshift(notif)
    persist()
    if (preferences.value.channels[notif.category]) {
      useSoundEffects().playForCategory(notif.category)
    }
  }

  function setChannelSound(category: NotificationCategory, on: boolean) {
    preferences.value.channels[category] = on
    localStorage.setItem(PREFS_KEY, JSON.stringify(preferences.value))
  }

  function markAsRead(id: string) {
    const n = notifications.value.find(n => n.id === id)
    if (n) {
      n.read = true
      persist()
    }
  }

  function markAllAsRead() {
    for (const n of notifications.value) {
      n.read = true
    }
    persist()
  }

  function dismiss(id: string) {
    notifications.value = notifications.value.filter(n => n.id !== id)
    persist()
  }

  function markManyRead(ids: string[]) {
    const idSet = new Set(ids)
    for (const n of notifications.value) {
      if (idSet.has(n.id)) n.read = true
    }
    persist()
  }

  function dismissMany(ids: string[]) {
    const idSet = new Set(ids)
    notifications.value = notifications.value.filter(n => !idSet.has(n.id))
    persist()
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

  return {
    notifications,
    preferences,
    unreadCount,
    unreadByCategory,
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
  }
})
