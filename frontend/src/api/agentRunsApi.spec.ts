import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import {
  fetchAgentRuns,
  fetchRunLogs,
  createAgentRun,
  appendRunLog,
  updateAgentRun,
  deleteAgentRun,
} from '@/api/agentRunsApi'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedGet = client.get as unknown as ReturnType<typeof vi.fn>
const mockedPost = client.post as unknown as ReturnType<typeof vi.fn>
const mockedPatch = client.patch as unknown as ReturnType<typeof vi.fn>
const mockedDelete = client.delete as unknown as ReturnType<typeof vi.fn>

const RUN = {
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

const LOG = {
  run_id: 'run-1',
  seq: 1,
  timestamp: '2026-10-11T08:01:00Z',
  type: 'reasoning',
  content_markdown: 'thinking…',
  metadata: { step: 1 },
}

describe('agentRunsApi (issue #574)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetchAgentRuns unwraps the envelope and encodes the agent id', async () => {
    mockedGet.mockResolvedValue({ data: { data: [RUN] } })

    const runs = await fetchAgentRuns('builder 1', 10)

    expect(mockedGet).toHaveBeenCalledWith('/agents/builder%201/runs', { params: { limit: 10 } })
    expect(runs).toEqual([RUN])
  })

  it('fetchRunLogs unwraps the envelope ordered by the backend', async () => {
    mockedGet.mockResolvedValue({ data: { data: [LOG] } })

    const logs = await fetchRunLogs('run-1')

    expect(mockedGet).toHaveBeenCalledWith('/runs/run-1/logs')
    expect(logs).toEqual([LOG])
  })

  it('falls back to empty lists on an empty envelope', async () => {
    mockedGet.mockResolvedValue({ data: {} })

    await expect(fetchAgentRuns('builder-1')).resolves.toEqual([])
    await expect(fetchRunLogs('run-1')).resolves.toEqual([])
  })

  it('createAgentRun posts the payload and returns the created run', async () => {
    mockedPost.mockResolvedValue({ data: { data: { ...RUN, status: 'running' } } })

    const run = await createAgentRun('builder-1', { issue_id: 'ISSUE-1', model: 'gpt-4o' })

    expect(mockedPost).toHaveBeenCalledWith('/agents/builder-1/runs', {
      issue_id: 'ISSUE-1',
      model: 'gpt-4o',
    })
    expect(run.status).toBe('running')
  })

  it('appendRunLog posts the typed entry', async () => {
    mockedPost.mockResolvedValue({ data: { data: LOG } })

    const entry = await appendRunLog('run-1', { type: 'progress', content_markdown: 'avanzo' })

    expect(mockedPost).toHaveBeenCalledWith('/runs/run-1/logs', { type: 'progress', content_markdown: 'avanzo' })
    expect(entry.seq).toBe(1)
  })

  it('updateAgentRun patches only the provided fields', async () => {
    mockedPatch.mockResolvedValue({ data: { data: { ...RUN, status: 'failed' } } })

    const run = await updateAgentRun('run-1', { status: 'failed', summary: 'boom' })

    expect(mockedPatch).toHaveBeenCalledWith('/runs/run-1', { status: 'failed', summary: 'boom' })
    expect(run.status).toBe('failed')
  })

  it('deleteAgentRun issues the DELETE verb', async () => {
    mockedDelete.mockResolvedValue({ data: { data: true } })

    await deleteAgentRun('run-1')

    expect(mockedDelete).toHaveBeenCalledWith('/runs/run-1')
  })

  it('propagates a 503 so the panel can show its error state', async () => {
    const unavailable = Object.assign(new Error('PostgreSQL not configured'), { status: 503 })
    mockedGet.mockRejectedValue(unavailable)

    await expect(fetchAgentRuns('builder-1')).rejects.toMatchObject({ status: 503 })
  })
})
