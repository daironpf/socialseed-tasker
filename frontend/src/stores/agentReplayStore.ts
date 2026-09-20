import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AgentSession, ReplayEvent } from '@/types/agentReplay'

const MOCK_EVENTS: ReplayEvent[] = [
  { id: 'e1', timestamp: 0, type: 'thought', severity: 'info', title: 'Analyzing issue', detail: 'Agent receiving ISS-042: Fix token expiry validation. Reading issue description and related files.' },
  { id: 'e2', timestamp: 2000, type: 'file_read', severity: 'info', title: 'Read src/auth/token.ts', detail: 'Reading token validation logic to understand current implementation.', metadata: { file: 'src/auth/token.ts', lines: '1-120' } },
  { id: 'e3', timestamp: 4500, type: 'file_read', severity: 'info', title: 'Read src/auth/token.test.ts', detail: 'Reading existing test cases to understand expected behavior.', metadata: { file: 'src/auth/token.test.ts', lines: '1-85' } },
  { id: 'e4', timestamp: 6000, type: 'cypher_query', severity: 'info', title: 'Query related issues', detail: 'MATCH (i:Issue)-[:RELATES_TO]->(r:RootCause) WHERE i.id = "ISS-042" RETURN r', metadata: { query: 'MATCH (i:Issue)-[:RELATES_TO]->(r:RootCause) WHERE i.id = "ISS-042" RETURN r', rows: '2' } },
  { id: 'e5', timestamp: 8500, type: 'decision', severity: 'info', title: 'Root cause identified', detail: 'Token validation missing expiry check in validateToken() at line 45. Will add jwt expiry verification.' },
  { id: 'e6', timestamp: 10000, type: 'tool_call', severity: 'info', title: 'Edit src/auth/token.ts', detail: 'Adding expiry check: if (payload.exp && payload.exp < Date.now() / 1000) throw', metadata: { tool: 'file_edit', file: 'src/auth/token.ts' } },
  { id: 'e7', timestamp: 14000, type: 'tool_call', severity: 'info', title: 'Edit src/auth/token.test.ts', detail: 'Adding test case for expired token rejection.', metadata: { tool: 'file_edit', file: 'src/auth/token.test.ts' } },
  { id: 'e8', timestamp: 17000, type: 'tool_call', severity: 'info', title: 'Run tests', detail: 'Executing npm test to verify fix. 15 tests passing, 0 failing.', metadata: { tool: 'shell', command: 'npm test' } },
  { id: 'e9', timestamp: 20000, type: 'cypher_query', severity: 'info', title: 'Update Neo4j graph', detail: 'MATCH (i:Issue {id: "ISS-042"}) SET i.status = "resolved", i.resolvedAt = datetime()', metadata: { query: 'MATCH (i:Issue {id: "ISS-042"}) SET i.status = "resolved"', rows: '1' } },
  { id: 'e10', timestamp: 22000, type: 'error', severity: 'error', title: 'Lint warning', detail: 'Unexpected any in type assertion at token.ts:47. Using explicit type instead.', metadata: { file: 'src/auth/token.ts', line: '47' } },
  { id: 'e11', timestamp: 24000, type: 'tool_call', severity: 'success', title: 'Fix lint issue', detail: 'Changed any to JwtPayload type for proper typing.', metadata: { tool: 'file_edit', file: 'src/auth/token.ts' } },
  { id: 'e12', timestamp: 26000, type: 'violation', severity: 'warning', title: 'Policy check triggered', detail: 'Constraint C-001: Direct file edit requires approval for production files. Auto-approved (test mode).' },
  { id: 'e13', timestamp: 28000, type: 'tool_call', severity: 'info', title: 'Create commit', detail: 'git commit -m "fix: add token expiry validation"', metadata: { tool: 'shell', command: 'git commit' } },
  { id: 'e14', timestamp: 30000, type: 'thought', severity: 'info', title: 'Task completed', detail: 'All tests passing. Token expiry validation implemented. Ready for PR creation.' },
]

