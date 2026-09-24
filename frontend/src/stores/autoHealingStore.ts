import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { PipelineRun, LogEntry, FixAttempt, PipelineStage } from '@/types/autoHealing'
import { useSoundEffects } from '@/composables/useSoundEffects'

const MOCK_STAGES: PipelineStage[] = [
  { id: 'test_failure', label: 'Test Failure Detected', status: 'completed', startedAt: '2026-09-20T10:00:00Z', completedAt: '2026-09-20T10:00:02Z', durationMs: 2000, details: '3 tests failed in auth module' },
  { id: 'neo4j_root_cause', label: 'Neo4j Root Cause Analysis', status: 'completed', startedAt: '2026-09-20T10:00:02Z', completedAt: '2026-09-20T10:00:15Z', durationMs: 13000, details: 'Root cause: token validation missing expiry check' },
  { id: 'task_generation', label: 'Task Generation', status: 'completed', startedAt: '2026-09-20T10:00:15Z', completedAt: '2026-09-20T10:00:18Z', durationMs: 3000, details: 'Created ISS-042: Fix token expiry validation' },
  { id: 'agent_fix', label: 'Agent Fix Attempt', status: 'running', startedAt: '2026-09-20T10:00:18Z', details: 'Agent claude-3.5-sonnet generating fix...' },
  { id: 'pr_created', label: 'PR Created', status: 'pending' },
]

const MOCK_RUNS: PipelineRun[] = [
  {
    id: 'run-001', issueId: 'ISS-042', issueTitle: 'Fix token expiry validation',
    repo: 'socialseed-tasker', branch: 'fix/token-expiry', commitSha: 'a1b2c3d',
    stages: MOCK_STAGES, currentStageIndex: 3, startedAt: '2026-09-20T10:00:00Z', status: 'running',
    neo4jNodeId: 'neo:node:42',
  },
  {
    id: 'run-002', issueId: 'ISS-038', issueTitle: 'Add rate limiting to API',
    repo: 'socialseed-tasker', branch: 'fix/rate-limit', commitSha: 'e4f5g6h',
    stages: [
      { id: 'test_failure', label: 'Test Failure Detected', status: 'completed', startedAt: '2026-09-19T15:00:00Z', completedAt: '2026-09-19T15:00:01Z', durationMs: 1000 },
      { id: 'neo4j_root_cause', label: 'Neo4j Root Cause Analysis', status: 'completed', startedAt: '2026-09-19T15:00:01Z', completedAt: '2026-09-19T15:00:08Z', durationMs: 7000 },
      { id: 'task_generation', label: 'Task Generation', status: 'completed', startedAt: '2026-09-19T15:00:08Z', completedAt: '2026-09-19T15:00:10Z', durationMs: 2000 },
      { id: 'agent_fix', label: 'Agent Fix Attempt', status: 'completed', startedAt: '2026-09-19T15:00:10Z', completedAt: '2026-09-19T15:00:45Z', durationMs: 35000 },
      { id: 'pr_created', label: 'PR Created', status: 'completed', startedAt: '2026-09-19T15:00:45Z', completedAt: '2026-09-19T15:00:48Z', durationMs: 3000, details: 'PR #127 created' },
    ],
    currentStageIndex: 4, startedAt: '2026-09-19T15:00:00Z', completedAt: '2026-09-19T15:00:48Z', status: 'completed',
    prUrl: 'https://github.com/daironpf/socialseed-tasker/pull/127', neo4jNodeId: 'neo:node:38',
  },
  {
    id: 'run-003', issueId: 'ISS-035', issueTitle: 'Fix WebSocket reconnect loop',
    repo: 'socialseed-tasker', branch: 'fix/ws-reconnect', commitSha: 'i7j8k9l',
    stages: [
      { id: 'test_failure', label: 'Test Failure Detected', status: 'completed', startedAt: '2026-09-19T09:00:00Z', completedAt: '2026-09-19T09:00:03Z', durationMs: 3000 },
      { id: 'neo4j_root_cause', label: 'Neo4j Root Cause Analysis', status: 'completed', startedAt: '2026-09-19T09:00:03Z', completedAt: '2026-09-19T09:00:12Z', durationMs: 9000 },
      { id: 'task_generation', label: 'Task Generation', status: 'completed', startedAt: '2026-09-19T09:00:12Z', completedAt: '2026-09-19T09:00:14Z', durationMs: 2000 },
      { id: 'agent_fix', label: 'Agent Fix Attempt', status: 'failed', startedAt: '2026-09-19T09:00:14Z', completedAt: '2026-09-19T09:00:50Z', durationMs: 36000, details: 'Agent unable to resolve circular dependency' },
      { id: 'pr_created', label: 'PR Created', status: 'pending' },
    ],
    currentStageIndex: 3, startedAt: '2026-09-19T09:00:00Z', status: 'failed',
  },
]

