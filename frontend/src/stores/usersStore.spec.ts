import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUsersStore } from '@/stores/usersStore'
import * as usersApi from '@/api/usersApi'
import { fetchAgentProfiles } from '@/api/agentProfilesApi'
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
}))

vi.mock('@/api/client', () => ({
  isMockMode: vi.fn(() => false),
}))

const LS_KEY = 'agent-studio-v1'
const mockedFetchUsers = vi.mocked(usersApi.fetchUsers)
const mockedFetchProfiles = vi.mocked(fetchAgentProfiles)
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
