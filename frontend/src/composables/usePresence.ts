import { ref, onMounted, onUnmounted, computed } from 'vue'

export interface PresenceUser {
  id: string
  username: string
  avatar: string
  type: 'human' | 'agent'
  lastSeen: number
  viewingField?: string
  isTyping?: boolean
  typingMessage?: string
}

const presenceMap = ref<Map<string, PresenceUser[]>>(new Map())
const localPresenceId = ref(`user-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`)
let heartbeatInterval: ReturnType<typeof setInterval> | null = null
let expireInterval: ReturnType<typeof setInterval> | null = null

const HEARTBEAT_MS = 30000
const EXPIRE_MS = 60000

function generateMockPresence(_issueId: string): PresenceUser[] {
  const roll = Math.random()
  if (roll > 0.6) return []
  const count = Math.random() > 0.7 ? 2 : 1
  const agents = [
    { id: 'agent-arch', username: 'Arch-Bot', avatar: '🏗️', type: 'agent' as const },
    { id: 'agent-review', username: 'Review-Bot', avatar: '🔍', type: 'agent' as const },
    { id: 'agent-test', username: 'Test-Bot', avatar: '🧪', type: 'agent' as const },
  ]
  const humans = [
    { id: 'user-alice', username: 'alice', avatar: '👩‍💻', type: 'human' as const },
    { id: 'user-bob', username: 'bob', avatar: '👨‍💻', type: 'human' as const },
  ]
  const pool = [...agents, ...humans]
  return Array.from({ length: count }, () => {
    const u = pool[Math.floor(Math.random() * pool.length)]
    return {
      ...u,
      lastSeen: Date.now() - Math.floor(Math.random() * 30000),
      isTyping: Math.random() > 0.6,
      typingMessage: Math.random() > 0.5 ? 'Analyzing dependencies...' : undefined,
    }
  })
}

export function usePresence(issueId: string) {
  const viewers = computed(() => {
    const list = presenceMap.value.get(issueId) || []
    const now = Date.now()
    return list.filter(u => now - u.lastSeen < EXPIRE_MS && u.id !== localPresenceId.value)
  })

  const typingAgents = computed(() =>
    viewers.value.filter(u => u.type === 'agent' && u.isTyping)
  )

  const hasConflict = computed(() => {
    const fields = viewers.value.filter(u => u.viewingField).map(u => u.viewingField)
    return fields.length > 1 && new Set(fields).size < fields.length
  })

  function joinPresence() {
    const list = presenceMap.value.get(issueId) || []
    const localUser: PresenceUser = {
      id: localPresenceId.value,
      username: 'You',
      avatar: '👤',
      type: 'human',
      lastSeen: Date.now(),
    }
    presenceMap.value.set(issueId, [...list.filter(u => u.id !== localPresenceId.value), localUser])

    if (!presenceMap.value.has(`mock-${issueId}`)) {
      presenceMap.value.set(`mock-${issueId}`, generateMockPresence(issueId))
    }
  }

  function updateField(fieldName: string | undefined) {
    const list = presenceMap.value.get(issueId) || []
    const idx = list.findIndex(u => u.id === localPresenceId.value)
    if (idx >= 0) {
      list[idx].viewingField = fieldName
      list[idx].lastSeen = Date.now()
      presenceMap.value.set(issueId, [...list])
    }
  }

  function leavePresence() {
    const list = presenceMap.value.get(issueId) || []
    presenceMap.value.set(issueId, list.filter(u => u.id !== localPresenceId.value))
  }

  function heartbeat() {
    const list = presenceMap.value.get(issueId) || []
    const idx = list.findIndex(u => u.id === localPresenceId.value)
    if (idx >= 0) {
      list[idx].lastSeen = Date.now()
      presenceMap.value.set(issueId, [...list])
    }

    const mockKey = `mock-${issueId}`
    const mockList = presenceMap.value.get(mockKey) || []
    const now = Date.now()
    presenceMap.value.set(mockKey, mockList.map(u => ({
      ...u,
      lastSeen: now - Math.floor(Math.random() * 15000),
      isTyping: Math.random() > 0.5,
    })))
  }

  function expireStale() {
    const now = Date.now()
    for (const [key, list] of presenceMap.value.entries()) {
      const filtered = list.filter(u => now - u.lastSeen < EXPIRE_MS)
      presenceMap.value.set(key, filtered)
    }
  }

  onMounted(() => {
    joinPresence()
    heartbeatInterval = setInterval(heartbeat, HEARTBEAT_MS)
    expireInterval = setInterval(expireStale, 10000)
  })

  onUnmounted(() => {
    leavePresence()
    if (heartbeatInterval) clearInterval(heartbeatInterval)
    if (expireInterval) clearInterval(expireInterval)
  })

  return {
    viewers,
    typingAgents,
    hasConflict,
    updateField,
    joinPresence,
    leavePresence,
  }
}