const MOCK_LOGS: LogEntry[] = [
  { id: 'log-001', runId: 'run-001', timestamp: '2026-09-20T10:00:00Z', source: 'test', content: 'FAIL src/auth/token.test.ts - Token expiry not validated' },
  { id: 'log-002', runId: 'run-001', timestamp: '2026-09-20T10:00:00Z', source: 'test', content: 'FAIL src/auth/token.test.ts - Expired token accepted' },
  { id: 'log-003', runId: 'run-001', timestamp: '2026-09-20T10:00:00Z', source: 'test', content: 'FAIL src/auth/session.test.ts - Session not invalidated' },
  { id: 'log-004', runId: 'run-001', timestamp: '2026-09-20T10:00:02Z', source: 'system', content: '[Auto-Healing] Test failure detected. Initiating root cause analysis...' },
  { id: 'log-005', runId: 'run-001', timestamp: '2026-09-20T10:00:05Z', source: 'system', content: '[Neo4j] Querying failure patterns... Found 2 related issues' },
  { id: 'log-006', runId: 'run-001', timestamp: '2026-09-20T10:00:15Z', source: 'system', content: '[Neo4j] Root cause: ISS-028 (token validation) - missing expiry check in validateToken()' },
  { id: 'log-007', runId: 'run-001', timestamp: '2026-09-20T10:00:18Z', source: 'system', content: '[Tasker] Generated ISS-042: Fix token expiry validation' },
  { id: 'log-008', runId: 'run-001', timestamp: '2026-09-20T10:00:20Z', source: 'agent', content: '[Agent] claude-3.5-sonnet analyzing codebase...' },
  { id: 'log-009', runId: 'run-001', timestamp: '2026-09-20T10:00:25Z', source: 'agent', content: '[Agent] Found validateToken() in src/auth/token.ts:45' },
  { id: 'log-010', runId: 'run-001', timestamp: '2026-09-20T10:00:30Z', source: 'agent', content: '[Agent] Adding expiry check: if (token.exp < Date.now()) throw new Error("Token expired")' },
  { id: 'log-011', runId: 'run-002', timestamp: '2026-09-19T15:00:00Z', source: 'test', content: 'FAIL src/api/rateLimit.test.ts - No rate limiting on /api/chat' },
  { id: 'log-012', runId: 'run-002', timestamp: '2026-09-19T15:00:48Z', source: 'system', content: '[Auto-Healing] Pipeline completed. PR #127 created successfully.' },
]

