import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { setActivePinia } from 'pinia'
import { mountComponent } from '@/test/mount'
import IssueDetailView from '@/views/IssueDetailView.vue'
import GitHubSyncCard from '@/components/issue/GitHubSyncCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'
import { connectSSE, type SSEHandle, type SSEHandlers } from '@/api/realtime'
import { setApiMode } from '@/api/client'
import * as issuesApi from '@/api/issuesApi'
import * as usersApi from '@/api/usersApi'
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

vi.mock('@/api/usersApi', () => ({
  fetchUsers: vi.fn(),
}))

vi.mock('@/composables/usePresence', async () => {
  const { ref } = await import('vue')
  return {
    usePresence: () => ({
      viewers: ref([]),
      typingAgents: ref([]),
      hasConflict: ref(false),
    }),
  }
})

vi.mock('@/api/realtime', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/realtime')>()
  return {
    ...actual,
    connectSSE: vi.fn(() => ({ close: vi.fn() })),
  }
})

const GITHUB_SYNC = {
  issue_number: 42,
  github_url: 'https://github.com/acme/repo/issues/42',
  sync_status: 'SYNCED' as const,
  last_synced_at: '2026-01-01T00:00:00Z',
}

function makeIssue(id: string, title: string, updatedAt = '2026-01-01T00:00:00Z'): Issue {
  return {
    id,
    title,
    description: 'description',
    status: IssueStatus.OPEN,
    priority: IssuePriority.MEDIUM,
    component_id: 'comp-1',
    project_id: 'socialseed-tasker',
    labels: [],
    dependencies: [],
    blocks: [],
    affects: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: updatedAt,
    closed_at: null,
    architectural_constraints: [],
    github_sync: { ...GITHUB_SYNC },
  }
}

function handlersFor(path: string): SSEHandlers | undefined {
  return vi.mocked(connectSSE).mock.calls.find(([p]) => p === path)?.[1]
}

function handleFor(path: string): SSEHandle | undefined {
  const index = vi.mocked(connectSSE).mock.calls.findIndex(([p]) => p === path)
  if (index === -1) return undefined
  return vi.mocked(connectSSE).mock.results[index].value as SSEHandle
}

describe('IssueDetailView GitHub sync', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setApiMode('real')
    vi.mocked(usersApi.fetchUsers).mockResolvedValue([])
  })

  afterEach(() => {
    document.body.innerHTML = ''
    setApiMode('mock')
  })

  async function mountView(issue: Issue) {
    const mounted = mountComponent(IssueDetailView, { props: { issue } })
    setActivePinia(mounted.pinia)
    const store = useIssuesStore()
    store.issues = [issue]
    await flushPromises()
    await mounted.wrapper.vm.$nextTick()
    return { wrapper: mounted.wrapper, store }
  }

  it('applies a sync:updated event without mutating the issue prop', async () => {
    const initial = makeIssue('ISS-1', 'Initial title')
    const { wrapper, store } = await mountView(initial)
    const fresh = { ...initial, title: 'Updated by GitHub', updated_at: '2026-01-02T00:00:00Z' }

    wrapper.findComponent(GitHubSyncCard).vm.$emit('sync:updated', fresh)
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(initial.title).toBe('Initial title')
    expect(store.issues[0].title).toBe('Updated by GitHub')
    expect(wrapper.find('input').element.value).toBe('Updated by GitHub')
  })

  it('refreshes from the API on a sync SSE event', async () => {
    const initial = makeIssue('ISS-1', 'Initial title')
    const { wrapper, store } = await mountView(initial)
    vi.mocked(issuesApi.fetchIssue).mockResolvedValue({
      ...initial,
      title: 'Fresh from server',
      updated_at: '2026-01-02T00:00:00Z',
    })

    handlersFor('/issues/ISS-1/github-sync/stream')?.onEvent('sync', undefined)
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(issuesApi.fetchIssue).toHaveBeenCalledWith('ISS-1')
    expect(initial.title).toBe('Initial title')
    expect(store.issues[0].title).toBe('Fresh from server')
    expect(wrapper.find('input').element.value).toBe('Fresh from server')
  })

  it('closes the previous stream and ignores its late response after switching issue', async () => {
    const first = makeIssue('ISS-1', 'First issue')
    const second = makeIssue('ISS-2', 'Second issue')
    let resolveFetch: (issue: Issue) => void = () => {}
    vi.mocked(issuesApi.fetchIssue).mockReturnValue(
      new Promise<Issue>((resolve) => {
        resolveFetch = resolve
      }),
    )

    const { wrapper, store } = await mountView(first)
    store.issues = [first, second]
    const firstHandle = handleFor('/issues/ISS-1/github-sync/stream')

    handlersFor('/issues/ISS-1/github-sync/stream')?.onEvent('sync', undefined)
    await wrapper.setProps({ issue: second })
    await flushPromises()

    expect(firstHandle?.close).toHaveBeenCalled()
    expect(handlersFor('/issues/ISS-2/github-sync/stream')).toBeDefined()

    resolveFetch({ ...first, title: 'Late first issue', updated_at: '2026-01-02T00:00:00Z' })
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(store.issues.find((i) => i.id === 'ISS-1')?.title).toBe('First issue')
    expect(wrapper.find('input').element.value).toBe('Second issue')
  })
})
