import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AppNotification, NotificationCategory } from '@/types/notifications'

const STORAGE_KEY = 'socialseed-notifications'

function loadFromStorage(): AppNotification[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
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

  const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

  const unreadByCategory = computed(() => {
    const counts: Record<NotificationCategory, number> = {
      mention: 0,
      hitl: 0,
      constraint_violation: 0,
      agent_failure: 0,
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

  function getFiltered(filter: 'all' | 'unread' | 'action', category?: NotificationCategory) {
    return notifications.value.filter(n => {
      if (category && n.category !== category) return false
      if (filter === 'unread' && n.read) return false
      if (filter === 'action' && !n.requiresAction) return false
      return true
    })
  }

  function seedMockNotifications() {
    if (notifications.value.length > 0) return
    const mocks: Omit<AppNotification, 'id' | 'read' | 'createdAt'>[] = [
      {
        title: '@alice mentioned you',
        message: 'Can you review the auth flow before we merge?',
        category: 'mention',
        requiresAction: true,
        linkTo: { name: 'issues' },
      },
      {
        title: 'HITL Approval Required',
        message: 'Agent requests DELETE on production users table',
        category: 'hitl',
        requiresAction: true,
        linkTo: { name: 'issues', params: { id: 'ISS-042' } },
      },
      {
        title: 'Constraint Violation',
        message: 'Rate limit exceeded: 500 req/min on /api/auth',
        category: 'constraint_violation',
        requiresAction: false,
        linkTo: { name: 'constraints' },
      },
      {
        title: 'Agent Failed',
        message: 'Impact analysis agent crashed on ISS-038',
        category: 'agent_failure',
        requiresAction: false,
        linkTo: { name: 'issues', params: { id: 'ISS-038' } },
      },
      {
        title: '@bob mentioned you',
        message: 'The dependency graph looks wrong after the last merge',
        category: 'mention',
        requiresAction: false,
        linkTo: { name: 'graph' },
      },
      {
        title: 'HITL Approval Required',
        message: 'Agent requests push to main branch',
        category: 'hitl',
        requiresAction: true,
        linkTo: { name: 'issues', params: { id: 'ISS-051' } },
      },
    ]
    for (const m of mocks) {
      addNotification(m)
    }
  }

  return {
    notifications,
    unreadCount,
    unreadByCategory,
    addNotification,
    markAsRead,
    markAllAsRead,
    dismiss,
    getFiltered,
    seedMockNotifications,
  }
})
