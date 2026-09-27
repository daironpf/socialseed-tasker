import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia, type Pinia } from 'pinia'
import { useIssuesStore } from '@/stores/issuesStore'
import { useUiStore } from '@/stores/uiStore'
import * as api from '@/api/issuesApi'
import { IssueStatus, IssuePriority, type Issue } from '@/types'

vi.mock('@/api/issuesApi', () => ({
  fetchIssues: vi.fn(),
  fetchIssue: vi.fn(),
  createIssue: vi.fn(),
  updateIssue: vi.fn(),
  deleteIssue: vi.fn(),
  closeIssue: vi.fn(),
  fetchBlockedIssues: vi.fn(),
}))

function makeIssue(overrides: Partial<Issue> = {}): Issue {
  return {
    id: 'ISS-1',
    title: 'Implement API',
    description: '',
    status: IssueStatus.OPEN,
    priority: IssuePriority.MEDIUM,
    component_id: 'comp-1',
    project_id: 'socialseed-tasker',
    labels: [],
    dependencies: [],
    blocks: [],
    affects: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    closed_at: null,
    architectural_constraints: [],
    ...overrides,
  }
}

describe('issuesStore', () => {
  let pinia: Pinia
  let store: ReturnType<typeof useIssuesStore>
  let ui: ReturnType<typeof useUiStore>

  beforeEach(() => {
    vi.clearAllMocks()
    pinia = createPinia()
    setActivePinia(pinia)
    ui = useUiStore()
    store = useIssuesStore()
  })

  describe('fetchIssues', () => {
    it('stores items and pagination on success', async () => {
      const items = [makeIssue()]
      vi.mocked(api.fetchIssues).mockResolvedValue({
        items,
        pagination: { page: 1, limit: 50, total: 1, has_next: false, has_prev: false },
      })

      await store.fetchIssues()

      expect(store.issues).toHaveLength(1)
      expect(store.pagination?.total).toBe(1)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(api.fetchIssues).toHaveBeenCalledWith(1, 50, undefined, undefined, undefined, undefined)
    })

    it('records the error and clears the list on failure', async () => {
      vi.mocked(api.fetchIssues).mockRejectedValue(new Error('boom'))

      await store.fetchIssues()

      expect(store.error).toBe('boom')
      expect(store.issues).toHaveLength(0)
      expect(store.loading).toBe(false)
    })
  })

  describe('createIssue', () => {
    it('prepends the API-created issue when online', async () => {
      const created = makeIssue({ id: 'ISS-new', title: 'Fresh' })
      vi.mocked(api.createIssue).mockResolvedValue(created)

      const result = await store.createIssue({ title: 'Fresh', component_id: 'comp-1' })

      expect(result?.id).toBe('ISS-new')
      expect(store.issues[0].id).toBe('ISS-new')
      expect(ui.syncQueue).toHaveLength(0)
    })

    it('creates a local issue and queues the mutation when offline', async () => {
      ui.setNetworkMode('offline')

      const result = await store.createIssue({ title: 'Offline issue', component_id: 'comp-1' })

      expect(result?.id).toMatch(/^local-/)
      expect(store.issues[0].title).toBe('Offline issue')
      expect(api.createIssue).not.toHaveBeenCalled()
      expect(ui.syncQueue).toHaveLength(1)
      expect(ui.syncQueue[0].operation).toBe('create')
      expect(ui.connectionState).toBe('OFFLINE_QUEUED')
    })
  })

  describe('updateIssue', () => {
    it('merges locally and queues when offline', async () => {
      store.issues = [makeIssue()]
      ui.setNetworkMode('offline')

      const result = await store.updateIssue('ISS-1', { title: 'Renamed' })

      expect(result?.title).toBe('Renamed')
      expect(store.issues[0].title).toBe('Renamed')
      expect(api.updateIssue).not.toHaveBeenCalled()
      expect(ui.syncQueue).toHaveLength(1)
      expect(ui.syncQueue[0].operation).toBe('update')
      expect(ui.syncQueue[0].entityId).toBe('ISS-1')
    })

    it('replaces the issue from the API when online', async () => {
      store.issues = [makeIssue()]
      vi.mocked(api.updateIssue).mockResolvedValue(makeIssue({ title: 'Server title' }))

      const result = await store.updateIssue('ISS-1', { title: 'Server title' })

      expect(result?.title).toBe('Server title')
      expect(store.issues[0].title).toBe('Server title')
      expect(ui.syncQueue).toHaveLength(0)
    })

    it('returns null for unknown ids when offline', async () => {
      ui.setNetworkMode('offline')
      const result = await store.updateIssue('missing', { title: 'x' })
      expect(result).toBeNull()
    })
  })

  describe('deleteIssue / closeIssue', () => {
    it('removes the issue from the list on successful delete', async () => {
      store.issues = [makeIssue(), makeIssue({ id: 'ISS-2' })]
      vi.mocked(api.deleteIssue).mockResolvedValue(undefined)

      const ok = await store.deleteIssue('ISS-1')

      expect(ok).toBe(true)
      expect(store.issues).toHaveLength(1)
      expect(store.issues[0].id).toBe('ISS-2')
    })

    it('keeps the list and records the error when delete fails', async () => {
      store.issues = [makeIssue()]
      vi.mocked(api.deleteIssue).mockRejectedValue(new Error('nope'))

      const ok = await store.deleteIssue('ISS-1')

      expect(ok).toBe(false)
      expect(store.error).toBe('nope')
      expect(store.issues).toHaveLength(1)
    })

    it('marks the issue as CLOSED on close', async () => {
      store.issues = [makeIssue()]
      vi.mocked(api.closeIssue).mockResolvedValue(
        makeIssue({ status: IssueStatus.CLOSED, closed_at: '2026-09-26T00:00:00Z' }),
      )

      const result = await store.closeIssue('ISS-1')

      expect(result?.status).toBe(IssueStatus.CLOSED)
      expect(store.issues[0].status).toBe(IssueStatus.CLOSED)
    })
  })

  describe('computed counts', () => {
    it('counts open and blocked issues', () => {
      store.issues = [
        makeIssue(),
        makeIssue({ id: 'ISS-2', status: IssueStatus.BLOCKED }),
        makeIssue({ id: 'ISS-3', status: IssueStatus.CLOSED }),
      ]

      expect(store.openIssuesCount).toBe(2)
      expect(store.blockedIssuesCount).toBe(1)
    })
  })

  describe('filteredIssues', () => {
    beforeEach(() => {
      store.issues = [
        makeIssue({ id: 'A', title: 'Alpha auth fix', status: IssueStatus.OPEN, priority: IssuePriority.HIGH, labels: ['auth'] }),
        makeIssue({ id: 'B', title: 'Beta billing', status: IssueStatus.CLOSED, priority: IssuePriority.CRITICAL, labels: ['billing'] }),
        makeIssue({ id: 'C', project_id: 'auth-service', title: 'Gamma other project' }),
      ]
    })

    it('always scopes to the current project', () => {
      expect(store.filteredIssues.map(i => i.id)).toEqual(['A', 'B'])
    })

    it('applies the status filter via uiStore', () => {
      ui.setFilter('status', [IssueStatus.OPEN])
      expect(store.filteredIssues.map(i => i.id)).toEqual(['A'])
    })

    it('searches title and id case-insensitively', () => {
      ui.setFilter('search', 'ALPHA')
      expect(store.filteredIssues.map(i => i.id)).toEqual(['A'])
    })

    it('combines conditions with the AND operator', () => {
      ui.setFilter('status', [IssueStatus.OPEN])
      ui.setFilter('priority', [IssuePriority.CRITICAL])
      expect(store.filteredIssues).toHaveLength(0)
    })

    it('combines conditions with the OR operator', () => {
      ui.setFilter('status', [IssueStatus.CLOSED])
      ui.setFilter('priority', [IssuePriority.HIGH])
      ui.setFilter('operator', 'OR')
      expect(store.filteredIssues.map(i => i.id).sort()).toEqual(['A', 'B'])
    })

    it('filters by labels', () => {
      ui.setFilter('labels', ['billing'])
      expect(store.filteredIssues.map(i => i.id)).toEqual(['B'])
    })

    it('returns to project-only scoping after clearFilters', () => {
      ui.setFilter('status', [IssueStatus.OPEN])
      ui.clearFilters()
      expect(store.filteredIssues.map(i => i.id)).toEqual(['A', 'B'])
    })
  })
})
