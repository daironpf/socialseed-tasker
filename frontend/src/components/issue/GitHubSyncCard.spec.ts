import { describe, it, expect, vi, beforeEach } from 'vitest'
import GitHubSyncCard from '@/components/issue/GitHubSyncCard.vue'
import { mountComponent } from '@/test/mount'
import * as githubSyncApi from '@/api/githubSyncApi'
import type { GitHubSync, Issue } from '@/types'

vi.mock('@/api/githubSyncApi', () => ({
  resyncIssue: vi.fn(),
  resolveConflict: vi.fn(),
}))

const synced: GitHubSync = {
  issue_number: 401,
  github_url: 'https://github.com/demo/repo/issues/401',
  sync_status: 'SYNCED',
  last_synced_at: '2026-09-16T02:24:48Z',
}

const conflicted: GitHubSync = {
  issue_number: 402,
  github_url: 'https://github.com/demo/repo/issues/402',
  sync_status: 'CONFLICT',
  last_synced_at: '2026-09-16T02:24:48Z',
  conflict: {
    fields: ['title'],
    local: { title: 'Local title' },
    remote: { title: 'Remote title' },
    detected_at: '2026-09-17T10:00:00Z',
  },
}

const updatedIssue = { id: 'ISS-1', title: 'Remote title' } as unknown as Issue

function mountCard(github: GitHubSync) {
  return mountComponent(GitHubSyncCard, {
    props: { issueId: 'ISS-1', github },
  }).wrapper
}

describe('GitHubSyncCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the linked issue, status and last synced timestamp', () => {
    const wrapper = mountCard(synced)

    expect(wrapper.text()).toContain('GitHub Sync')
    expect(wrapper.text()).toContain('#401')
    expect(wrapper.text()).toContain('Synced')
    expect(wrapper.text()).toContain('Last synced')
    expect(wrapper.text()).toContain(new Date('2026-09-16T02:24:48Z').toLocaleString())
  })

  it('re-syncs the issue and emits the updated issue', async () => {
    vi.mocked(githubSyncApi.resyncIssue).mockResolvedValue(updatedIssue)
    const wrapper = mountCard(synced)

    const resync = wrapper.findAll('button').find((b) => b.text().includes('Force Re-sync'))!
    await resync.trigger('click')

    expect(githubSyncApi.resyncIssue).toHaveBeenCalledWith('ISS-1')
    expect(wrapper.emitted('sync:updated')).toHaveLength(1)
    expect(wrapper.emitted('sync:updated')![0]).toEqual([updatedIssue])
  })

  it('shows an error and skips the emit when the re-sync fails', async () => {
    vi.mocked(githubSyncApi.resyncIssue).mockRejectedValue(new Error('boom'))
    const wrapper = mountCard(synced)

    const resync = wrapper.findAll('button').find((b) => b.text().includes('Force Re-sync'))!
    await resync.trigger('click')

    expect(wrapper.text()).toContain('GitHub sync action failed')
    expect(wrapper.text()).toContain('boom')
    expect(wrapper.emitted('sync:updated')).toBeUndefined()
  })

  it('renders the conflict panel with local and remote values', () => {
    const wrapper = mountCard(conflicted)

    expect(wrapper.text()).toContain('Conflict')
    expect(wrapper.text()).toContain('Double-edit conflict')
    expect(wrapper.text()).toContain('title')
    expect(wrapper.text()).toContain('Local title')
    expect(wrapper.text()).toContain('Remote title')
    expect(wrapper.text()).toContain('Keep local')
    expect(wrapper.text()).toContain('Keep remote')
    expect(wrapper.text()).toContain('Merge')
  })

  it('resolves the conflict keeping the local version', async () => {
    vi.mocked(githubSyncApi.resolveConflict).mockResolvedValue(updatedIssue)
    const wrapper = mountCard(conflicted)

    const keepLocal = wrapper.findAll('button').find((b) => b.text() === 'Keep local')!
    await keepLocal.trigger('click')

    expect(githubSyncApi.resolveConflict).toHaveBeenCalledWith('ISS-1', 'local', undefined)
    expect(wrapper.emitted('sync:updated')).toHaveLength(1)
  })

  it('applies a merge with the edited values', async () => {
    vi.mocked(githubSyncApi.resolveConflict).mockResolvedValue(updatedIssue)
    const wrapper = mountCard(conflicted)

    const merge = wrapper.findAll('button').find((b) => b.text() === 'Merge')!
    await merge.trigger('click')
    expect(wrapper.find('textarea').exists()).toBe(true)

    await wrapper.find('textarea').setValue('Merged title')
    const apply = wrapper.findAll('button').find((b) => b.text() === 'Apply merge')!
    await apply.trigger('click')

    expect(githubSyncApi.resolveConflict).toHaveBeenCalledWith('ISS-1', 'merge', {
      title: 'Merged title',
    })
    expect(wrapper.emitted('sync:updated')).toHaveLength(1)
  })
})
