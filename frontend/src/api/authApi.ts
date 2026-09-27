// HTTP client for /auth endpoints (issue #519). Uses its own axios instance
// (no X-API-Key, no mock routing) and registers the session refresh handler.

import axios, { AxiosInstance } from 'axios'
import * as session from './authSession'
import type { SessionUser, TokenPair } from './authSession'

const env = import.meta.env as unknown as Record<string, string | undefined>
const API_URL =
  (window as unknown as { __API_URL__?: string }).__API_URL__ || env.VITE_API_URL || '/api/v1'

export type OAuthProvider = 'github' | 'google'

const authClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

interface AuthResponse extends TokenPair {
  user: SessionUser
}

let inflightRefresh: Promise<boolean> | null = null

function bearerHeaders(): Record<string, string> {
  const token = session.getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function post<T>(path: string, body?: unknown, withAuth = false): Promise<T> {
  const res = await authClient.post(path, body, { headers: withAuth ? bearerHeaders() : {} })
  return res.data as T
}

export async function login(apiKey: string): Promise<SessionUser> {
  const data = await post<AuthResponse>('/auth/login', { api_key: apiKey })
  session.applyTokens(data, data.user)
  return data.user
}

export async function exchange(code: string): Promise<SessionUser> {
  const data = await post<AuthResponse>('/auth/exchange', { code })
  session.applyTokens(data, data.user)
  return data.user
}

export async function fetchMe(): Promise<SessionUser> {
  const res = await authClient.get('/auth/me', { headers: bearerHeaders() })
  session.setUser(res.data as SessionUser)
  return res.data as SessionUser
}

export function refresh(): Promise<boolean> {
  if (inflightRefresh) {
    return inflightRefresh
  }
  const refreshToken = session.getStoredRefreshToken()
  if (!refreshToken) {
    return Promise.resolve(false)
  }
  inflightRefresh = (async () => {
    try {
      const data = await post<AuthResponse>('/auth/refresh', { refresh_token: refreshToken })
      session.applyTokens(data, data.user)
      return true
    } catch {
      session.clearSession()
      return false
    } finally {
      inflightRefresh = null
    }
  })()
  return inflightRefresh
}

/** Silent session restore on app boot: refresh token first, then legacy API key. */
export async function restoreSession(legacyApiKey?: string): Promise<SessionUser | null> {
  if (session.getStoredRefreshToken()) {
    const ok = await refresh()
    if (!ok) {
      return null
    }
    try {
      return await fetchMe()
    } catch {
      return session.getUser()
    }
  }
  if (legacyApiKey) {
    try {
      return await login(legacyApiKey)
    } catch {
      session.clearSession()
      return null
    }
  }
  return null
}

export async function logout(): Promise<void> {
  const refreshToken = session.getStoredRefreshToken()
  try {
    if (refreshToken) {
      await post('/auth/logout', { refresh_token: refreshToken })
    }
  } catch {
    // Best effort: always clear the local session.
  }
  session.clearSession()
}

export async function startOAuth(provider: OAuthProvider): Promise<void> {
  const res = await authClient.get(`/auth/oauth/${provider}/authorize`)
  const url = (res.data as { authorize_url: string }).authorize_url
  window.location.assign(url)
}

session.registerRefreshHandler(refresh)
