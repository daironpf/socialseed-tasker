import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUsersStore } from '@/stores/usersStore'
import * as usersApi from '@/api/usersApi'
import { createAgentProfile, fetchAgentProfiles } from '@/api/agentProfilesApi'
import { isMockMode } from '@/api/client'
import { saveStudioProfiles } from '@/utils/studioAgents'
import type { AgentProfile } from '@/types/agentStudio'
import type { User } from '@/types'

vi.mock('@/api/usersApi', () => ({
  fetchUsers: vi.fn(),
  updateUser: vi.fn(),
  createUser: vi.fn(),
  deleteUser: vi.fn(),
}))

vi.mock('@/api/agentProfilesApi', () => ({
  fetchAgentProfiles: vi.fn(),
  createAgentProfile: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  isMockMode: vi.fn(() => false),
}))

const LS_KEY = 'agent-studio-v1'
const mockedFetchUsers = vi.mocked(usersApi.fetchUsers)
const mockedFetchProfiles = vi.mocked(fetchAgentProfiles)
const mockedCreateProfile = vi.mocked(createAgentProfile)
const mockedIsMockMode = vi.mocked(isMockMode)

function makeHuman(id: string, username: string): User {
  return {
    id,
    username,
    email: `${username}@socialseed.com`,
    role: 'VIEWER',
    type: 'human',
    avatar: '🦊',
    skills: ['python'],
    issues_assigned: 0,
    issues_created: 0,
    last_active: '2026-10-01T08:00:00Z',
    is_active: true,
  }
}

function makeProfile(id: string, username: string): User {
  return {
    id,
    username,
    email: `${username}@socialseed.com`,
    role: 'ai-agent',
    type: 'agent',
    avatar: '🤖',
    model: 'gpt-4o',
    skills: ['testing'],
    issues_assigned: 0,
    issues_created: 0,
    last_active: '2026-10-08T12:00:00Z',
    specialization: 'qa',
    is_active: true,
  }
}

function makeStudioProfile(id: string): AgentProfile {
  return {
    id,
    name: id,
    role: 'developer',
    avatar: '🎭',
    model: 'gpt-4o',
    systemPrompt: '',
    tools: [],
    limits: { maxTokensPerRun: 1000, timeoutSeconds: 30, maxRisk: 'LOW' },
    enabled: true,
    createdAt: '2026-10-04T00:00:00Z',
  }
}

describe('usersStore.fetchUsers (issue #565)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.removeItem(LS_KEY)
    mockedIsMockMode.mockReturnValue(false)
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    localStorage.removeItem(LS_KEY)
    vi.restoreAllMocks()
  })

  it('combines /users + /agents/profiles + studio locales without duplicate ids', async () => {
    mockedFetchUsers.mockResolvedValue([makeHuman('u-1', 'ana')])
    mockedFetchProfiles.mockResolvedValue([makeProfile('pg-agent-1', 'bot-qa')])
    saveStudioProfiles([makeStudioProfile('agent-studio-1')])

    const store = useUsersStore()
    await store.fetchUsers()

    expect(mockedFetchUsers).toHaveBeenCalledTimes(1)
    expect(mockedFetchProfiles).toHaveBeenCalledTimes(1)
    expect(store.users.map(u => u.id)).toEqual(['u-1', 'agent-studio-1', 'pg-agent-1'])
    expect(store.humans).toHaveLength(1)
    expect(store.agents.map(u => u.username)).toEqual(['agent-studio-1', 'bot-qa'])
  })

  it('never duplicates an id already present in the human collection', async () => {
    mockedFetchUsers.mockResolvedValue([makeHuman('pg-agent-1', 'ana')])
    mockedFetchProfiles.mockResolvedValue([makeProfile('pg-agent-1', 'bot-qa')])

    const store = useUsersStore()
    await store.fetchUsers()

    expect(store.users.filter(u => u.id === 'pg-agent-1')).toHaveLength(1)
    expect(store.users).toHaveLength(1)
  })

  it('keeps the humans when /agents/profiles fails (503 without database)', async () => {
    mockedFetchUsers.mockResolvedValue([makeHuman('u-1', 'ana'), makeHuman('u-2', 'pedro')])
    mockedFetchProfiles.mockRejectedValue(
      Object.assign(new Error('PostgreSQL not configured'), { status: 503 }),
    )

    const store = useUsersStore()
    await store.fetchUsers()

    expect(store.users.map(u => u.id)).toEqual(['u-1', 'u-2'])
    expect(store.error).toBeNull()
    expect(store.loading).toBe(false)
    expect(console.warn).toHaveBeenCalled()
  })

  it('propagates a /users failure as store error', async () => {
    mockedFetchUsers.mockRejectedValue(new Error('boom'))

    const store = useUsersStore()
    await store.fetchUsers()

    expect(store.users).toEqual([])
    expect(store.error).toBe('boom')
    expect(store.loading).toBe(false)
  })

  it('in mock mode only calls the mock collection (no /agents/profiles)', async () => {
    mockedIsMockMode.mockReturnValue(true)
    mockedFetchUsers.mockResolvedValue([
      makeHuman('u-1', 'ana'),
      { ...makeProfile('agent-studio-9', 'local-bot'), id: 'agent-studio-9' },
    ])

    const store = useUsersStore()
    await store.fetchUsers()

    expect(mockedFetchUsers).toHaveBeenCalledTimes(1)
    expect(mockedFetchProfiles).not.toHaveBeenCalled()
    expect(store.users.map(u => u.id)).toEqual(['u-1', 'agent-studio-9'])
    expect(store.error).toBeNull()
  })

  it('exposes the endpoint agents through stats computeds (#565)', async () => {
    mockedFetchUsers.mockResolvedValue([makeHuman('u-1', 'ana')])
    mockedFetchProfiles.mockResolvedValue([
      makeProfile('pg-agent-1', 'bot-qa'),
      makeProfile('pg-agent-2', 'bot-ci'),
    ])

    const store = useUsersStore()
    await store.fetchUsers()

    expect(store.users).toHaveLength(3)
    expect(store.agents).toHaveLength(2)
    expect(store.activeAgents).toHaveLength(2)
  })
})

