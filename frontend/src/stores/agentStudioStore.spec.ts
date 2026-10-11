import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAgentStudioStore } from '@/stores/agentStudioStore'
import * as usersApi from '@/api/usersApi'
import {
  createAgentProfileRaw,
  deleteAgentProfile,
  fetchAgentProfiles,
  fetchAgentProfilesRaw,
  updateAgentProfile,
} from '@/api/agentProfilesApi'
import { isMockMode } from '@/api/client'
import {
  loadStudioProfiles,
  saveStudioProfiles,
  wasStudioImported,
  markStudioImported,
} from '@/utils/studioAgents'
import type { BackendAgentProfile } from '@/api/agentProfilesApi'
import type { AgentProfile } from '@/types/agentStudio'

vi.mock('@/api/usersApi', () => ({
  fetchUsers: vi.fn(),
  updateUser: vi.fn(),
  createUser: vi.fn(),
  deleteUser: vi.fn(),
}))

vi.mock('@/api/agentProfilesApi', () => ({
  fetchAgentProfilesRaw: vi.fn(),
  fetchAgentProfiles: vi.fn(),
  createAgentProfileRaw: vi.fn(),
  createAgentProfile: vi.fn(),
  updateAgentProfile: vi.fn(),
  deleteAgentProfile: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  isMockMode: vi.fn(() => false),
}))

const mockedFetchRaw = vi.mocked(fetchAgentProfilesRaw)
const mockedFetchProfiles = vi.mocked(fetchAgentProfiles)
const mockedCreateRaw = vi.mocked(createAgentProfileRaw)
const mockedUpdate = vi.mocked(updateAgentProfile)
const mockedDelete = vi.mocked(deleteAgentProfile)
const mockedFetchUsers = vi.mocked(usersApi.fetchUsers)
const mockedIsMockMode = vi.mocked(isMockMode)

function makeBackendProfile(id: string, username: string): BackendAgentProfile {
  return {
    id,
    username,
    avatar: '🤖',
    model: 'gpt-4o',
    specialization: 'developer',
    system_prompt: 'You are a builder.',
    tools: ['code_search'],
    limits: { maxTokensPerRun: 4000, timeoutSeconds: 60, maxRisk: 'LOW' },
    enabled: true,
    created_at: '2026-10-01T08:00:00Z',
    last_used_at: null,
  }
}

function draftInput(name: string): Omit<AgentProfile, 'id' | 'createdAt'> {
  return {
    name,
    role: 'developer',
    avatar: '🤖',
    model: 'gpt-4o',
    systemPrompt: 'You are a builder.',
    tools: ['code_search'],
    limits: { maxTokensPerRun: 4000, timeoutSeconds: 60, maxRisk: 'LOW' },
    enabled: true,
  }
}

