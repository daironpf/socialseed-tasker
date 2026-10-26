import { beforeEach, describe, expect, it, vi } from 'vitest'

const { get } = vi.hoisted(() => ({
  get: vi.fn(),
}))

vi.mock('axios', () => ({
  default: {
    create: () => ({ get, post: vi.fn() }),
  },
}))

import { fetchMe } from './authApi'
import * as session from './authSession'

const USER: session.SessionUser = {
  id: 'u-admin',
  username: 'admin',
  role: 'ADMIN',
  permissions: ['admin'],
}

describe('authApi.fetchMe', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    session.clearSession()
    session.applyTokens({ access_token: 'access-token' })
  })

  it('unwraps the API envelope and stores the session user', async () => {
    get.mockResolvedValue({
      data: {
        data: USER,
        error: null,
        meta: { timestamp: '2026-10-26T00:00:00Z', request_id: null },
      },
    })

    await expect(fetchMe()).resolves.toEqual(USER)
    expect(session.getUser()).toEqual(USER)
    expect(get).toHaveBeenCalledWith('/auth/me', {
      headers: { Authorization: 'Bearer access-token' },
    })
  })
})
