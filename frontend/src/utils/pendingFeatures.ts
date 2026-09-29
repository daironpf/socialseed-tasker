/**
 * Routes whose real (non-mock) implementation has not started yet.
 *
 * Every listed view runs exclusively against the mock API / local dataset
 * (mock API mode in `api/client.ts`), so the UI shows a pending badge
 * (construction icon) in the sidebar navigation, the mobile drawer and the
 * page header to signal that the feature is awaiting development.
 *
 * The badge is shown in both data-source modes: in mock mode it marks the
 * view as demo-only, and when the app consumes data from the real REST
 * backend (issue #517) it warns that the feature still does not talk to the
 * API. On the real API the page header additionally renders a visible
 * "Under construction" text chip via `isRealPendingFeature`.
 *
 * See features.md §50 "Known Gaps & Missing Features".
 */
import { isMockMode } from '@/api/client'

export const PENDING_FEATURE_ROUTES: readonly string[] = [
  '/board',
  '/system',
  '/kanban',
  '/list',
  '/components',
  '/policies',
  '/constraints',
  '/sandbox',
  '/finops',
  '/auto-healing',
  '/replay',
  '/executive',
  '/users',
  '/chat',
  '/hitl',
  '/organization',
  '/governance-matrix',
  '/audit-log',
  '/agents/studio',
  '/graph',
  '/analysis',
  '/analytics',
]

export function isPendingFeature(path: string): boolean {
  return PENDING_FEATURE_ROUTES.includes(path)
}

export function isRealPendingFeature(path: string): boolean {
  return !isMockMode() && isPendingFeature(path)
}
