import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import AgentRunHistoryPanel from '@/components/agents/AgentRunHistoryPanel.vue'
import { fetchAgentRuns, fetchRunLogs } from '@/api/agentRunsApi'
import type { AgentRun } from '@/api/agentRunsApi'

vi.mock('@/api/agentRunsApi', () => ({
  fetchAgentRuns: vi.fn(),
  fetchRunLogs: vi.fn(),
}))

const COMPLETED_RUN: AgentRun = {
  id: 'run-1',
  agent_id: 'builder-1',
  issue_id: 'ISSUE-1',
  status: 'completed',
  model: 'gpt-4o',
  started_at: '2026-10-11T08:00:00Z',
  finished_at: '2026-10-11T08:05:00Z',
  total_tokens: 1200,
  duration_ms: 300000,
  summary: 'done',
}

const RUNNING_RUN: AgentRun = {
  id: 'run-2',
  agent_id: 'builder-1',
  issue_id: null,
  status: 'running',
  started_at: '2026-10-11T09:00:00Z',
}

describe('AgentRunHistoryPanel (issue #574)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists the runs of the agent with status, duration and tokens', async () => {
    vi.mocked(fetchAgentRuns).mockResolvedValue([COMPLETED_RUN, RUNNING_RUN])

    const { wrapper } = mountComponent(AgentRunHistoryPanel, { props: { agentId: 'builder-1' } })
    await flushPromises()

    expect(fetchAgentRuns).toHaveBeenCalledWith('builder-1')
    expect(wrapper.text()).toContain('COMPLETED')
    expect(wrapper.text()).toContain('RUNNING')
    expect(wrapper.text()).toContain('300000 ms')
    expect(wrapper.text()).toContain('1200 tokens')
    expect(wrapper.text()).toContain('ISSUE-1')
  })

  it('expands a run and renders its persisted log entries', async () => {
    vi.mocked(fetchAgentRuns).mockResolvedValue([COMPLETED_RUN])
    vi.mocked(fetchRunLogs).mockResolvedValue([
      {
        run_id: 'run-1',
        seq: 1,
        type: 'reasoning',
        content_markdown: 'thinking…',
      },
      {
        run_id: 'run-1',
        seq: 2,
        type: 'progress',
        content_markdown: 'writing code',
      },
    ])

    const { wrapper } = mountComponent(AgentRunHistoryPanel, { props: { agentId: 'builder-1' } })
    await flushPromises()

    await wrapper.find('ul li button').trigger('click')
    await flushPromises()

    expect(fetchRunLogs).toHaveBeenCalledWith('run-1')
    expect(wrapper.text()).toContain('thinking…')
    expect(wrapper.text()).toContain('writing code')

    // collapse hides the entries again
    await wrapper.find('ul li button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).not.toContain('thinking…')
  })

  it('shows the empty state when the agent has no runs', async () => {
    vi.mocked(fetchAgentRuns).mockResolvedValue([])

    const { wrapper } = mountComponent(AgentRunHistoryPanel, { props: { agentId: 'builder-1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('No runs recorded yet.')
  })

  it('shows the error state and retries on demand', async () => {
    vi.mocked(fetchAgentRuns).mockRejectedValueOnce(new Error('boom'))
    vi.mocked(fetchAgentRuns).mockResolvedValueOnce([RUNNING_RUN])

    const { wrapper } = mountComponent(AgentRunHistoryPanel, { props: { agentId: 'builder-1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('Could not load the run history.')

    const retry = wrapper.findAll('button').find(b => b.text() === 'Retry')
    await retry!.trigger('click')
    await flushPromises()

    expect(fetchAgentRuns).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('RUNNING')
  })

  it('asks for an agent and skips the fetch when none is selected', async () => {
    const { wrapper } = mountComponent(AgentRunHistoryPanel, { props: { agentId: '' } })
    await flushPromises()

    expect(wrapper.text()).toContain('Select an agent to view its run history.')
    expect(fetchAgentRuns).not.toHaveBeenCalled()
  })

  it('shows the log error state when GET /runs/{id}/logs fails', async () => {
    vi.mocked(fetchAgentRuns).mockResolvedValue([COMPLETED_RUN])
    vi.mocked(fetchRunLogs).mockRejectedValue(new Error('boom'))

    const { wrapper } = mountComponent(AgentRunHistoryPanel, { props: { agentId: 'builder-1' } })
    await flushPromises()

    await wrapper.find('ul li button').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Could not load the run logs.')
  })
})
