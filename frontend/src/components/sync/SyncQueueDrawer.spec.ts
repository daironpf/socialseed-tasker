import { describe, it, expect, vi } from 'vitest'
import { nextTick } from 'vue'
import { createQueueEntry, type QueuedMutation } from '@/utils/offlineQueue'
import SyncQueueDrawer from '@/components/sync/SyncQueueDrawer.vue'
import { mountComponent } from '@/test/mount'
import { useUiStore } from '@/stores/uiStore'

vi.mock('@/api/issuesApi', () => ({
  fetchIssues: vi.fn(),
  fetchIssue: vi.fn(),
  createIssue: vi.fn(),
  updateIssue: vi.fn(),
  deleteIssue: vi.fn(),
  closeIssue: vi.fn(),
  fetchBlockedIssues: vi.fn(),
}))

function pendingEntry(overrides: Partial<QueuedMutation> = {}): QueuedMutation {
  return {
    ...createQueueEntry({
      entity: 'issue',
      operation: 'update',
      entityId: 'ISS-1',
      payload: { title: 'Renamed remotely' },
    }),
    ...overrides,
  }
}

describe('SyncQueueDrawer', () => {
  it('shows the empty state and disables force sync when there is nothing queued', () => {
    const { wrapper, pinia } = mountComponent(SyncQueueDrawer)
    const ui = useUiStore(pinia)
    ui.syncQueue = []

    expect(wrapper.text()).toContain('Queue is empty. Everything is in sync.')
    expect(wrapper.text()).toContain('0 queued')

    const forceSync = wrapper.findAll('button').find(b => b.text().includes('Force sync'))!
    expect(forceSync.attributes('disabled')).toBeDefined()
  })

  it('emits close from the backdrop and the close button', async () => {
    const { wrapper } = mountComponent(SyncQueueDrawer)

    await wrapper.find('[role="dialog"] > div').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)

    await wrapper.find('button[aria-label="Close"]').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(2)
  })

  it('renders queued entries with entity, operation and summary', async () => {
    const { wrapper, pinia } = mountComponent(SyncQueueDrawer)
    const ui = useUiStore(pinia)
    ui.syncQueue = [pendingEntry()]
    await nextTick()

    expect(wrapper.text()).toContain('1 queued')
    expect(wrapper.text()).toContain('issue')
    expect(wrapper.text()).toContain('update')
    expect(wrapper.text()).toContain('Pending')
    expect(wrapper.text()).toContain('ISS-1')
    expect(wrapper.text()).not.toContain('Queue is empty')
  })

  it('retries a pending entry from the drawer', async () => {
    const { wrapper, pinia } = mountComponent(SyncQueueDrawer)
    const ui = useUiStore(pinia)
    ui.syncQueue = [pendingEntry()]
    await nextTick()

    const retry = wrapper.findAll('button').find(b => b.text().includes('Retry'))!
    await retry.trigger('click')

    expect(ui.syncQueue[0].retries).toBe(1)
    expect(wrapper.text()).toContain('1 retries')
  })

  it('removes a pending entry and falls back to the empty state', async () => {
    const { wrapper, pinia } = mountComponent(SyncQueueDrawer)
    const ui = useUiStore(pinia)
    ui.syncQueue = [pendingEntry()]
    await nextTick()

    const remove = wrapper.findAll('button').find(b => b.text().includes('Delete'))!
    await remove.trigger('click')

    expect(ui.syncQueue).toHaveLength(0)
    expect(wrapper.text()).toContain('Queue is empty. Everything is in sync.')
  })

  it('renders the conflict resolution actions for conflicted entries', async () => {
    const { wrapper, pinia } = mountComponent(SyncQueueDrawer)
    const ui = useUiStore(pinia)
    ui.syncQueue = [pendingEntry({ status: 'conflict', remotePayload: { title: 'Renamed remotely (remote)' } })]
    await nextTick()

    expect(wrapper.text()).toContain('Conflict')
    expect(wrapper.text()).toContain('Keep local')
    expect(wrapper.text()).toContain('Keep remote')
    expect(wrapper.text()).toContain('Merge')
    expect(wrapper.findAll('button').find(b => b.text().includes('Retry'))).toBeUndefined()
  })
})
