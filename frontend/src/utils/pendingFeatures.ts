/**
 * Routes whose real (non-mock) implementation has not started yet.
 *
 * Every listed view runs exclusively against the mock API / local dataset
 * (`USE_MOCK = true` in `api/client.ts`), so the UI shows a pending badge
 * (hourglass) in the sidebar navigation and in the page header to signal
 * that the feature is awaiting development.
 *
 * See features.md §50 "Known Gaps & Missing Features".
 */
export const PENDING_FEATURE_ROUTES: readonly string[] = [
  '/board',
  '/system',
  '/kanban',
  '/list',
  '/components',
  '/policies',
  '/constraints',
  '/sandbox',
  '/rag',
  '/finops',
  '/auto-healing',
  '/replay',
  '/executive',
  '/users',
  '/chat',
  '/mcp',
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
