import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { API_KEY, isMockMode } from '@/api/client'
import * as authApi from '@/api/authApi'
import * as session from '@/api/authSession'
import type { SessionUser } from '@/api/authSession'
import i18n from '@/i18n'

function httpDetail(err: unknown): string | undefined {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  return typeof detail === 'string' ? detail : undefined
}

const DEMO_USER: SessionUser = {
  id: 'demo-admin',
  username: 'admin',
  role: 'ADMIN',
  permissions: ['admin', 'create:issue', 'delete:issue', 'read:context', 'read:impact'],
}

// Frontend action -> backend permission (issue #519).
const PERMISSION_FOR_ACTION: Record<string, string> = {
  'issue.create': 'create:issue',
  'issue.edit': 'create:issue',
  'issue.kill': 'create:issue',
  'issue.delete': 'delete:issue',
  'hitl.approve': 'admin',
  'user.manage': 'admin',
  'settings.manage': 'admin',
  'admin.reset': 'admin',
}

const ROLE_RANK: Record<string, number> = { VIEWER: 1, DEVELOPER: 2, ADMIN: 3 }

export const useAuthStore = defineStore('auth', () => {
  const storedKey = ref(localStorage.getItem('tasker_api_key') || '')
  const user = ref<SessionUser | null>(session.getUser())
  const sessionReady = ref(false)
  const busy = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(
    () => isMockMode() || !!user.value || !!storedKey.value || !!API_KEY,
  )

  const role = computed(() => user.value?.role ?? null)
  const permissions = computed(() => user.value?.permissions ?? [])

  let initPromise: Promise<void> | null = null

  function initSession(): Promise<void> {
    if (initPromise) {
      return initPromise
    }
    initPromise = (async () => {
      try {
        if (isMockMode()) {
          user.value = DEMO_USER
          return
        }
        const restored = await authApi.restoreSession(storedKey.value || API_KEY || undefined)
        if (restored) {
          user.value = restored
        } else {
          user.value = null
        }
      } catch {
        user.value = null
      } finally {
        sessionReady.value = true
      }
    })()
    return initPromise
  }

  async function login(apiKey: string): Promise<SessionUser> {
    busy.value = true
    error.value = null
    try {
      const logged = await authApi.login(apiKey)
      user.value = logged
      if (apiKey) {
        localStorage.setItem('tasker_api_key', apiKey)
        storedKey.value = apiKey
      }
      return logged
    } catch (err) {
      const detail = httpDetail(err)
      error.value =
        detail && detail.toLowerCase().includes('invalid')
          ? i18n.global.t('auth.invalidKey')
          : i18n.global.t('auth.loginFailed')
      throw err
    } finally {
      busy.value = false
    }
  }

  async function loginOAuth(provider: 'github' | 'google'): Promise<void> {
    busy.value = true
    error.value = null
    try {
      await authApi.startOAuth(provider)
    } catch (err) {
      const detail = httpDetail(err)
      error.value =
        detail && detail.startsWith('oauth_not_configured')
          ? i18n.global.t('auth.oauthNotConfigured')
          : i18n.global.t('auth.oauthError')
      busy.value = false
      throw err
    }
  }

  async function completeOAuth(code: string): Promise<SessionUser> {
    busy.value = true
    error.value = null
    try {
      const logged = await authApi.exchange(code)
      user.value = logged
      return logged
    } finally {
      busy.value = false
    }
  }

  async function logout(): Promise<void> {
    await authApi.logout()
    user.value = null
    storedKey.value = ''
    localStorage.removeItem('tasker_api_key')
    if (isMockMode()) {
      user.value = DEMO_USER
    }
    window.location.reload()
  }

  function clearSession(): void {
    session.clearSession()
    user.value = null
    storedKey.value = ''
    localStorage.removeItem('tasker_api_key')
  }

  function can(action: string): boolean {
    if (isMockMode()) {
      return true
    }
    const current = user.value
    if (!current) {
      return false
    }
    const permission = PERMISSION_FOR_ACTION[action]
    if (!permission) {
      return true
    }
    return current.role === 'ADMIN' || current.permissions.includes(permission)
  }

  function hasRole(...roles: string[]): boolean {
    if (isMockMode()) {
      return true
    }
    const current = user.value
    if (!current || roles.length === 0) {
      return false
    }
    const currentRank = ROLE_RANK[current.role] ?? 0
    return roles.some((needed) => currentRank >= (ROLE_RANK[needed] ?? 99))
  }

  function rolesAllowed(roles: string[] | undefined): boolean {
    if (!roles || roles.length === 0) {
      return true
    }
    if (isMockMode()) {
      return true
    }
    if (!user.value) {
      return false
    }
    return hasRole(...roles)
  }

  // Session expiry / failed refresh dispatched by client.ts.
  if (typeof window !== 'undefined') {
    window.addEventListener('auth:unauthorized', () => {
      if (!isMockMode()) {
        user.value = null
        session.clearSession()
      }
    })
  }

  return {
    storedKey,
    user,
    sessionReady,
    busy,
    error,
    isAuthenticated,
    role,
    permissions,
    initSession,
    login,
    loginOAuth,
    completeOAuth,
    logout,
    clearSession,
    can,
    hasRole,
    rolesAllowed,
  }
})