const MOCK_FIX_ATTEMPTS: FixAttempt[] = [
  { id: 'fix-001', runId: 'run-001', timestamp: '2026-09-20T10:00:30Z', description: 'Add token expiry validation in validateToken()', filesChanged: ['src/auth/token.ts', 'src/auth/token.test.ts'], status: 'attempting', diffPreview: '- const payload = jwt.verify(token, secret);\n+ const payload = jwt.verify(token, secret);\n+ if (payload.exp && payload.exp < Date.now() / 1000) {\n+   throw new Error("Token expired");\n+ }' },
  { id: 'fix-002', runId: 'run-002', timestamp: '2026-09-19T15:00:15Z', description: 'Add rate limiting middleware to /api/chat', filesChanged: ['src/api/middleware/rateLimit.ts', 'src/api/routes/chat.ts'], status: 'success', diffPreview: '+ import rateLimit from "express-rate-limit";\n+ const chatLimiter = rateLimit({ windowMs: 60000, max: 10 });\n+ router.post("/chat", chatLimiter, handler);' },
  { id: 'fix-003', runId: 'run-003', timestamp: '2026-09-19T09:00:20Z', description: 'Fix WebSocket reconnect backoff', filesChanged: ['src/websocket/reconnect.ts'], status: 'failed', error: 'Circular dependency detected between reconnect.ts and connection.ts' },
]

export const useAutoHealingStore = defineStore('autoHealing', () => {
  const runs = ref<PipelineRun[]>([...MOCK_RUNS])
  const logs = ref<LogEntry[]>([...MOCK_LOGS])
  const fixAttempts = ref<FixAttempt[]>([...MOCK_FIX_ATTEMPTS])
  const selectedRunId = ref<string>('run-001')
  const loading = ref(false)
  const error = ref<string | null>(null)

  const selectedRun = computed(() => runs.value.find(r => r.id === selectedRunId.value))
  const runLogs = computed(() => logs.value.filter(l => l.runId === selectedRunId.value).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()))
  const runFixes = computed(() => fixAttempts.value.filter(f => f.runId === selectedRunId.value))
  const activeRuns = computed(() => runs.value.filter(r => r.status === 'running'))
  const completedRuns = computed(() => runs.value.filter(r => r.status === 'completed'))
  const failedRuns = computed(() => runs.value.filter(r => r.status === 'failed'))

  function stageColor(status: string) {
    if (status === 'completed') return 'bg-green-500'
    if (status === 'running') return 'bg-blue-500 animate-pulse'
    if (status === 'failed') return 'bg-red-500'
    return 'bg-gray-300 dark:bg-gray-600'
  }

  function stageIcon(status: string) {
    if (status === 'completed') return 'M5 13l4 4L19 7'
    if (status === 'running') return 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
    if (status === 'failed') return 'M6 18L18 6M6 6l12 12'
    return 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }

  function selectRun(id: string) { selectedRunId.value = id }

  function simulateCompletion(id?: string): boolean {
    const run =
      runs.value.find(r => r.id === (id ?? selectedRunId.value)) ??
      runs.value.find(r => r.status === 'running')
    if (!run || run.status !== 'running') return false
    const now = new Date().toISOString()
    run.stages = run.stages.map(s =>
      s.status === 'pending' || s.status === 'running'
        ? { ...s, status: 'completed' as const, completedAt: now }
        : s
    )
    run.currentStageIndex = run.stages.length - 1
    run.status = 'completed'
    run.completedAt = now
    logs.value.push({
      id: `log-${Date.now()}`,
      runId: run.id,
      timestamp: now,
      source: 'system',
      content: '[Auto-Healing] Pipeline completed successfully (simulated).',
    })
    useSoundEffects().playSuccess()
    return true
  }

  function formatDuration(ms?: number) {
    if (!ms) return '-'
    if (ms < 1000) return ms + 'ms'
    return (ms / 1000).toFixed(1) + 's'
  }

  function formatTime(ts: string) {
    return new Date(ts).toLocaleTimeString()
  }

  return {
    runs, logs, fixAttempts, selectedRunId, loading, error,
    selectedRun, runLogs, runFixes, activeRuns, completedRuns, failedRuns,
    stageColor, stageIcon, selectRun, simulateCompletion, formatDuration, formatTime,
  }
})
