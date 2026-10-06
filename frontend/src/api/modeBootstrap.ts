// Boot-time API mode detection (notas.md #3 first-entry fix): a fresh
// browser has no stored mode, so the default "mock" made an installed
// deployment show the demo 5 HITL instead of the real onboarding
// notifications. The first navigation now probes the real backend once
// ({API_URL}/health, exempt from the API key middleware) and switches to
// real mode when it answers. Only success is persisted: without a backend
// the mock default is kept and the probe runs again on the next load.

import { API_MODE_STORAGE_KEY, API_URL, isMockMode, setApiMode } from './client'

const PROBE_TIMEOUT_MS = 2500

let probePromise: Promise<void> | null = null

/** Resolve the api mode for this browser. Called once per page load, before `initSession`. */
export function resolveInitialApiMode(): Promise<void> {
  if (!probePromise) {
    probePromise = probe()
  }
  return probePromise
}

function probe(): Promise<void> {
  // An explicit choice (setup wizard or manual toggle) always wins.
  if (localStorage.getItem(API_MODE_STORAGE_KEY) !== null || !isMockMode()) {
    return Promise.resolve()
  }
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS)
  return fetch(`${API_URL}/health`, { signal: controller.signal })
    .then((response) => {
      if (response.ok) {
        setApiMode('real')
      }
    })
    .catch(() => {
      // Backend unreachable: keep the mock default; the next load retries.
    })
    .finally(() => clearTimeout(timer))
}

/** Test hook: forget the memoized probe so a spec can run it again. */
export function resetApiModeProbe(): void {
  probePromise = null
}
