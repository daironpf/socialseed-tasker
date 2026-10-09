import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUsersStore } from '@/stores/usersStore'
import * as usersApi from '@/api/usersApi'
import {
  createAgentProfile,
  deleteAgentProfile,
  fetchAgentProfiles,
  updateAgentProfile,
} from '@/api/agentProfilesApi'
import { isMockMode } from '@/api/client'
import { loadStudioProfiles, saveStudioProfiles } from '@/utils/studioAgents'
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
  updateAgentProfile: vi.fn(),
  deleteAgentProfile: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  isMockMode: vi.fn(() => false),
}))

const LS_KEY = 'agent-studio-v1'
const mockedFetchUsers = vi.mocked(usersApi.fetchUsers)
const mockedFetchProfiles = vi.mocked(fetchAgentProfiles)
const mockedCreateProfile = vi.mocked(createAgentProfile)
const mockedUpdateProfile = vi.mocked(updateAgentProfile)
const mockedDeleteProfile = vi.mocked(deleteAgentProfile)
const mockedUpdateUser = vi.mocked(usersApi.updateUser)
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

describe('usersStore.editUser (issue #567)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.removeItem(LS_KEY)
    mockedIsMockMode.mockReturnValue(false)
    mockedFetchUsers.mockResolvedValue([])
    mockedFetchProfiles.mockResolvedValue([])
  })

  afterEach(() => {
    localStorage.removeItem(LS_KEY)
  })

  it('routes an endpoint agent to PUT /agents/profiles/{id} with the contract payload only', async () => {
    const card = makeProfile('pg-agent-1', 'bot-qa')
    const store = useUsersStore()
    store.users.push(card)
    const resolved = { ...card, model: 'claude-3', system_prompt: 'New prompt' }
    mockedUpdateProfile.mockResolvedValue(resolved)

    const modalPayload = {
      ...card,
      model: 'claude-3',
      system_prompt: 'New prompt',
      temperature: 0.3,
      tools: ['fs_read'],
      write_access: ['issues'],
      skills: ['testing', 'pytest'],
    }
    const updated = await store.editUser(modalPayload)

    expect(mockedUpdateProfile).toHaveBeenCalledTimes(1)
    expect(mockedUpdateProfile).toHaveBeenCalledWith('pg-agent-1', {
      username: 'bot-qa',
      email: 'bot-qa@socialseed.com',
      avatar: '🤖',
      model: 'claude-3',
      specialization: 'qa',
      temperature: 0.3,
      system_prompt: 'New prompt',
      tools: ['fs_read'],
      write_access: ['issues'],
      skills: ['testing', 'pytest'],
    })
    expect(usersApi.updateUser).not.toHaveBeenCalled()
    expect(updated.model).toBe('claude-3')
    expect(updated.type).toBe('agent')
    expect(store.users[0]).toEqual(updated) // normalized response replaces the card (#556)
    expect(store.error).toBeNull()
  })

  it('persists an agent-studio-* edit in localStorage without touching any API (even in mock)', async () => {
    mockedIsMockMode.mockReturnValue(true)
    saveStudioProfiles([makeStudioProfile('agent-studio-1')])
    const store = useUsersStore()
    store.users.push({ ...makeProfile('agent-studio-1', 'agent-studio-1'), role: 'developer' })

    const updated = await store.editUser({
      id: 'agent-studio-1',
      type: 'agent',
      username: 'renamed-bot',
      avatar: '🎭',
      model: 'llama-3',
      system_prompt: 'New prompt',
      skills: ['fs_read'],
      tools: [],
    })

    expect(mockedUpdateProfile).not.toHaveBeenCalled()
    expect(usersApi.updateUser).not.toHaveBeenCalled()
    const [saved] = loadStudioProfiles()
    expect(saved).toMatchObject({
      id: 'agent-studio-1',
      name: 'renamed-bot',
      avatar: '🎭',
      model: 'llama-3',
      systemPrompt: 'New prompt',
      tools: ['fs_read'],
    })
    expect(updated.username).toBe('renamed-bot')
    expect(updated.system_prompt).toBe('New prompt')
    expect(store.users[0]).toEqual(updated)
  })

  it('keeps humans on updateUser (/users/{id}) — no-regression of #560', async () => {
    const human = makeHuman('u-1', 'ana')
    const store = useUsersStore()
    store.users.push(human)
    mockedUpdateUser.mockResolvedValue({ ...human, username: 'ana-g' })

    await store.editUser({ ...human, username: 'ana-g' })

    expect(mockedUpdateUser).toHaveBeenCalledTimes(1)
    expect(mockedUpdateUser).toHaveBeenCalledWith('u-1', expect.objectContaining({ username: 'ana-g' }))
    expect(mockedUpdateProfile).not.toHaveBeenCalled()
    expect(store.users[0].username).toBe('ana-g')
  })

  it('in mock mode updates agents through the mock collection (owns its entities, #566)', async () => {
    mockedIsMockMode.mockReturnValue(true)
    const card = { ...makeProfile('agent-9', 'mock-bot') }
    const store = useUsersStore()
    store.users.push(card)
    mockedUpdateUser.mockResolvedValue({ ...card, model: 'gpt-4-turbo' })

    await store.editUser({ ...card, model: 'gpt-4-turbo' })

    expect(mockedUpdateUser).toHaveBeenCalledTimes(1)
    expect(mockedUpdateProfile).not.toHaveBeenCalled()
    expect(store.users[0].model).toBe('gpt-4-turbo')
  })

  it('propagates a 404 without mutating the card and refetches the list', async () => {
    const card = makeProfile('pg-agent-1', 'bot-qa')
    const store = useUsersStore()
    store.users.push(card)
    mockedUpdateProfile.mockRejectedValue(
      Object.assign(new Error('Agent profile not found'), { status: 404 }),
    )
    // Pending fetch: the refetch must be triggered but must not blank the
    // list before the assertions run.
    mockedFetchUsers.mockReturnValue(new Promise<User[]>(() => {}))
    mockedFetchProfiles.mockReturnValue(new Promise<User[]>(() => {}))

    await expect(store.editUser({ ...card, model: 'claude-3' })).rejects.toMatchObject({
      status: 404,
      message: 'Agent profile not found',
    })

    expect(store.users[0].model).toBe('gpt-4o') // card untouched
    expect(store.error).toBe('Agent profile not found')
    expect(mockedFetchUsers).toHaveBeenCalled() // stale card triggers a refetch
  })
})

