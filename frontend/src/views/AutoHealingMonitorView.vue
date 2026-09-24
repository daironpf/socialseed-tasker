<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('autoHealing.title') }}</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('autoHealing.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          v-if="store.activeRuns.length"
          class="rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 transition-colors hover:bg-emerald-100 dark:border-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300 dark:hover:bg-emerald-900/40"
          @click="store.simulateCompletion(store.selectedRunId)"
        >
          {{ t('autoHealing.simulateSuccess') }}
        </button>
        <span class="inline-flex items-center gap-1.5 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
          <span class="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse"></span>
          {{ store.activeRuns.length }} {{ t('autoHealing.active') }}
        </span>
        <span class="inline-flex items-center gap-1.5 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-300">
          {{ store.completedRuns.length }} {{ t('autoHealing.completed') }}
        </span>
        <span class="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-300">
          {{ store.failedRuns.length }} {{ t('autoHealing.failed') }}
        </span>
      </div>
    </div>

    <!-- Run Selector -->
    <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <div class="flex items-center gap-2 mb-3">
        <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('autoHealing.selectRun') }}</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <button v-for="run in store.runs" :key="run.id" @click="store.selectRun(run.id)"
          class="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors"
          :class="store.selectedRunId === run.id
            ? 'border-blue-500 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-900/20 dark:text-blue-300'
            : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:border-gray-500'">
          <span class="h-2 w-2 rounded-full" :class="run.status === 'running' ? 'bg-blue-500 animate-pulse' : run.status === 'completed' ? 'bg-green-500' : 'bg-red-500'"></span>
          <span class="font-medium">{{ run.issueId }}</span>
          <span class="text-gray-400">{{ run.issueTitle }}</span>
        </button>
      </div>
    </div>

    <template v-if="store.selectedRun">
      <!-- Pipeline Progress -->
      <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('autoHealing.pipelineProgress') }}</h3>
          <div class="flex items-center gap-2">
            <span class="text-xs text-gray-400">{{ store.selectedRun.repo }}/{{ store.selectedRun.branch }}</span>
            <span class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] text-gray-500 dark:bg-gray-700 dark:text-gray-400">{{ store.selectedRun.commitSha }}</span>
          </div>
        </div>
        <div class="relative mb-6">
          <div class="h-2 rounded-full bg-gray-200 dark:bg-gray-700">
            <div class="h-2 rounded-full transition-all duration-500" :class="store.selectedRun.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'" :style="{ width: pipelineProgress + '%' }"></div>
          </div>
        </div>
        <div class="grid grid-cols-5 gap-2">
          <div v-for="stage in store.selectedRun.stages" :key="stage.id" class="text-center">
            <div class="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full" :class="store.stageColor(stage.status)">
              <svg v-if="stage.status === 'completed'" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
              <svg v-else-if="stage.status === 'running'" class="h-5 w-5 text-white animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
              <svg v-else-if="stage.status === 'failed'" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
              <svg v-else class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="12" cy="12" r="3" /></svg>
            </div>
            <div class="text-[11px] font-medium text-gray-700 dark:text-gray-300">{{ t('autoHealing.stages.' + stage.id) }}</div>
            <div v-if="stage.durationMs" class="text-[10px] text-gray-400">{{ store.formatDuration(stage.durationMs) }}</div>
            <div v-if="stage.details" class="mt-1 text-[10px] text-gray-400 truncate max-w-[120px] mx-auto" :title="stage.details">{{ stage.details }}</div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Live Terminal -->
        <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between border-b border-gray-200 px-5 py-3 dark:border-gray-700">
            <div class="flex items-center gap-2">
              <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              <span class="text-sm font-medium text-gray-900 dark:text-white">{{ t('autoHealing.liveLogs') }}</span>
            </div>
            <span class="text-[10px] text-gray-400">{{ store.runLogs.length }} {{ t('autoHealing.entries') }}</span>
          </div>
          <div ref="terminalRef" class="bg-gray-900 text-green-400 font-mono text-xs p-4 rounded-b-xl overflow-auto max-h-80">
            <div v-for="log in store.runLogs" :key="log.id" class="flex gap-2 leading-relaxed">
              <span class="text-gray-500 shrink-0">{{ store.formatTime(log.timestamp) }}</span>
              <span class="shrink-0" :class="log.source === 'test' ? 'text-red-400' : log.source === 'agent' ? 'text-blue-400' : 'text-yellow-400'">[{{ log.source }}]</span>
              <span :class="log.source === 'test' ? 'text-red-300' : ''">{{ log.content }}</span>
            </div>
            <div v-if="store.selectedRun.status === 'running'" class="flex gap-2 mt-1">
              <span class="text-gray-500">...</span>
              <span class="animate-pulse text-green-400">_</span>
            </div>
          </div>
        </div>

        <!-- Fix Attempts -->
        <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between border-b border-gray-200 px-5 py-3 dark:border-gray-700">
            <div class="flex items-center gap-2">
              <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
              <span class="text-sm font-medium text-gray-900 dark:text-white">{{ t('autoHealing.fixAttempts') }}</span>
            </div>
          </div>
          <div class="p-5 space-y-4 max-h-80 overflow-auto">
            <div v-if="store.runFixes.length === 0" class="text-center py-8 text-sm text-gray-400">{{ t('autoHealing.noFixes') }}</div>
            <div v-for="fix in store.runFixes" :key="fix.id" class="rounded-lg border border-gray-200 p-3 dark:border-gray-700">
              <div class="flex items-start justify-between mb-2">
                <div class="text-sm text-gray-700 dark:text-gray-300">{{ fix.description }}</div>
                <span class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold" :class="fix.status === 'success' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : fix.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'">
                  {{ fix.status === 'success' ? t('autoHealing.success') : fix.status === 'failed' ? t('autoHealing.failed') : t('autoHealing.attempting') }}
                </span>
              </div>
              <div class="flex flex-wrap gap-1 mb-2">
                <span v-for="f in fix.filesChanged" :key="f" class="inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] text-gray-600 dark:bg-gray-700 dark:text-gray-400">{{ f }}</span>
              </div>
              <div v-if="fix.diffPreview" class="rounded bg-gray-900 p-2 font-mono text-[10px] text-green-400 overflow-x-auto">
                <pre>{{ fix.diffPreview }}</pre>
              </div>
              <div v-if="fix.error" class="mt-2 rounded bg-red-50 p-2 text-[10px] text-red-600 dark:bg-red-900/20 dark:text-red-400">{{ fix.error }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Links -->
      <div class="flex gap-3">
        <a v-if="store.selectedRun.prUrl" :href="store.selectedRun.prUrl" target="_blank" class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
          {{ t('autoHealing.viewPR') }}
        </a>
        <button v-if="store.selectedRun.neo4jNodeId" class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" /></svg>
          {{ t('autoHealing.viewNeo4j') }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAutoHealingStore } from '@/stores/autoHealingStore'

const { t } = useI18n()
const store = useAutoHealingStore()
const terminalRef = ref<HTMLElement | null>(null)

const pipelineProgress = computed(() => {
  if (!store.selectedRun) return 0
  const completed = store.selectedRun.stages.filter(s => s.status === 'completed').length
  const total = store.selectedRun.stages.length
  const current = store.selectedRun.stages[store.selectedRun.currentStageIndex]
  const bonus = current?.status === 'running' ? 0.5 : 0
  return ((completed + bonus) / total) * 100
})
</script>
