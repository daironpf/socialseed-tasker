import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import {
  createAgentProfile,
  deleteAgentProfile,
  fetchAgentProfiles,
  normalizeAgentProfile,
  updateAgentProfile,
} from '@/api/agentProfilesApi'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedGet = client.get as unknown as ReturnType<typeof vi.fn>
const mockedPost = client.post as unknown as ReturnType<typeof vi.fn>
const mockedPut = client.put as unknown as ReturnType<typeof vi.fn>
const mockedDelete = client.delete as unknown as ReturnType<typeof vi.fn>

const PROFILE = {
  id: 'f8e6e797-uuid-uid',
  username: 'bot-qa',
  email: 'bot@socialseed.com',
  role: null,
  type: 'agent',
  avatar: '🤖',
  model: 'gpt-4o',
  specialization: 'qa',
  temperature: 0.2,
  system_prompt: 'You are a QA bot.',
  tools: ['fs_read', 'test_runner'],
  write_access: ['issues'],
  limits: { max_tokens: 4000 },
  enabled: false,
  skills: ['testing'],
  created_at: '2026-10-08T10:00:00Z',
  last_used_at: '2026-10-08T12:00:00Z',
}

describe('agentProfilesApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('unwraps the APIResponse envelope into normalized User cards (issue #565)', async () => {
    mockedGet.mockResolvedValue({ data: { data: [PROFILE] } })

    const [agent] = await fetchAgentProfiles()

    expect(mockedGet).toHaveBeenCalledWith('/agents/profiles', { suppressErrorToast: true })
    expect(agent.id).toBe('f8e6e797-uuid-uid')
    expect(agent.type).toBe('agent')
    expect(agent.role).toBe('ai-agent') // null role from PG, derived (#564/#565)
    expect(agent.username).toBe('bot-qa')
    expect(agent.avatar).toBe('🤖')
    expect(agent.model).toBe('gpt-4o')
    expect(agent.specialization).toBe('qa')
    expect(agent.skills).toEqual(['testing'])
    expect(agent.is_active).toBe(false) // enabled -> is_active
    expect(agent.last_active).toBe('2026-10-08T12:00:00Z')
    expect(agent.issues_assigned).toBe(0)
  })

  it('falls back to defaults on a partial payload (empty envelope, no enabled)', async () => {
    mockedGet.mockResolvedValue({ data: {} })
    await expect(fetchAgentProfiles()).resolves.toEqual([])

    const agent = normalizeAgentProfile({ id: 'uid-1', username: 'bot' })
    expect(agent.role).toBe('ai-agent')
    expect(agent.avatar).toBe('🤖')
    expect(agent.is_active).toBe(true)
    expect(agent.skills).toEqual([])
    expect(agent.last_active).toBe(new Date(0).toISOString())
  })

  it('propagates a 503 so the store can degrade to humans-only (issue #565)', async () => {
    const unavailable = Object.assign(new Error('PostgreSQL not configured'), { status: 503 })
    mockedGet.mockRejectedValue(unavailable)

    await expect(fetchAgentProfiles()).rejects.toMatchObject({ status: 503 })
  })

  it('propagates a 404 from GET /agents/profiles/{id}', async () => {
    const notFound = Object.assign(new Error('Agent profile not found'), { status: 404 })
    mockedGet.mockRejectedValue(notFound)

    await expect(fetchAgentProfiles()).rejects.toMatchObject({ status: 404 })
  })

  it('creates a profile and normalizes the 201 body', async () => {
    mockedPost.mockResolvedValue({ data: { data: PROFILE } })

    const created = await createAgentProfile({ username: 'bot-qa', model: 'gpt-4o' })

    expect(mockedPost).toHaveBeenCalledWith(
      '/agents/profiles',
      { username: 'bot-qa', model: 'gpt-4o' },
      { suppressErrorToast: true },
    )
    expect(created.id).toBe('f8e6e797-uuid-uid')
    expect(created.type).toBe('agent')
  })

  it('updates a profile against /agents/profiles/{id}', async () => {
    mockedPut.mockResolvedValue({
      data: { data: { ...PROFILE, model: 'claude-3', enabled: true } },
    })

    const updated = await updateAgentProfile(PROFILE.id, { model: 'claude-3', enabled: true })

    expect(mockedPut).toHaveBeenCalledWith(
      `/agents/profiles/${PROFILE.id}`,
      { model: 'claude-3', enabled: true },
      { suppressErrorToast: true },
    )
    expect(updated.model).toBe('claude-3')
    expect(updated.is_active).toBe(true)
  })

  it('deletes a profile and returns void', async () => {
    mockedDelete.mockResolvedValue({ data: { data: true } })

    await expect(deleteAgentProfile(PROFILE.id)).resolves.toBeUndefined()
    expect(mockedDelete).toHaveBeenCalledWith(`/agents/profiles/${PROFILE.id}`, {
      suppressErrorToast: true,
    })
  })
})
