import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { setActivePinia, type Pinia } from 'pinia'
import { mountComponent } from '@/test/mount'
import ListView from '@/views/ListView.vue'
import { useUiStore } from '@/stores/uiStore'
import {
  useKeyboardShortcuts,
  initKeyboardShortcuts,
  destroyKeyboardShortcuts,
} from '@/composables/useKeyboardShortcuts'
import * as issuesApi from '@/api/issuesApi'
import * as componentsApi from '@/api/componentsApi'
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

vi.mock('@/api/componentsApi', () => ({
  fetchComponents: vi.fn(),
  fetchComponent: vi.fn(),
  createComponent: vi.fn(),
  updateComponent: vi.fn(),
  deleteComponent: vi.fn(),
}))

function makeIssue(id: string, title: string): Issue {
  return {
    id,
    title,
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
  }
}

function press(key: string) {
  document.dispatchEvent(new KeyboardEvent('keydown', { key, cancelable: true, bubbles: true }))
}

describe('ListView keyboard navigation', () => {
  const kb = useKeyboardShortcuts()
  let pinia: Pinia

  beforeEach(() => {
    destroyKeyboardShortcuts()
    kb.unregisterAll()
    initKeyboardShortcuts()
    vi.mocked(issuesApi.fetchIssues).mockResolvedValue({
      items: [makeIssue('ISS-1', 'First issue'), makeIssue('ISS-2', 'Second issue')],
      pagination: { page: 1, limit: 100, total: 2, has_next: false, has_prev: false },
    })
    vi.mocked(componentsApi.fetchComponents).mockResolvedValue([])
  })

  afterEach(() => {
    destroyKeyboardShortcuts()
    kb.unregisterAll()
    document.body.innerHTML = ''
  })

  async function mountList() {
    const mounted = mountComponent(ListView)
    pinia = mounted.pinia
    setActivePinia(pinia)
    await flushPromises()
    await mounted.wrapper.vm.$nextTick()
    return mounted.wrapper
  }

  it('moves the active row with J/K and exposes it via aria-activedescendant', async () => {
    const wrapper = await mountList()

    press('j')
    await wrapper.vm.$nextTick()
    const table = wrapper.find('table')
    expect(table.attributes('aria-activedescendant')).toBe('issue-row-0')
    expect(table.attributes('role')).toBe('grid')
    expect(wrapper.find('#issue-row-0').classes()).toContain('outline')
    expect(wrapper.find('#issue-row-0').attributes('aria-selected')).toBe('true')
    expect(wrapper.find('#issue-row-1').attributes('aria-selected')).toBe('false')

    press('j')
    await wrapper.vm.$nextTick()
    expect(table.attributes('aria-activedescendant')).toBe('issue-row-1')

    press('k')
    await wrapper.vm.$nextTick()
    expect(table.attributes('aria-activedescendant')).toBe('issue-row-0')
  })

  it('opens the active issue with Enter and closes it with Escape', async () => {
    const wrapper = await mountList()
    const ui = useUiStore()

    press('j')
    await wrapper.vm.$nextTick()

    press('Enter')
    expect(ui.selectedIssueId).toBe('ISS-1')
    ui.setSelectedIssue(null)

    press('k')
    press('Escape')
    expect(ui.selectedIssueId).toBeNull()
  })

  it('is a no-op when the list is empty', async () => {
    vi.mocked(issuesApi.fetchIssues).mockResolvedValue({
      items: [],
      pagination: { page: 1, limit: 100, total: 0, has_next: false, has_prev: false },
    })
    const wrapper = await mountList()

    press('j')
    press('Enter')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('table').attributes('aria-activedescendant')).toBeUndefined()
    expect(useUiStore().selectedIssueId).toBeNull()
  })
})
