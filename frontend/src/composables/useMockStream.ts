import { ref, computed, onUnmounted } from 'vue'
import type { AgentLog } from '@/types'

export type MockSpeed = '1x' | '2x' | '5x'

export interface MockStreamOptions {
  speed?: MockSpeed
  autoStart?: boolean
}

const MOCK_LOGS_TEMPLATES: Array<{ type: AgentLog['type']; content: string }> = [
  { type: 'reasoning', content: 'Analyzing issue dependencies and component relationships...' },
  { type: 'reasoning', content: 'Scanning codebase for affected modules...' },
  { type: 'reasoning', content: 'Evaluating architectural constraints for this change...' },
  { type: 'reasoning', content: 'Checking existing patterns in similar components...' },
  { type: 'reasoning', content: 'Computing impact score based on dependency graph...' },
  { type: 'progress', content: 'Starting analysis of component structure...' },
  { type: 'progress', content: 'Processing 12 related issues in the dependency chain...' },
  { type: 'progress', content: 'Validating constraint rules against proposed changes...' },
  { type: 'progress', content: 'Running impact analysis on transitive dependencies...' },
  { type: 'progress', content: 'Generating solution proposal with risk assessment...' },
  { type: 'files', content: '```diff\n@@ -15,6 +15,8 @@\n export function processData(data: Input) {\n+  const validated = validateInput(data)\n+  if (!validated) throw new Error("Invalid input")\n   return transform(data)\n }\n```' },
  { type: 'files', content: '```diff\n@@ -1,3 +1,5 @@\n+import { validateSchema } from "./validator"\n+import { logger } from "../utils/logger"\n import { Component } from "./types"\n```' },
  { type: 'files', content: '```diff\n@@ -42,7 +42,9 @@\n   const result = await fetch(url)\n-  return result.json()\n+  const data = await result.json()\n+  logger.info("Fetched data:", { url, size: data.length })\n+  return data\n}\n```' },
  { type: 'debt', content: 'Detected **unused import** in `utils/helpers.ts` — consider cleanup.' },
  { type: 'debt', content: 'Function `processBatch` exceeds recommended complexity threshold (cyclomatic: 12).' },
  { type: 'reasoning', content: 'Comparing proposed solution against existing architectural patterns...' },
  { type: 'reasoning', content: 'Checking for potential circular dependencies in the import graph...' },
  { type: 'progress', content: 'Applying code transformation to 3 files...' },
  { type: 'progress', content: 'Running unit test suite against modified modules...' },
  { type: 'files', content: '```diff\n@@ -88,4 +88,6 @@\n describe("FeatureX", () => {\n+  it("should handle edge case with empty input", () => {\n+    expect(processData([])).toEqual([])\n+  })\n })\n```' },
  { type: 'debt', content: 'Consider extracting repeated validation logic into a shared utility.' },
  { type: 'reasoning', content: 'Finalizing analysis — all constraints satisfied, preparing summary...' },
  { type: 'progress', content: 'Analysis complete. Generated 3 file modifications, 0 constraint violations.' },
]

function generateLog(index: number): AgentLog {
  const template = MOCK_LOGS_TEMPLATES[index % MOCK_LOGS_TEMPLATES.length]
  return {
    timestamp: new Date().toISOString(),
    type: template.type,
    content_markdown: template.content,
  }
}

export function useMockStream(options: MockStreamOptions = {}) {
  const logs = ref<AgentLog[]>([])
  const isRunning = ref(false)
  const isPaused = ref(false)
  const speed = ref<MockSpeed>(options.speed || '1x')
  const currentIndex = ref(0)

  let intervalId: ReturnType<typeof setInterval> | null = null
  let tokenCounter = ref(0)

  const BASE_INTERVAL_MS = 2000

  const intervalMs = computed(() => {
    switch (speed.value) {
      case '1x': return BASE_INTERVAL_MS
      case '2x': return BASE_INTERVAL_MS / 2
      case '5x': return BASE_INTERVAL_MS / 5
    }
  })

  const elapsedSeconds = ref(0)
  let elapsedInterval: ReturnType<typeof setInterval> | null = null

  function start() {
    if (intervalId) stop()
    isRunning.value = true
    isPaused.value = false
    currentIndex.value = 0
    logs.value = []
    tokenCounter.value = 0
    elapsedSeconds.value = 0

    elapsedInterval = setInterval(() => {
      elapsedSeconds.value++
    }, 1000)

    emitNextLog()
  }

  function emitNextLog() {
    if (!isRunning.value || isPaused.value) return

    const log = generateLog(currentIndex.value)
    logs.value.push(log)
    tokenCounter.value += Math.ceil(log.content_markdown.length / 4)
    currentIndex.value++

    const maxLogs = MOCK_LOGS_TEMPLATES.length * 2
    if (currentIndex.value >= maxLogs) {
      stop()
      return
    }

    intervalId = setTimeout(() => {
      emitNextLog()
    }, intervalMs.value) as unknown as ReturnType<typeof setInterval>
  }

  function stop() {
    if (intervalId) {
      clearTimeout(intervalId as unknown as number)
      intervalId = null
    }
    if (elapsedInterval) {
      clearInterval(elapsedInterval)
      elapsedInterval = null
    }
    isRunning.value = false
    isPaused.value = false
  }

  function pause() {
    isPaused.value = true
  }

  function resume() {
    if (!isRunning.value) return
    isPaused.value = false
    emitNextLog()
  }

  function togglePause() {
    if (isPaused.value) resume()
    else pause()
  }

  function setSpeed(newSpeed: MockSpeed) {
    speed.value = newSpeed
  }

  function clearLogs() {
    logs.value = []
    currentIndex.value = 0
    tokenCounter.value = 0
    elapsedSeconds.value = 0
  }

  onUnmounted(() => {
    stop()
  })

  return {
    logs,
    isRunning,
    isPaused,
    speed,
    intervalMs,
    tokenCount: tokenCounter,
    elapsedSeconds,
    start,
    stop,
    pause,
    resume,
    togglePause,
    setSpeed,
    clearLogs,
  }
}
