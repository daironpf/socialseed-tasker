import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import IssueCard from '@/components/board/IssueCard.vue'
import { mountComponent } from '@/test/mount'
import { useUiStore } from '@/stores/uiStore'
import { IssueStatus, IssuePriority, type Issue } from '@/types'
import * as api from '@/api/issuesApi'

vi.mock('@/api/issuesApi', () => ({
  fetchIssues: vi.fn(),
  fetchIssue: vi.fn(),
  createIssue: vi.fn(),
  updateIssue: vi.fn(),
  startAgent: vi.fn(),
  stopAgent: vi.fn(),
  deleteIssue: vi.fn(),
  closeIssue: vi.fn(),
  fetchBlockedIssues: vi.fn(),
}))

function makeIssue(overrides: Partial<Issue> = {}): Issue {
  return {
    id: 'ISS-1',
    title: 'Implement the login form',
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

describe('IssueCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders the issue title', () => {
    const { wrapper } = mountComponent(IssueCard, { props: { issue: makeIssue() } })

    expect(wrapper.find('h4').text()).toBe('Implement the login form')
  })

  it('emits select with the issue on click', async () => {
    const issue = makeIssue()
    const { wrapper } = mountComponent(IssueCard, { props: { issue } })

    await wrapper.trigger('click')

    const emitted = wrapper.emitted('select')
    expect(emitted).toHaveLength(1)
    expect(emitted?.[0]).toEqual([issue])
  })

  it('applies the critical priority accent border', () => {
    const { wrapper } = mountComponent(IssueCard, {
      props: { issue: makeIssue({ priority: IssuePriority.CRITICAL }) },
    })

    expect(wrapper.classes()).toContain('border-l-red-500')
  })

  it('applies the high priority accent border', () => {
    const { wrapper } = mountComponent(IssueCard, {
      props: { issue: makeIssue({ priority: IssuePriority.HIGH }) },
    })

    expect(wrapper.classes()).toContain('border-l-orange-400')
  })

  it('renders only the first three labels plus an overflow counter', () => {
    const { wrapper } = mountComponent(IssueCard, {
      props: { issue: makeIssue({ labels: ['alpha', 'beta', 'gamma', 'delta'] }) },
    })

    expect(wrapper.text()).toContain('alpha')
    expect(wrapper.text()).toContain('gamma')
    expect(wrapper.text()).not.toContain('delta')
    expect(wrapper.text()).toContain('+1')
  })

  it('shows the dependency count when present', () => {
    const { wrapper } = mountComponent(IssueCard, {
      props: { issue: makeIssue({ dependencies: ['ISS-2', 'ISS-3'] }) },
    })

    expect(wrapper.text()).toContain('2')
  })

  it('hides the kill switch when the agent is not working', () => {
    const { wrapper } = mountComponent(IssueCard, { props: { issue: makeIssue() } })

    expect(wrapper.find('button[title="Stop Agent"]').exists()).toBe(false)
  })

  it('stops the agent from the kill switch via the dedicated endpoint', async () => {
    vi.useFakeTimers()
    const { wrapper, pinia } = mountComponent(IssueCard, {
      props: { issue: makeIssue({ agent_working: true, agent_working_started_at: '2026-09-26T10:00:00Z' }) },
      global: { stubs: { AgentWorkingIcon: true } },
    })

    const killButton = wrapper.find('button[title="Stop Agent"]')
    expect(killButton.exists()).toBe(true)

    await killButton.trigger('click')

    expect(api.stopAgent).toHaveBeenCalledWith('ISS-1', undefined)
    expect(api.updateIssue).not.toHaveBeenCalled()
    expect(useUiStore(pinia).connectionState).toBe('OFFLINE_QUEUED')

    vi.runAllTimers()
  })
})
