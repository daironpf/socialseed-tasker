import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/authStore'
import { setApiMode } from '@/api/client'
import * as authApi from '@/api/authApi'
import type { SessionUser } from '@/api/authSession'

vi.mock('@/api/authApi', () => ({
  login: vi.fn(),
  restoreSession: vi.fn(),
  logout: vi.fn(),
  exchange: vi.fn(),
  startOAuth: vi.fn(),
  refresh: vi.fn(),
  fetchMe: vi.fn(),
}))

const ADMIN_USER: SessionUser = {
  id: 'u-admin',
  username: 'admin',
  role: 'ADMIN',
  permissions: ['admin', 'create:issue', 'delete:issue', 'read:context', 'read:impact'],
}

const VIEWER_USER: SessionUser = {
  id: 'u-viewer',
  username: 'reader',
  role: 'VIEWER',
  permissions: ['read:context', 'read:impact'],
}

describe('authStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  describe('mock mode', () => {
    beforeEach(() => setApiMode('mock'))

    it('authenticates without a session and grants all permissions', async () => {
      const store = useAuthStore()
      await store.initSession()
      expect(store.isAuthenticated).toBe(true)
      expect(store.user?.role).toBe('ADMIN')
      expect(store.can('issue.kill')).toBe(true)
      expect(store.can('hitl.approve')).toBe(true)
      expect(store.hasRole('ADMIN')).toBe(true)
      expect(store.rolesAllowed(['ADMIN'])).toBe(true)
      expect(store.sessionReady).toBe(true)
    })
  })

  describe('real mode', () => {
    beforeEach(() => setApiMode('real'))

    it('restores the session returned by restoreSession on init', async () => {
      vi.mocked(authApi.restoreSession).mockResolvedValue(ADMIN_USER)
      const store = useAuthStore()
      await store.initSession()
      expect(authApi.restoreSession).toHaveBeenCalled()
      expect(store.user?.username).toBe('admin')
      expect(store.isAuthenticated).toBe(true)
      expect(store.sessionReady).toBe(true)
    })

    it('stays logged out when no credentials exist', async () => {
      vi.mocked(authApi.restoreSession).mockResolvedValue(null)
      const store = useAuthStore()
      await store.initSession()
      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.sessionReady).toBe(true)
    })

    it('passes the legacy stored API key to restoreSession', async () => {
      localStorage.setItem('tasker_api_key', 'legacy-key')
      vi.mocked(authApi.restoreSession).mockResolvedValue(null)
      const store = useAuthStore()
      await store.initSession()
      expect(authApi.restoreSession).toHaveBeenCalledWith('legacy-key')
    })

    it('login stores the user and maps permissions', async () => {
      vi.mocked(authApi.login).mockResolvedValue(ADMIN_USER)
      const store = useAuthStore()
      const logged = await store.login('admintoken123')
      expect(logged.username).toBe('admin')
      expect(store.user).toEqual(ADMIN_USER)
      expect(store.isAuthenticated).toBe(true)
      expect(store.can('issue.create')).toBe(true)
      expect(store.can('issue.delete')).toBe(true)
      expect(store.can('hitl.approve')).toBe(true)
      expect(localStorage.getItem('tasker_api_key')).toBe('admintoken123')
    })

    it('viewer sessions are blocked from privileged routes and actions', async () => {
      vi.mocked(authApi.login).mockResolvedValue(VIEWER_USER)
      const store = useAuthStore()
      await store.login('readertoken123')
      expect(store.can('issue.create')).toBe(false)
      expect(store.can('issue.kill')).toBe(false)
      expect(store.can('hitl.approve')).toBe(false)
      expect(store.hasRole('ADMIN')).toBe(false)
      expect(store.hasRole('DEVELOPER')).toBe(false)
      expect(store.hasRole('VIEWER')).toBe(true)
      expect(store.rolesAllowed(['ADMIN'])).toBe(false)
      expect(store.rolesAllowed(['ADMIN', 'DEVELOPER'])).toBe(false)
      expect(store.rolesAllowed(undefined)).toBe(true)
    })

    it('developer sessions allow issue actions but not admin routes', async () => {
      vi.mocked(authApi.login).mockResolvedValue({
        ...VIEWER_USER,
        id: 'u-dev',
        username: 'dev',
        role: 'DEVELOPER',
        permissions: ['create:issue', 'delete:issue'],
      })
      const store = useAuthStore()
      await store.login('devkey')
      expect(store.can('issue.create')).toBe(true)
      expect(store.can('issue.kill')).toBe(true)
      expect(store.can('hitl.approve')).toBe(false)
      expect(store.rolesAllowed(['ADMIN'])).toBe(false)
      expect(store.rolesAllowed(['ADMIN', 'DEVELOPER'])).toBe(true)
    })

    it('surfaces a translated error on invalid API key', async () => {
      vi.mocked(authApi.login).mockRejectedValue(
        Object.assign(new Error('Request failed'), {
          response: { status: 401, data: { detail: 'Invalid API key' } },
        }),
      )
      const store = useAuthStore()
      await expect(store.login('nope')).rejects.toThrow()
      expect(store.error).toBe('Invalid API key. Check it and try again.')
      expect(store.user).toBeNull()
    })

    it('translates the oauth_not_configured backend detail', async () => {
      vi.mocked(authApi.startOAuth).mockRejectedValue(
        Object.assign(new Error('Request failed'), {
          response: { status: 403, data: { detail: 'oauth_not_configured:github' } },
        }),
      )
      const store = useAuthStore()
      await expect(store.loginOAuth('github')).rejects.toThrow()
      expect(store.error).toBe('This sign-in method is not configured on the server.')
      expect(store.busy).toBe(false)
    })

    it('completeOAuth exchanges the code and stores the user', async () => {
      vi.mocked(authApi.exchange).mockResolvedValue(ADMIN_USER)
      const store = useAuthStore()
      const logged = await store.completeOAuth('one-time-code')
      expect(authApi.exchange).toHaveBeenCalledWith('one-time-code')
      expect(logged.username).toBe('admin')
      expect(store.user).toEqual(ADMIN_USER)
      expect(store.busy).toBe(false)
    })
  })
})