describe('usersStore.createAgent (issue #566)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.removeItem(LS_KEY)
    mockedIsMockMode.mockReturnValue(false)
  })

  afterEach(() => {
    localStorage.removeItem(LS_KEY)
  })

  const MODAL_PAYLOAD = {
    username: 'bot-qa',
    email: 'bot@socialseed.com',
    avatar: '🤖',
    model: 'gpt-4o',
    specialization: 'testing',
    system_prompt: 'You are a QA bot.',
    skills: ['Testing', 'Pytest'],
  }

  it('posts the modal payload to /agents/profiles and pushes the normalized card', async () => {
    mockedCreateProfile.mockResolvedValue(makeProfile('pg-agent-1', 'bot-qa'))

    const store = useUsersStore()
    const created = await store.createAgent(MODAL_PAYLOAD)

    expect(mockedCreateProfile).toHaveBeenCalledWith(MODAL_PAYLOAD)
    expect(mockedCreateProfile).toHaveBeenCalledTimes(1)
    // The card is the normalized shape, never the raw backend payload (#556/#566)
    expect(created).toEqual(
      expect.objectContaining({
        id: 'pg-agent-1',
        username: 'bot-qa',
        type: 'agent',
        role: 'ai-agent',
        avatar: '🤖',
        model: 'gpt-4o',
        specialization: 'qa',
        skills: ['testing'],
        is_active: true,
      }),
    )
    expect(created).not.toHaveProperty('system_prompt')
    expect(created).not.toHaveProperty('temporary_password')
    expect(store.users).toHaveLength(1)
    expect(store.users[0]).toEqual(created) // deep-equal: Vue wraps the pushed object in a reactive proxy
    expect(store.error).toBeNull()
  })

  it('propagates a 409 duplicate username without touching the list', async () => {
    mockedCreateProfile.mockRejectedValue(
      Object.assign(new Error('username already exists'), { status: 409 }),
    )

    const store = useUsersStore()
    await expect(store.createAgent(MODAL_PAYLOAD)).rejects.toMatchObject({
      status: 409,
      message: 'username already exists',
    })
    expect(store.users).toEqual([])
    expect(store.error).toBe('username already exists')
  })

  it('in mock mode creates through the mock collection instead of the profiles API', async () => {
    mockedIsMockMode.mockReturnValue(true)
    mockedCreateProfile.mockResolvedValue(makeProfile('pg-agent-1', 'bot-qa'))
    vi.mocked(usersApi.createUser).mockResolvedValue({
      user: { ...makeProfile('agent-studio-new', 'bot-qa'), id: 'agent-studio-new' },
      temporaryPassword: null,
    })

    const store = useUsersStore()
    const created = await store.createAgent(MODAL_PAYLOAD)

    expect(mockedCreateProfile).not.toHaveBeenCalled()
    expect(usersApi.createUser).toHaveBeenCalledWith(
      expect.objectContaining({ username: 'bot-qa', type: 'agent', role: 'ai-agent' }),
    )
    expect(created.id).toBe('agent-studio-new')
    expect(store.users.map(u => u.id)).toEqual(['agent-studio-new'])
  })
})