describe('agentStudioStore real mode (issue #573)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
    mockedIsMockMode.mockReturnValue(false)
    mockedFetchRaw.mockResolvedValue([])
    mockedFetchProfiles.mockResolvedValue([])
    mockedFetchUsers.mockResolvedValue([])
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('loadProfiles maps backend profiles to the Studio shape', async () => {
    mockedFetchRaw.mockResolvedValue([makeBackendProfile('pg-1', 'release-bot')])
    const store = useAgentStudioStore()

    await store.loadProfiles()

    expect(mockedFetchRaw).toHaveBeenCalledTimes(1)
    expect(store.profiles).toHaveLength(1)
    expect(store.profiles[0]).toMatchObject({
      id: 'pg-1',
      name: 'release-bot',
      role: 'developer',
      systemPrompt: 'You are a builder.',
      tools: ['code_search'],
      enabled: true,
      limits: { maxTokensPerRun: 4000, timeoutSeconds: 60, maxRisk: 'LOW' },
    })
  })

  it('saveProfile (create) posts the payload and keeps the PG uid', async () => {
    mockedCreateRaw.mockResolvedValue(makeBackendProfile('pg-9', 'new-bot'))
    const store = useAgentStudioStore()

    const saved = await store.saveProfile(draftInput('new-bot'))

    expect(mockedCreateRaw).toHaveBeenCalledWith({
      username: 'new-bot',
      avatar: '🤖',
      model: 'gpt-4o',
      specialization: 'developer',
      system_prompt: 'You are a builder.',
      tools: ['code_search'],
      limits: { maxTokensPerRun: 4000, timeoutSeconds: 60, maxRisk: 'LOW' },
      enabled: true,
    })
    expect(saved?.id).toBe('pg-9')
    expect(store.profiles[0].id).toBe('pg-9')
  })

  it('saveProfile (update) puts the merged profile through PUT', async () => {
    mockedFetchRaw.mockResolvedValue([makeBackendProfile('pg-1', 'release-bot')])
    mockedUpdate.mockResolvedValue({} as never)
    const store = useAgentStudioStore()
    await store.loadProfiles()

    const saved = await store.saveProfile(draftInput('renamed-bot'), 'pg-1')

    expect(mockedUpdate).toHaveBeenCalledWith('pg-1', expect.objectContaining({ username: 'renamed-bot' }))
    expect(saved?.name).toBe('renamed-bot')
    expect(store.profiles[0].name).toBe('renamed-bot')
  })

  it('toggleEnabled flips enabled through PUT', async () => {
    mockedFetchRaw.mockResolvedValue([makeBackendProfile('pg-1', 'release-bot')])
    mockedUpdate.mockResolvedValue({} as never)
    const store = useAgentStudioStore()
    await store.loadProfiles()

    await store.toggleEnabled('pg-1')

    expect(mockedUpdate).toHaveBeenCalledWith('pg-1', { enabled: false })
    expect(store.profiles[0].enabled).toBe(false)
  })

  it('removeProfile deletes through the API and drops the card', async () => {
    mockedFetchRaw.mockResolvedValue([makeBackendProfile('pg-1', 'release-bot')])
    mockedDelete.mockResolvedValue(undefined)
    const store = useAgentStudioStore()
    await store.loadProfiles()

    await store.removeProfile('pg-1')

    expect(mockedDelete).toHaveBeenCalledWith('pg-1')
    expect(store.profiles).toEqual([])
  })

  it('markUsed stamps last_used_at through PUT (backend column #573)', async () => {
    mockedFetchRaw.mockResolvedValue([makeBackendProfile('pg-1', 'release-bot')])
    mockedUpdate.mockResolvedValue({} as never)
    const store = useAgentStudioStore()
    await store.loadProfiles()

    await store.markUsed('pg-1')

    expect(mockedUpdate).toHaveBeenCalledWith('pg-1', { last_used_at: expect.any(String) })
    expect(store.profiles[0].lastUsedAt).toBeTruthy()
  })

  it('cloneProfile creates a disabled copy through POST', async () => {
    mockedFetchRaw.mockResolvedValue([makeBackendProfile('pg-1', 'release-bot')])
    mockedCreateRaw.mockResolvedValue(makeBackendProfile('pg-2', 'release-bot-copy'))
    const store = useAgentStudioStore()
    await store.loadProfiles()

    const clone = await store.cloneProfile('pg-1')

    expect(mockedCreateRaw).toHaveBeenCalledWith(expect.objectContaining({
      username: 'release-bot-copy',
      enabled: false,
    }))
    expect(clone?.id).toBe('pg-2')
    expect(store.profiles).toHaveLength(2)
  })

  it('a failed create toasts an error and keeps the library unchanged', async () => {
    mockedCreateRaw.mockRejectedValue(Object.assign(new Error('duplicate'), { status: 409 }))
    const store = useAgentStudioStore()

    const saved = await store.saveProfile(draftInput('new-bot'))

    expect(saved).toBeNull()
    expect(store.profiles).toEqual([])
  })
})

