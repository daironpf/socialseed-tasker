<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-semibold text-gray-800 dark:text-gray-200">{{ t('agentStudio.runs.title') }}</h2>
      <button
        class="text-[11px] text-sky-600 hover:underline dark:text-sky-400"
        :disabled="loading"
        @click="load"
      >
        {{ t('agentStudio.runs.retry') }}
      </button>
    </div>

    <p v-if="!agentId" class="text-xs text-gray-500 dark:text-gray-400">{{ t('agentStudio.runs.selectAgent') }}</p>

    <template v-else>
      <p v-if="loading" class="text-xs text-gray-500 dark:text-gray-400">{{ t('agentStudio.runs.loading') }}</p>

      <div v-else-if="error" class="flex items-center gap-3">
        <span class="text-xs text-rose-600 dark:text-rose-400">{{ t('agentStudio.runs.error') }}</span>
        <button
          class="rounded-lg border border-gray-300 px-2.5 py-1 text-[11px] font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="load"
        >
          {{ t('agentStudio.runs.retry') }}
        </button>
      </div>

      <p v-else-if="!runs.length" class="text-xs text-gray-500 dark:text-gray-400">{{ t('agentStudio.runs.empty') }}</p>

      <ul v-else class="divide-y divide-gray-100 dark:divide-gray-700/60">
        <li v-for="run in runs" :key="run.id">
          <button
            class="flex w-full items-center gap-2 px-1 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700/40"
            @click="toggleLogs(run.id)"
          >
            <span
              class="rounded-full px-2 py-0.5 text-[10px] font-bold"
              :class="statusClasses(run.status)"
            >
              {{ t(`agentStudio.runs.status.${run.status}`) }}
            </span>
            <span class="text-xs text-gray-600 dark:text-gray-300">{{ formatTimestamp(run.started_at) }}</span>
            <span v-if="run.duration_ms != null" class="text-[11px] text-gray-400 dark:text-gray-500">
              {{ t('agentStudio.runs.durationMs', { ms: run.duration_ms }) }}
            </span>
            <span v-if="run.total_tokens != null" class="text-[11px] text-gray-400 dark:text-gray-500">
              {{ t('agentStudio.runs.tokens', { count: run.total_tokens }) }}
            </span>
            <span v-if="run.issue_id" class="ml-auto text-[11px] text-sky-600 dark:text-sky-400">{{ run.issue_id }}</span>
          </button>

          <div v-if="expandedId === run.id" class="border-t border-gray-100 px-1 py-2 dark:border-gray-700/60">
            <p v-if="logsLoading" class="text-[11px] text-gray-500 dark:text-gray-400">{{ t('agentStudio.runs.loading') }}</p>
            <p v-else-if="logsError" class="text-[11px] text-rose-600 dark:text-rose-400">{{ t('agentStudio.runs.logsError') }}</p>
            <p v-else-if="!logs.length" class="text-[11px] text-gray-500 dark:text-gray-400">{{ t('agentStudio.runs.emptyLogs') }}</p>
            <ul v-else class="space-y-1.5">
              <li v-for="entry in logs" :key="entry.seq" class="flex gap-2">
                <span class="mt-0.5 shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-semibold text-gray-500 dark:bg-gray-700 dark:text-gray-300">
                  {{ entry.type }}
                </span>
                <pre class="whitespace-pre-wrap break-words text-[11px] text-gray-700 dark:text-gray-300">{{ entry.content_markdown }}</pre>
              </li>
            </ul>
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { fetchAgentRuns, fetchRunLogs } from '@/api/agentRunsApi'
import type { AgentRun, AgentRunLog, AgentRunStatus } from '@/api/agentRunsApi'

const props = defineProps<{ agentId: string }>()

const { t } = useI18n()

const runs = ref<AgentRun[]>([])
const logs = ref<AgentRunLog[]>([])
const loading = ref(false)
const error = ref(false)
const logsLoading = ref(false)
const logsError = ref(false)
const expandedId = ref<string | null>(null)

async function load() {
  if (!props.agentId) {
    runs.value = []
    return
  }
  loading.value = true
  error.value = false
  try {
    runs.value = await fetchAgentRuns(props.agentId)
  } catch {
    runs.value = []
    error.value = true
  } finally {
    loading.value = false
  }
}

async function loadLogs(runId: string) {
  logsLoading.value = true
  logsError.value = false
  try {
    logs.value = await fetchRunLogs(runId)
  } catch {
    logs.value = []
    logsError.value = true
  } finally {
    logsLoading.value = false
  }
}

async function toggleLogs(runId: string) {
  if (expandedId.value === runId) {
    expandedId.value = null
    logs.value = []
    return
  }
  expandedId.value = runId
  await loadLogs(runId)
}

function statusClasses(status: AgentRunStatus): string {
  if (status === 'running') return 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300'
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
  if (status === 'failed') return 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300'
  return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
}

function formatTimestamp(value?: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

watch(
  () => props.agentId,
  () => {
    expandedId.value = null
    logs.value = []
    void load()
  },
  { immediate: true },
)

defineExpose({ load })
</script>
