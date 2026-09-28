import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { setActivePinia, type Pinia } from 'pinia'
import { mountComponent } from '@/test/mount'
import KanbanView from '@/views/KanbanView.vue'
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

describe('KanbanView keyboard navigation', () => {
  const kb = useKeyboardShortcuts()

  beforeEach(() => {
    destroyKeyboardShortcuts()
    kb.unregisterAll()
    initKeyboardShortcuts()
    vi.mocked(issuesApi.fetchIssues).mockResolvedValue({
      items: [makeIssue('ISS-1', 'First card'), makeIssue('ISS-2', 'Second card')],
      pagination: { page: 1, limit: 100, total: 2, has_next: false, has_prev: false },
    })
    vi.mocked(componentsApi.fetchComponents).mockResolvedValue([])
  })

  afterEach(() => {
    destroyKeyboardShortcuts()
    kb.unregisterAll()
    document.body.innerHTML = ''
  })

  async function mountBoard() {
    const mounted = mountComponent(KanbanView)
    setActivePinia(mounted.pinia as Pinia)
    await flushPromises()
    await mounted.wrapper.vm.$nextTick()
    return mounted.wrapper
  }

  it('moves the active card with J/K and exposes it via aria-activedescendant', async () => {
    const wrapper = await mountBoard()

    press('j')
    await wrapper.vm.$nextTick()
    const board = wrapper.find('[role="listbox"]')
    expect(board.attributes('aria-activedescendant')).toBe('issue-card-ISS-1')
    expect(board.attributes('tabindex')).toBe('-1')

    const card = wrapper.find('#issue-card-ISS-1')
    expect(card.exists()).toBe(true)
    expect(card.attributes('role')).toBe('option')
    expect(card.attributes('aria-selected')).toBe('true')
    expect(card.classes()).toContain('outline')

    press('j')
    await wrapper.vm.$nextTick()
    expect(board.attributes('aria-activedescendant')).toBe('issue-card-ISS-2')

    press('k')
    await wrapper.vm.$nextTick()
    expect(board.attributes('aria-activedescendant')).toBe('issue-card-ISS-1')
  })

  it('opens the active card with Enter', async () => {
    const wrapper = await mountBoard()
    const ui = useUiStore()

    press('j')
    await wrapper.vm.$nextTick()

    press('Enter')
    expect(ui.selectedIssueId).toBe('ISS-1')
    ui.setSelectedIssue(null)
  })
})
