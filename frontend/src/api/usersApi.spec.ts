import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import { fetchUsers } from '@/api/usersApi'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedGet = client.get as unknown as ReturnType<typeof vi.fn>

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

  it('returns an empty list when the envelope has no data', async () => {
    mockedGet.mockResolvedValue({ data: {} })
    await expect(fetchUsers()).resolves.toEqual([])
  })
})