const MOCK_SESSIONS: AgentSession[] = [
  { id: 'session-001', issueId: 'ISS-042', issueTitle: 'Fix token expiry validation', agent: 'claude-3.5-sonnet', model: 'claude-3.5-sonnet', startedAt: '2026-09-20T10:00:00Z', totalDurationMs: 32000, events: MOCK_EVENTS, status: 'completed', totalTokens: 12500, totalToolCalls: 6 },
  { id: 'session-002', issueId: 'ISS-038', issueTitle: 'Add rate limiting to API', agent: 'gpt-4o', model: 'gpt-4o', startedAt: '2026-09-19T15:00:00Z', totalDurationMs: 28000, events: [
    { id: 'e20', timestamp: 0, type: 'thought', severity: 'info', title: 'Analyzing rate limit issue', detail: 'Reviewing API endpoints for rate limiting requirements.' },
    { id: 'e21', timestamp: 3000, type: 'file_read', severity: 'info', title: 'Read src/api/routes/chat.ts', detail: 'Checking existing route configuration.', metadata: { file: 'src/api/routes/chat.ts', lines: '1-60' } },
    { id: 'e22', timestamp: 6000, type: 'decision', severity: 'info', title: 'Strategy chosen', detail: 'Will use express-rate-limit middleware with 10 requests per minute window.' },
    { id: 'e23', timestamp: 9000, type: 'tool_call', severity: 'info', title: 'Create rateLimit.ts', detail: 'Creating new rate limiting middleware file.', metadata: { tool: 'file_create', file: 'src/api/middleware/rateLimit.ts' } },
    { id: 'e24', timestamp: 13000, type: 'tool_call', severity: 'info', title: 'Edit chat.ts', detail: 'Adding rate limiter to /api/chat route.', metadata: { tool: 'file_edit', file: 'src/api/routes/chat.ts' } },
    { id: 'e25', timestamp: 17000, type: 'tool_call', severity: 'success', title: 'Tests passing', detail: 'All 12 rate limit tests passing.' },
    { id: 'e26', timestamp: 20000, type: 'thought', severity: 'info', title: 'Done', detail: 'Rate limiting implemented and verified.' },
  ], status: 'completed', totalTokens: 8200, totalToolCalls: 4 },
]

export const useAgentReplayStore = defineStore('agentReplay', () => {
  const sessions = ref<AgentSession[]>([...MOCK_SESSIONS])
  const selectedSessionId = ref<string>('session-001')
  const currentTime = ref<number>(0)
  const isPlaying = ref(false)
  const playSpeed = ref<number>(1)
  const loading = ref(false)
  const error = ref<string | null>(null)

  let playInterval: ReturnType<typeof setInterval> | null = null

  const selectedSession = computed(() => sessions.value.find(s => s.id === selectedSessionId.value))

  const visibleEvents = computed(() => {
    if (!selectedSession.value) return []
    return selectedSession.value.events.filter(e => e.timestamp <= currentTime.value)
  })

  const currentEvent = computed(() => {
    if (!selectedSession.value) return null
    const events = selectedSession.value.events
    let curr = events[0]
    for (const e of events) {
      if (e.timestamp <= currentTime.value) curr = e
      else break
    }
    return curr
  })

  const progress = computed(() => {
    if (!selectedSession.value) return 0
    return Math.min((currentTime.value / selectedSession.value.totalDurationMs) * 100, 100)
  })

  function selectSession(id: string) {
    stop()
    selectedSessionId.value = id
    currentTime.value = 0
  }

  function play() {
    if (isPlaying.value) return
    isPlaying.value = true
    playInterval = setInterval(() => {
      if (!selectedSession.value) return
      currentTime.value += 100 * playSpeed.value
      if (currentTime.value >= selectedSession.value.totalDurationMs) {
        currentTime.value = selectedSession.value.totalDurationMs
        stop()
      }
    }, 100)
  }

  function stop() {
    isPlaying.value = false
    if (playInterval) { clearInterval(playInterval); playInterval = null }
  }

  function pause() { stop() }

  function stepForward() {
    if (!selectedSession.value) return
    currentTime.value = Math.min(currentTime.value + 1000, selectedSession.value.totalDurationMs)
  }

  function stepBackward() {
    currentTime.value = Math.max(currentTime.value - 1000, 0)
  }

  function seekTo(pct: number) {
    if (!selectedSession.value) return
    currentTime.value = Math.round((pct / 100) * selectedSession.value.totalDurationMs)
  }

  function setSpeed(s: number) { playSpeed.value = s }

  function formatTime(ms: number) {
    const s = Math.floor(ms / 1000)
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  function eventColor(type: string) {
    if (type === 'error') return 'bg-red-500'
    if (type === 'violation') return 'bg-amber-500'
    if (type === 'decision') return 'bg-purple-500'
    if (type === 'cypher_query') return 'bg-cyan-500'
    if (type === 'tool_call') return 'bg-blue-500'
    if (type === 'file_read' || type === 'file_edit') return 'bg-green-500'
    return 'bg-gray-400'
  }

  function eventIcon(type: string) {
    if (type === 'error') return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    if (type === 'violation') return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    if (type === 'decision') return 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4'
    if (type === 'cypher_query') return 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4'
    if (type === 'tool_call') return 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'
    return 'M15 12a3 3 0 11-6 0 3 3 0 016 0z'
  }

  return {
    sessions, selectedSessionId, currentTime, isPlaying, playSpeed, loading, error,
    selectedSession, visibleEvents, currentEvent, progress,
    selectSession, play, stop, pause, stepForward, stepBackward, seekTo, setSpeed,
    formatTime, eventColor, eventIcon,
  }
})
