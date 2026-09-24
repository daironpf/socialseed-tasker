export type QueueEntity = 'issue' | 'policy'
export type QueueOperation = 'create' | 'update'
export type QueueEntryStatus = 'pending' | 'conflict'

export interface QueuedMutation {
  id: string
  entity: QueueEntity
  operation: QueueOperation
  entityId: string | null
  payload: Record<string, unknown>
  remotePayload: Record<string, unknown> | null
  status: QueueEntryStatus
  retries: number
  timestamp: string
}

const STORAGE_KEY = 'socialseed-offline-queue'

export function loadQueue(): QueuedMutation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) return parsed as QueuedMutation[]
    }
  } catch {
    // corrupted storage -> start with empty queue
  }
  return []
}

export function saveQueue(queue: QueuedMutation[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue))
  } catch {
    // storage unavailable; in-memory queue still works
  }
}

export function createQueueEntry(input: {
  entity: QueueEntity
  operation: QueueOperation
  entityId?: string | null
  payload: Record<string, unknown>
  conflict?: boolean
}): QueuedMutation {
  return {
    id: `q-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    entity: input.entity,
    operation: input.operation,
    entityId: input.entityId ?? null,
    payload: input.payload,
    remotePayload: input.conflict ? simulateRemoteVersion(input.payload) : null,
    status: input.conflict ? 'conflict' : 'pending',
    retries: 0,
    timestamp: new Date().toISOString(),
  }
}

const DRIFT_KEYS = ['priority', 'status', 'is_active', 'level', 'title', 'name']
const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
const STATUSES = ['OPEN', 'IN_PROGRESS', 'BLOCKED', 'CLOSED']

export function simulateRemoteVersion(payload: Record<string, unknown>): Record<string, unknown> {
  const remote: Record<string, unknown> = JSON.parse(JSON.stringify(payload))
  for (const key of DRIFT_KEYS) {
    if (!(key in remote)) continue
    const value = remote[key]
    if (key === 'priority' && typeof value === 'string') {
      const idx = PRIORITIES.indexOf(value)
      remote[key] = PRIORITIES[(idx + 1) % PRIORITIES.length] || PRIORITIES[1]
      return remote
    }
    if (key === 'status' && typeof value === 'string') {
      const idx = STATUSES.indexOf(value)
      remote[key] = STATUSES[(idx + 1) % STATUSES.length] || STATUSES[0]
      return remote
    }
    if (key === 'is_active' && typeof value === 'boolean') {
      remote[key] = !value
      return remote
    }
    if ((key === 'title' || key === 'name' || key === 'level') && typeof value === 'string') {
      remote[key] = `${value} (remote)`
      return remote
    }
  }
  remote._remoteEdit = true
  return remote
}