describe('usersStore.deleteAgent (issue #568)', () => {
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

  it('deletes a PG agent through DELETE /agents/profiles/{id} and removes the card', async () => {
    const store = useUsersStore()
    store.users.push(makeProfile('pg-agent-1', 'bot-qa'))
    mockedDeleteProfile.mockResolvedValue(undefined)

    await store.deleteAgent(makeProfile('pg-agent-1', 'bot-qa'))

    expect(mockedDeleteProfile).toHaveBeenCalledTimes(1)
    expect(mockedDeleteProfile).toHaveBeenCalledWith('pg-agent-1')
    expect(usersApi.deleteUser).not.toHaveBeenCalled()
    expect(store.users).toHaveLength(0)
    expect(store.error).toBeNull()
  })

  it('removes agent-studio-* from localStorage without any network call (even in mock)', async () => {
    mockedIsMockMode.mockReturnValue(true)
    saveStudioProfiles([makeStudioProfile('agent-studio-1')])
    const store = useUsersStore()
    store.users.push(makeProfile('agent-studio-1', 'agent-studio-1'))

    await store.deleteAgent(makeProfile('agent-studio-1', 'agent-studio-1'))

    expect(mockedDeleteProfile).not.toHaveBeenCalled()
    expect(usersApi.deleteUser).not.toHaveBeenCalled()
    expect(loadStudioProfiles()).toHaveLength(0)
    expect(store.users).toHaveLength(0)
    expect(store.error).toBeNull()
  })

  it('in mock mode deletes agents through the mock collection (owns its entities, #566)', async () => {
    mockedIsMockMode.mockReturnValue(true)
    const store = useUsersStore()
    store.users.push(makeProfile('mock-bot-1', 'mock-bot'))
    vi.mocked(usersApi.deleteUser).mockResolvedValue(undefined)

    await store.deleteAgent(makeProfile('mock-bot-1', 'mock-bot'))

    expect(usersApi.deleteUser).toHaveBeenCalledTimes(1)
    expect(usersApi.deleteUser).toHaveBeenCalledWith('mock-bot-1')
    expect(mockedDeleteProfile).not.toHaveBeenCalled()
    expect(store.users).toHaveLength(0)
  })

  it('propagates a 404 without removing the card and refetches the list', async () => {
    const card = makeProfile('pg-agent-1', 'bot-qa')
    const store = useUsersStore()
    store.users.push(card)
    mockedDeleteProfile.mockRejectedValue(
      Object.assign(new Error('Agent profile not found'), { status: 404 }),
    )
    mockedFetchUsers.mockReturnValue(new Promise<User[]>(() => {}))
    mockedFetchProfiles.mockReturnValue(new Promise<User[]>(() => {}))

    await expect(store.deleteAgent(card)).rejects.toMatchObject({
      status: 404,
      message: 'Agent profile not found',
    })

    expect(store.users).toHaveLength(1) // card untouched
    expect(store.error).toBe('Agent profile not found')
    expect(mockedFetchUsers).toHaveBeenCalled() // stale card triggers a refetch
  })

  it('keeps humans on deleteUser with the 409 guard — no-regression of #562/#556', async () => {
    const human = makeHuman('u-1', 'ana')
    const store = useUsersStore()
    store.users.push(human)
    vi.mocked(usersApi.deleteUser).mockRejectedValue(
      Object.assign(new Error('Cannot delete the last human'), { status: 409 }),
    )

    await expect(store.deleteUser('u-1')).rejects.toMatchObject({ status: 409 })

    expect(usersApi.deleteUser).toHaveBeenCalledTimes(1)
    expect(mockedDeleteProfile).not.toHaveBeenCalled()
    expect(store.users).toHaveLength(1) // guard kept the card
    expect(store.error).toBe('Cannot delete the last human')
  })
})
