import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import { createUser, fetchUsers } from '@/api/usersApi'

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

describe('usersApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('normalizes the real-mode admin profile (missing type/avatar/skills, null email)', async () => {
    mockedGet.mockResolvedValue({
      data: {
        data: [
          {
            id: 'f5dcf582-0cd2-48e6-a900-69d8bb3c5cda',
            username: 'admin',
            email: null,
            role: 'ADMIN',
            github_handle: null,
            created_at: '2026-10-07T00:56:24.737386Z',
            last_login: null,
            preferences: null,
          },
        ],
      },
    })

    const [admin] = await fetchUsers()

    expect(mockedGet).toHaveBeenCalledWith('/users')
    expect(admin.username).toBe('admin')
    expect(admin.type).toBe('human')
    expect(admin.avatar).toBe('👤')
    expect(admin.skills).toEqual([])
    expect(admin.email).toBe('')
    expect(admin.last_active).toBe('2026-10-07T00:56:24.737386Z')
    expect(admin.is_active).toBe(true)
    expect(admin.issues_assigned).toBe(0)
    expect(admin.issues_created).toBe(0)
    expect(admin.role).toBe('ADMIN')
  })

  it('keeps well-formed users untouched (idempotent for mock payloads)', async () => {
    mockedGet.mockResolvedValue({
      data: {
        data: [
          {
            id: 'u-1',
            username: 'pedro',
            email: 'pedro@example.com',
            role: 'lead-developer',
            type: 'agent',
            avatar: '🤖',
            skills: ['go'],
            issues_assigned: 3,
            issues_created: 1,
            last_active: '2026-10-01T10:00:00.000Z',
            is_active: false,
          },
        ],
      },
    })

    const [user] = await fetchUsers()

    expect(user).toEqual({
      id: 'u-1',
      username: 'pedro',
      email: 'pedro@example.com',
      role: 'lead-developer',
      type: 'agent',
      avatar: '🤖',
      model: undefined,
      skills: ['go'],
      issues_assigned: 3,
      issues_created: 1,
      last_active: '2026-10-01T10:00:00.000Z',
      specialization: undefined,
      is_active: false,
    })
  })

  it('preserves the full composed backend profile (issue #558)', async () => {
    mockedGet.mockResolvedValue({
      data: {
        data: [
          {
            id: '55aa44bb-uuid-uid',
            username: 'ana',
            email: 'ana@socialseed.com',
            role: 'VIEWER',
            type: 'human',
            avatar: '🦊',
            skills: ['python', 'vue'],
            model: null,
            specialization: null,
            is_active: false,
            github_handle: 'ana-gh',
            preferences: 'dark',
            created_at: '2026-10-01T08:00:00Z',
            last_login: '2026-10-06T09:30:00Z',
          },
        ],
      },
    })

    const [ana] = await fetchUsers()

    expect(ana.id).toBe('55aa44bb-uuid-uid')
    expect(ana.role).toBe('VIEWER')
    expect(ana.type).toBe('human')
    expect(ana.avatar).toBe('🦊')
    expect(ana.skills).toEqual(['python', 'vue'])
    expect(ana.is_active).toBe(false)
    expect(ana.last_active).toBe('2026-10-06T09:30:00Z')
  })

  it('maps a null role on agents to ai-agent (issue #558)', async () => {
    mockedGet.mockResolvedValue({
      data: {
        data: [
          {
            id: 'uid-agent',
            username: 'bot-qa',
            email: 'bot@socialseed.com',
            role: null,
            type: 'agent',
            avatar: '🤖',
            skills: ['testing'],
            model: 'gpt-4o',
            specialization: 'qa',
            is_active: true,
            created_at: '2026-10-01T08:00:00Z',
          },
        ],
      },
    })

    const [agent] = await fetchUsers()

    expect(agent.role).toBe('ai-agent')
    expect(agent.type).toBe('agent')
    expect(agent.model).toBe('gpt-4o')
    expect(agent.specialization).toBe('qa')
    expect(agent.skills).toEqual(['testing'])
  })

  it('returns an empty list when the envelope has no data', async () => {
    mockedGet.mockResolvedValue({ data: {} })
    await expect(fetchUsers()).resolves.toEqual([])
  })

  it('normalizes the created user response (issue #559)', async () => {
    mockedPost.mockResolvedValue({
      data: {
        data: {
          id: 'pg-gen-1',
          username: 'pedro',
          email: 'pedro@socialseed.com',
          role: 'DEVELOPER',
          type: 'human',
          avatar: '🧑‍💻',
          skills: ['vue'],
          model: null,
          specialization: null,
          is_active: true,
          created_at: '2026-10-07T18:00:00Z',
          last_login: null,
        },
      },
    })

    const created = await createUser({
      username: 'pedro',
      email: 'pedro@socialseed.com',
      role: 'developer',
      type: 'human',
      avatar: '🧑‍💻',
      skills: ['vue'],
    })

    expect(mockedPost).toHaveBeenCalledWith(
      '/users',
      expect.objectContaining({ username: 'pedro' }),
      { suppressErrorToast: true },
    )
    expect(created.id).toBe('pg-gen-1')
    expect(created.type).toBe('human')
    expect(created.avatar).toBe('🧑‍💻')
    expect(created.skills).toEqual(['vue'])
    expect(created.role).toBe('DEVELOPER')
    expect(created.last_active).toBe('2026-10-07T18:00:00Z')
    expect(created.email).toBe('pedro@socialseed.com')
  })

  it('propagates a 409 conflict so the view can translate it (issue #559)', async () => {
    const conflict = Object.assign(new Error('username already exists'), { status: 409 })
    mockedPost.mockRejectedValue(conflict)

    await expect(
      createUser({ username: 'admin', email: 'a@x.com', role: 'developer' }),
    ).rejects.toMatchObject({ status: 409, message: 'username already exists' })
    expect(mockedPost).toHaveBeenCalledWith('/users', expect.anything(), {
      suppressErrorToast: true,
    })
  })
})
