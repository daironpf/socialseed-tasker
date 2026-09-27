import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia, type Pinia } from 'pinia'
import { useUiStore } from '@/stores/uiStore'
import type { QueuedMutation } from '@/utils/offlineQueue'

const QUEUE_KEY = 'socialseed-offline-queue'

function readStoredQueue(): QueuedMutation[] {
  const raw = localStorage.getItem(QUEUE_KEY)
  return raw ? (JSON.parse(raw) as QueuedMutation[]) : []
}

describe('uiStore', () => {
  let pinia: Pinia
  let store: ReturnType<typeof useUiStore>

  beforeEach(() => {
    vi.clearAllMocks()
    vi.clearAllTimers()
    pinia = createPinia()
    setActivePinia(pinia)
    store = useUiStore()
    store.setApiMode('mock')
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('filters', () => {
    it('detects active filters and clears them', () => {
      expect(store.hasActiveFilters()).toBe(false)

      store.setFilter('status', ['OPEN'])
      expect(store.hasActiveFilters()).toBe(true)

      store.setFilter('search', 'api')
      store.setFilter('hasTechDebt', true)
      store.clearFilters()

      expect(store.hasActiveFilters()).toBe(false)
      expect(store.filters.status).toEqual([])
      expect(store.filters.search).toBe('')
      expect(store.filters.hasTechDebt).toBeNull()
    })

    it('maps filters to backend query params', () => {
      store.setFilter('status', ['OPEN', 'BLOCKED'])
      store.setFilter('priority', ['HIGH'])
      store.setFilter('component', 'comp-1')

      const params = store.getBackendFilters()

      expect(params.status).toBe('OPEN,BLOCKED')
      expect(params.priority).toBe('HIGH')
      expect(params.component).toBe('comp-1')
      expect(store.getBackendFilters).toBeDefined()
    })

    it('serializes unset backend filters to undefined', () => {
      const params = store.getBackendFilters()
      expect(params.status).toBeUndefined()
      expect(params.priority).toBeUndefined()
      expect(params.component).toBeUndefined()
      expect(params.project).toBeUndefined()
    })
  })

  describe('saved searches', () => {
    it('saves, loads and deletes searches with localStorage persistence', () => {
      store.setFilter('status', ['OPEN'])
      const saved = store.saveSearch('My search')

      expect(store.savedSearches[0].name).toBe('My search')
      expect(JSON.parse(localStorage.getItem('savedSearches')!)).toHaveLength(1)

      store.clearFilters()
      store.loadSearch(saved.id)
      expect(store.filters.status).toEqual(['OPEN'])

      store.deleteSearch(saved.id)
      expect(store.savedSearches).toHaveLength(0)
      expect(JSON.parse(localStorage.getItem('savedSearches')!)).toHaveLength(0)
    })

    it('caps saved searches at 10 entries', () => {
      for (let i = 0; i < 12; i++) {
        store.saveSearch(`search-${i}`)
      }
      expect(store.savedSearches).toHaveLength(10)
      expect(store.savedSearches[0].name).toBe('search-11')
    })
  })

  describe('offline sync queue (issue #515)', () => {
    it('enqueues a mutation, persists it and flips the connection state', () => {
      const entry = store.enqueueMutation({
        entity: 'issue',
        operation: 'create',
        entityId: null,
        payload: { title: 'Queued' },
      })

      expect(store.syncQueue).toHaveLength(1)
      expect(store.syncQueue[0].id).toBe(entry.id)
      expect(store.syncQueue[0].status).toBe('pending')
      expect(store.connectionState).toBe('OFFLINE_QUEUED')
      expect(store.pendingSyncCount).toBe(1)
      expect(readStoredQueue()).toHaveLength(1)
    })

    it('marks a duplicate update of the same entity as a conflict', () => {
      store.enqueueMutation({ entity: 'issue', operation: 'update', entityId: 'ISS-1', payload: { title: 'one' } })
      const second = store.enqueueMutation({ entity: 'issue', operation: 'update', entityId: 'ISS-1', payload: { title: 'two' } })

      expect(second.status).toBe('conflict')
      expect(second.remotePayload).not.toBeNull()
    })

    it('flags conflicts for updates while degraded', () => {
      store.setNetworkMode('degraded')
      const entry = store.enqueueMutation({ entity: 'issue', operation: 'update', entityId: 'ISS-9', payload: { title: 'x' } })

      expect(entry.status).toBe('conflict')
      expect(store.connectionState).toBe('OFFLINE_QUEUED')
    })

    it('removes entries and restores the connection state', () => {
      const entry = store.enqueueMutation({ entity: 'issue', operation: 'create', entityId: null, payload: {} })
      store.removeQueued(entry.id)

      expect(store.syncQueue).toHaveLength(0)
      expect(readStoredQueue()).toHaveLength(0)
      expect(store.connectionState).toBe('SYNCED')
      expect(store.pendingSyncCount).toBe(0)
    })

    it('increments retries on retryQueued', () => {
      const entry = store.enqueueMutation({ entity: 'policy', operation: 'update', entityId: 'P-1', payload: {} })
      store.retryQueued(entry.id)

      expect(store.syncQueue[0].retries).toBe(1)
      expect(readStoredQueue()[0].retries).toBe(1)
    })

    it('flushes pending entries but keeps conflicts', () => {
      vi.useFakeTimers()
      store.enqueueMutation({ entity: 'issue', operation: 'create', entityId: null, payload: { title: 'go' } })
      store.enqueueMutation({ entity: 'issue', operation: 'update', entityId: 'ISS-1', payload: { title: 'a' } })
      store.enqueueMutation({ entity: 'issue', operation: 'update', entityId: 'ISS-1', payload: { title: 'b' } })
      expect(store.syncQueue).toHaveLength(3)

      store.flushQueue()
      vi.advanceTimersByTime(400)
      expect(store.connectionState).toBe('SYNCING')

      vi.advanceTimersByTime(900)

      expect(store.syncQueue).toHaveLength(1)
      expect(store.syncQueue[0].status).toBe('conflict')
      expect(store.connectionState).toBe('OFFLINE_QUEUED')
      expect(readStoredQueue()).toHaveLength(1)
    })

    it('sets network mode with persistence and derives the connection state', () => {
      store.setNetworkMode('degraded')
      expect(store.networkMode).toBe('degraded')
      expect(localStorage.getItem('networkMode')).toBe('degraded')
      expect(store.connectionState).toBe('DEGRADED')

      store.setNetworkMode('offline')
      expect(store.connectionState).toBe('SYNCED')
      expect(localStorage.getItem('networkMode')).toBe('offline')

      store.setNetworkMode('online')
      expect(store.connectionState).toBe('SYNCED')
      expect(store.pendingSyncCount).toBe(0)
    })
  })

  describe('api mode (issue #517)', () => {
    it('defaults to mock and toggles to real with persistence', () => {
      expect(store.apiMode).toBe('mock')
      expect(store.isMockApi).toBe(true)

      store.setApiMode('real')

      expect(store.apiMode).toBe('real')
      expect(store.isMockApi).toBe(false)
      expect(localStorage.getItem('socialseed-api-mode')).toBe('real')
    })
  })

  describe('project, locale and theme persistence', () => {
    it('persists the selected project and mirrors it into filters', () => {
      store.setProject('auth-service')
      expect(store.currentProject).toBe('auth-service')
      expect(localStorage.getItem('currentProject')).toBe('auth-service')
      expect(store.filters.project).toBe('auth-service')
    })

    it('persists locale and toast theme', () => {
      store.setLocale('es')
      store.setToastTheme('enterprise')

      expect(localStorage.getItem('locale')).toBe('es')
      expect(localStorage.getItem('toast-theme')).toBe('enterprise')
    })
  })
})
