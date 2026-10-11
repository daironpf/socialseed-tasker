import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import {
  fetchWorkflows,
  fetchWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
} from '@/api/workflowsApi'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedGet = client.get as unknown as ReturnType<typeof vi.fn>
const mockedPost = client.post as unknown as ReturnType<typeof vi.fn>
const mockedPut = client.put as unknown as ReturnType<typeof vi.fn>
const mockedDelete = client.delete as unknown as ReturnType<typeof vi.fn>

const WORKFLOW = {
  slug: 'commit-push',
  name: 'Prepare for Commit (User Approval Required)',
  description: 'The agent MUST NOT execute git commit or git push.',
  source: 'builtin',
  created_by: null,
  created_at: '2026-10-11T08:00:00Z',
  updated_at: null,
  content_md: '# Workflow: Prepare for Commit\n\nSteps…',
  steps: null,
}

describe('workflowsApi (issue #575)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetchWorkflows unwraps the envelope and passes the source filter', async () => {
    mockedGet.mockResolvedValue({ data: { data: [WORKFLOW] } })

    const workflows = await fetchWorkflows('builtin')

    expect(mockedGet).toHaveBeenCalledWith('/workflows', { params: { source: 'builtin' } })
    expect(workflows).toEqual([WORKFLOW])
  })

  it('fetchWorkflows omits the source param when unfiltered', async () => {
    mockedGet.mockResolvedValue({ data: { data: [] } })

    await fetchWorkflows()

    expect(mockedGet).toHaveBeenCalledWith('/workflows', { params: {} })
  })

  it('fetchWorkflow encodes the slug and returns the full definition', async () => {
    mockedGet.mockResolvedValue({ data: { data: WORKFLOW } })

    const workflow = await fetchWorkflow('commit push')

    expect(mockedGet).toHaveBeenCalledWith('/workflows/commit%20push')
    expect(workflow.content_md).toContain('# Workflow:')
  })

  it('falls back to an empty list on an empty envelope', async () => {
    mockedGet.mockResolvedValue({ data: {} })

    await expect(fetchWorkflows()).resolves.toEqual([])
  })

  it('createWorkflow posts the payload and returns the created row', async () => {
    mockedPost.mockResolvedValue({
      data: { data: { ...WORKFLOW, slug: 'my-flow', source: 'custom', created_by: 'admin' } },
    })

    const created = await createWorkflow({ slug: 'my-flow', name: 'My Flow', content_md: 'v1' })

    expect(mockedPost).toHaveBeenCalledWith('/workflows', {
      slug: 'my-flow',
      name: 'My Flow',
      content_md: 'v1',
    })
    expect(created.created_by).toBe('admin')
  })

  it('updateWorkflow PUTs only the provided fields', async () => {
    mockedPut.mockResolvedValue({ data: { data: { ...WORKFLOW, source: 'custom', name: 'Renamed' } } })

    const updated = await updateWorkflow('my-flow', { name: 'Renamed', content_md: 'v2' })

    expect(mockedPut).toHaveBeenCalledWith('/workflows/my-flow', { name: 'Renamed', content_md: 'v2' })
    expect(updated.name).toBe('Renamed')
  })

  it('deleteWorkflow issues the DELETE verb', async () => {
    mockedDelete.mockResolvedValue({ data: { data: true } })

    await deleteWorkflow('my-flow')

    expect(mockedDelete).toHaveBeenCalledWith('/workflows/my-flow')
  })

  it('propagates a 409 so the panel can show the builtin/duplicate conflict', async () => {
    const conflict = Object.assign(new Error('builtin workflow'), { status: 409 })
    mockedPut.mockRejectedValue(conflict)

    await expect(updateWorkflow('commit-push', { name: 'x' })).rejects.toMatchObject({ status: 409 })
  })

  it('propagates a 503 so the panel can show its error state', async () => {
    const unavailable = Object.assign(new Error('PostgreSQL not configured'), { status: 503 })
    mockedGet.mockRejectedValue(unavailable)

    await expect(fetchWorkflows()).rejects.toMatchObject({ status: 503 })
  })
})
