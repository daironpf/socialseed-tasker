/**
 * Routes whose real (non-mock) implementation has not started yet.
 *
 * Every listed view runs exclusively against the mock API / local dataset
 * (mock API mode in `api/client.ts`), so the UI shows a pending badge
 * (hourglass) in the sidebar navigation and in the page header to signal
 * that the feature is awaiting development.
 *
 * The badge is only shown while the app runs in mock mode; switching the
 * data source to the real API (issue #517) hides it.
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
  return isMockMode() && PENDING_FEATURE_ROUTES.includes(path)
}
