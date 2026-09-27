// JWT session holder for the OAuth2/API-key flow (issue #519).
// Deliberately free of axios/Pinia imports so client.ts, authApi.ts and
// authStore.ts can share it without module cycles.

export interface SessionUser {
  id: string
  username: string
  role: 'ADMIN' | 'DEVELOPER' | 'VIEWER'
  permissions: string[]
  email?: string
}

export interface TokenPair {
  access_token: string
  refresh_token?: string | null
  expires_in?: number
}

const REFRESH_KEY = 'tasker_refresh_token'
const USER_KEY = 'tasker_session_user'
const EXPIRY_SAFETY_MS = 60_000
const MIN_REFRESH_DELAY_MS = 5_000

let accessToken: string | null = null
let refreshTimer: ReturnType<typeof setTimeout> | null = null
let refreshHandler: (() => Promise<boolean>) | null = null

export function getAccessToken(): string | null {
  return accessToken
}

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function getUser(): SessionUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as SessionUser) : null
  } catch {
    return null
  }
}

export function setUser(user: SessionUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

/** Registers the single-flight refresh used by the timer and by client.ts. */
export function registerRefreshHandler(handler: () => Promise<boolean>): void {
  refreshHandler = handler
}

export function clearSession(): void {
  accessToken = null
  if (refreshTimer) {
    clearTimeout(refreshTimer)
    refreshTimer = null
  }
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
}

export function applyTokens(pair: TokenPair, user?: SessionUser): void {
  accessToken = pair.access_token
  if (pair.refresh_token) {
    localStorage.setItem(REFRESH_KEY, pair.refresh_token)
  }
  if (user) {
    setUser(user)
  }
  scheduleRefresh(pair.expires_in ?? 900)
}

function scheduleRefresh(expiresIn: number): void {
  if (refreshTimer) {
    clearTimeout(refreshTimer)
  }
  const delay = Math.max(expiresIn * 1000 - EXPIRY_SAFETY_MS, MIN_REFRESH_DELAY_MS)
  refreshTimer = setTimeout(() => {
    void refreshHandler?.()
  }, delay)
}
