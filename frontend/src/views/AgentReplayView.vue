<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('replay.title') }}</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('replay.subtitle') }}</p>
      </div>
    </div>

    <!-- Session Selector -->
    <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <div class="flex items-center gap-2 mb-3">
        <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('replay.selectSession') }}</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <button v-for="s in store.sessions" :key="s.id" @click="store.selectSession(s.id)"
          class="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors"
          :class="store.selectedSessionId === s.id
            ? 'border-blue-500 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-900/20 dark:text-blue-300'
            : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:border-gray-500'">
          <span class="h-2 w-2 rounded-full" :class="s.status === 'completed' ? 'bg-green-500' : s.status === 'failed' ? 'bg-red-500' : 'bg-amber-500'"></span>
          <span class="font-medium">{{ s.issueId }}</span>
          <span class="text-gray-400">{{ s.issueTitle }}</span>
          <span class="text-xs text-gray-400">{{ s.agent }}</span>
        </button>
      </div>
    </div>

    <template v-if="store.selectedSession">
      <!-- Player Controls -->
      <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-3">
            <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ store.selectedSession.issueId }}</span>
            <span class="text-sm text-gray-500">{{ store.selectedSession.issueTitle }}</span>
          </div>
          <div class="flex items-center gap-2 text-xs text-gray-400">
            <span>{{ store.selectedSession.totalToolCalls }} {{ t('replay.toolCalls') }}</span>
            <span>{{ store.selectedSession.totalTokens.toLocaleString() }} {{ t('replay.tokens') }}</span>
          </div>
        </div>

        <!-- Scrubber Timeline -->
        <div class="relative mb-4">
          <div class="h-3 rounded-full bg-gray-200 dark:bg-gray-700 cursor-pointer" @click="(e: MouseEvent) => { const r = (e.currentTarget as HTMLElement).getBoundingClientRect(); store.seekTo(((e.clientX - r.left) / r.width) * 100) }">
            <div class="h-3 rounded-full bg-blue-500 transition-all" :style="{ width: store.progress + '%' }"></div>
          </div>
          <!-- Event markers -->
          <div class="absolute top-0 left-0 h-3 w-full pointer-events-none">
            <div v-for="evt in store.selectedSession.events" :key="evt.id"
              class="absolute top-0 h-3 w-1.5 rounded-full -translate-y-0"
              :class="store.eventColor(evt.type)"
              :style="{ left: (evt.timestamp / store.selectedSession.totalDurationMs * 100) + '%' }"
              :title="evt.title">
            </div>
          </div>
        </div>

        <!-- Controls -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1">
            <button @click="store.stepBackward" class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700" :title="t('replay.stepBack')">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z" /></svg>
            </button>
            <button v-if="!store.isPlaying" @click="store.play" class="p-2.5 rounded-full bg-blue-600 text-white hover:bg-blue-700" :title="t('replay.play')">
              <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
            </button>
            <button v-else @click="store.pause" class="p-2.5 rounded-full bg-red-600 text-white hover:bg-red-700" :title="t('replay.pause')">
              <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" /></svg>
            </button>
            <button @click="store.stepForward" class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700" :title="t('replay.stepForward')">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z" /></svg>
            </button>
          </div>
          <div class="flex items-center gap-3">
            <span class="font-mono text-sm text-gray-700 dark:text-gray-300">{{ store.formatTime(store.currentTime) }} / {{ store.formatTime(store.selectedSession.totalDurationMs) }}</span>
            <div class="flex items-center gap-1">
              <button v-for="sp in [0.5, 1, 2, 4]" :key="sp" @click="store.setSpeed(sp)"
                class="rounded px-2 py-0.5 text-xs font-medium transition-colors"
                :class="store.playSpeed === sp ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'">
                {{ sp }}x
              </button>
            </div>
          </div>
        </div>

        <!-- Legend -->
        <div class="mt-4 flex flex-wrap gap-3 border-t border-gray-100 pt-3 dark:border-gray-700">
          <div v-for="(label, key) in legendItems" :key="key" class="flex items-center gap-1.5">
            <span class="h-2 w-2 rounded-full" :class="store.eventColor(key as string)"></span>
            <span class="text-[10px] text-gray-500">{{ label }}</span>
          </div>
        </div>
      </div>

      <!-- Synchronized Views -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <!-- Event Stream -->
        <div class="lg:col-span-2 rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between border-b border-gray-200 px-5 py-3 dark:border-gray-700">
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ t('replay.eventStream') }}</span>
            <span class="text-[10px] text-gray-400">{{ store.visibleEvents.length }} / {{ store.selectedSession.events.length }}</span>
          </div>
          <div class="max-h-96 overflow-auto p-4 space-y-2">
            <div v-for="evt in store.visibleEvents" :key="evt.id"
              class="flex items-start gap-3 rounded-lg p-3 transition-colors"
              :class="store.currentEvent?.id === evt.id ? 'bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-200 dark:ring-blue-800' : 'hover:bg-gray-50 dark:hover:bg-gray-700/30'">
              <div class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full" :class="store.eventColor(evt.type)">
                <svg class="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="store.eventIcon(evt.type)" /></svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-900 dark:text-white">{{ evt.title }}</span>
                  <span class="text-[10px] text-gray-400">{{ store.formatTime(evt.timestamp) }}</span>
                </div>
                <p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{{ evt.detail }}</p>
                <div v-if="evt.metadata" class="mt-1 flex flex-wrap gap-1">
                  <span v-for="(val, key) in evt.metadata" :key="key" class="inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] text-gray-600 dark:bg-gray-700 dark:text-gray-400">{{ key }}: {{ val }}</span>
                </div>
              </div>
            </div>
            <div v-if="store.visibleEvents.length === 0" class="py-8 text-center text-sm text-gray-400">{{ t('replay.noEvents') }}</div>
          </div>
        </div>

        <!-- Side Panel: Current Context -->
        <div class="space-y-4">
          <!-- Current Event Detail -->
          <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">{{ t('replay.currentEvent') }}</h4>
            <template v-if="store.currentEvent">
              <div class="flex items-center gap-2 mb-2">
                <span class="inline-flex h-6 w-6 items-center justify-center rounded-full" :class="store.eventColor(store.currentEvent.type)">
                  <svg class="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="store.eventIcon(store.currentEvent.type)" /></svg>
                </span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ store.currentEvent.title }}</span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ store.currentEvent.detail }}</p>
            </template>
            <p v-else class="text-xs text-gray-400">{{ t('replay.waitingForEvents') }}</p>
          </div>

          <!-- Files Affected -->
          <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">{{ t('replay.filesAffected') }}</h4>
            <div class="space-y-1.5">
              <div v-for="f in affectedFiles" :key="f" class="flex items-center gap-2 rounded bg-gray-50 px-2 py-1.5 dark:bg-gray-700/50">
                <svg class="h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                <span class="font-mono text-[11px] text-gray-700 dark:text-gray-300">{{ f }}</span>
              </div>
              <p v-if="affectedFiles.length === 0" class="text-xs text-gray-400">{{ t('replay.noFilesYet') }}</p>
            </div>
          </div>

          <!-- Cypher Queries -->
          <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">{{ t('replay.cypherQueries') }}</h4>
            <div class="space-y-2">
              <div v-for="q in cypherQueries" :key="q.id" class="rounded bg-gray-900 p-2 font-mono text-[10px] text-green-400 overflow-x-auto">
                <pre>{{ q.metadata?.query || q.detail }}</pre>
              </div>
              <p v-if="cypherQueries.length === 0" class="text-xs text-gray-400">{{ t('replay.noQueriesYet') }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAgentReplayStore } from '@/stores/agentReplayStore'

const { t } = useI18n()
const store = useAgentReplayStore()

const legendItems: Record<string, string> = {
  thought: 'Thought',
  file_read: 'File Read',
  file_edit: 'File Edit',
  cypher_query: 'Cypher',
  tool_call: 'Tool Call',
  error: 'Error',
  violation: 'Violation',
  decision: 'Decision',
}

const affectedFiles = computed(() => {
  const files = new Set<string>()
  store.visibleEvents.forEach(e => {
    if (e.metadata?.file) files.add(e.metadata.file)
  })
  return Array.from(files)
})

const cypherQueries = computed(() => {
  return store.visibleEvents.filter(e => e.type === 'cypher_query')
})
</script>