describe('agentStudioStore mock mode (issue #573)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
    mockedIsMockMode.mockReturnValue(true)
    mockedFetchUsers.mockResolvedValue([])
  })

  it('loadProfiles reads localStorage without touching the network', async () => {
    const local: AgentProfile = { ...draftInput('local-bot'), id: 'agent-studio-1', createdAt: '2026-10-01T08:00:00Z' }
    saveStudioProfiles([local])
    const store = useAgentStudioStore()

    await store.loadProfiles()

    expect(mockedFetchRaw).not.toHaveBeenCalled()
    expect(mockedCreateRaw).not.toHaveBeenCalled()
    expect(store.profiles[0].id).toBe('agent-studio-1')
  })

  it('saveProfile persists to localStorage without any API call', async () => {
    const store = useAgentStudioStore()

    const saved = await store.saveProfile(draftInput('local-bot'))

    expect(saved?.id.startsWith('agent-studio-')).toBe(true)
    expect(mockedCreateRaw).not.toHaveBeenCalled()
    expect(mockedUpdate).not.toHaveBeenCalled()
    const persisted = loadStudioProfiles()
    expect(persisted).toHaveLength(1)
    expect(persisted[0].name).toBe('local-bot')
  })

  it('toggle and remove stay local', async () => {
    const local: AgentProfile = { ...draftInput('local-bot'), id: 'agent-studio-1', createdAt: '2026-10-01T08:00:00Z' }
    saveStudioProfiles([local])
    const store = useAgentStudioStore()
    await store.loadProfiles()

    await store.toggleEnabled('agent-studio-1')
    expect(loadStudioProfiles()[0].enabled).toBe(false)
    expect(mockedUpdate).not.toHaveBeenCalled()

    await store.removeProfile('agent-studio-1')
    expect(loadStudioProfiles()).toEqual([])
    expect(mockedDelete).not.toHaveBeenCalled()
  })
})

describe('agentStudioStore one-time import (issue #573)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
    mockedIsMockMode.mockReturnValue(false)
    mockedFetchRaw.mockResolvedValue([])
    mockedFetchProfiles.mockResolvedValue([])
    mockedFetchUsers.mockResolvedValue([])
  })

  function seedLegacyProfiles() {
    const legacy: AgentProfile[] = [
      { ...draftInput('legacy-one'), id: 'agent-studio-a', createdAt: '2026-09-01T08:00:00Z' },
      { ...draftInput('legacy-two'), id: 'agent-studio-b', createdAt: '2026-09-02T08:00:00Z' },
    ]
    saveStudioProfiles(legacy)
  }

  it('imports every local profile once and marks the flag', async () => {
    seedLegacyProfiles()
    mockedCreateRaw
      .mockResolvedValueOnce(makeBackendProfile('pg-a', 'legacy-one'))
      .mockResolvedValueOnce(makeBackendProfile('pg-b', 'legacy-two'))
    const store = useAgentStudioStore()

    await store.loadProfiles()

    expect(mockedCreateRaw).toHaveBeenCalledTimes(2)
    expect(mockedCreateRaw).toHaveBeenNthCalledWith(1, expect.objectContaining({ username: 'legacy-one' }))
    expect(mockedCreateRaw).toHaveBeenNthCalledWith(2, expect.objectContaining({ username: 'legacy-two' }))
    expect(wasStudioImported()).toBe(true)
    expect(loadStudioProfiles()).toEqual([]) // legacy key cleared after import
  })

  it('does not re-import once the flag is set', async () => {
    seedLegacyProfiles()
    markStudioImported()
    const store = useAgentStudioStore()

    await store.loadProfiles()

    expect(mockedCreateRaw).not.toHaveBeenCalled()
  })

  it('a failed profile does not block the rest of the import', async () => {
    seedLegacyProfiles()
    mockedCreateRaw
      .mockRejectedValueOnce(Object.assign(new Error('duplicate'), { status: 409 }))
      .mockResolvedValueOnce(makeBackendProfile('pg-b', 'legacy-two'))
    const store = useAgentStudioStore()

    await store.loadProfiles()

    expect(mockedCreateRaw).toHaveBeenCalledTimes(2)
    expect(wasStudioImported()).toBe(true)
  })
})
