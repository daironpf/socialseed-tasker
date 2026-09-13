<template>
  <div class="space-y-6">
    <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-4">
      <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">{{ t('analysis.testFailureDetails') }}</h4>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('analysis.testName') }}</label>
          <input
            v-model="form.test_name"
            type="text"
            :placeholder="t('analysis.testNamePlaceholder')"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('issues.component') }}</label>
          <select
            v-model="form.component"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          >
            <option value="">{{ t('analysis.anyComponent') }}</option>
            <option v-for="comp in compStore.components" :key="comp.id" :value="comp.name">{{ comp.name }}</option>
          </select>
        </div>
      </div>

      <div class="mt-4">
        <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('analysis.errorMessage') }}</label>
        <textarea
          v-model="form.error_message"
          rows="3"
          :placeholder="t('analysis.errorPlaceholder')"
          class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        ></textarea>
      </div>

      <div class="mt-4">
        <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">{{ t('issues.labels') }}</label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="label in availableLabels"
            :key="label"
            class="rounded-full border px-3 py-1 text-xs font-medium transition-colors"
            :class="form.labels.includes(label)
              ? 'border-blue-500 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
              : 'border-gray-300 bg-white text-gray-600 hover:border-blue-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400'"
            @click="toggleLabel(label)"
          >
            {{ label }}
          </button>
        </div>
      </div>

      <div class="mt-4 flex gap-3">
        <button
          :disabled="!form.test_name || !form.error_message || analysisStore.loadingRootCause"
          class="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
          @click="analyze"
        >
          {{ analysisStore.loadingRootCause ? t('analysis.loading') : t('analysis.findRootCause') }}
        </button>
        <button
          v-if="analysisStore.rootCauseResults.length"
          class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
          @click="loadPreset"
        >
          {{ t('analysis.loadSampleFailure') }}
        </button>
      </div>
    </div>

    <div v-if="analysisStore.loadingRootCause" class="flex items-center justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-purple-500 border-t-transparent"></div>
      <span class="ml-3 text-sm text-gray-500">{{ t('analysis.searchingRootCauses') }}</span>
    </div>

    <div v-else-if="analysisStore.rootCauseResults.length" class="space-y-4">
      <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
        {{ t('analysis.candidateRootCauses') }} ({{ analysisStore.rootCauseResults.length }})
      </h4>

      <div
        v-for="(link, idx) in analysisStore.rootCauseResults"
        :key="link.issue_id"
        class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <span
              class="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold"
              :class="idx === 0 ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'"
            >
              {{ idx + 1 }}
            </span>
            <div>
              <div class="flex items-center gap-2">
                <span class="font-mono text-xs font-bold text-gray-500">{{ link.issue_id }}</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ link.issue_title }}</span>
              </div>
              <div class="mt-1 flex items-center gap-2">
                <span
                  class="rounded px-1.5 py-0.5 text-[10px] font-bold"
                  :class="statusBadgeClass(link.issue_status)"
                >
                  {{ link.issue_status }}
                </span>
                <span v-if="link.graph_distance < 999" class="text-xs text-gray-500">
                  {{ t('analysis.graphDistance') }} {{ link.graph_distance }}
                </span>
              </div>
            </div>
          </div>

          <div class="text-right">
            <div class="text-lg font-bold" :class="confidenceColor(link.confidence)">
              {{ Math.round(link.confidence) }}%
            </div>
            <div class="text-[10px] text-gray-500">{{ t('analysis.confidence') }}</div>
          </div>
        </div>

        <div class="mt-3 h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            class="h-2 rounded-full transition-all duration-500"
            :class="confidenceBarColor(link.confidence)"
            :style="{ width: `${Math.min(link.confidence, 100)}%` }"
          ></div>
        </div>

        <div class="mt-3 flex flex-wrap gap-1.5">
          <span
            v-for="reason in link.reasons"
            :key="reason"
            class="rounded-full bg-gray-100 px-2.5 py-0.5 text-[10px] font-medium text-gray-700 dark:bg-gray-700 dark:text-gray-300"
          >
            {{ reason }}
          </span>
        </div>
      </div>
    </div>

    <div v-else-if="!analysisStore.loadingRootCause && searched" class="flex flex-col items-center justify-center py-12 text-gray-400">
      <svg class="mb-3 h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <p class="text-sm">{{ t('analysis.noMatchingRootCauses') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useComponentsStore } from '@/stores/componentsStore'

const { t } = useI18n()

const analysisStore = useAnalysisStore()
const compStore = useComponentsStore()

const searched = ref(false)
const presetIndex = ref(0)

const availableLabels = [
  'bug', 'auth', 'security', 'performance', 'database', 'ui', 'feature',
  'webhook', 'graphql', 'dependencies', 'regression', 'timeout', 'concurrency',
]

const form = ref({
  test_name: '',
  error_message: '',
  component: '',
  labels: [] as string[],
})

onMounted(() => {
  compStore.fetchComponents()
})

function toggleLabel(label: string) {
  const idx = form.value.labels.indexOf(label)
  if (idx >= 0) form.value.labels.splice(idx, 1)
  else form.value.labels.push(label)
}

async function analyze() {
  if (!form.value.test_name || !form.value.error_message) return
  searched.value = true
  await analysisStore.analyzeRootCause({
    test_name: form.value.test_name,
    error_message: form.value.error_message,
    component: form.value.component || undefined,
    labels: form.value.labels.length ? form.value.labels : undefined,
  })
}

async function loadPreset() {
  const failures = await analysisStore.fetchTestFailures()
  if (failures.length) {
    const f = failures[presetIndex.value % failures.length]
    form.value.test_name = f.test_name
    form.value.error_message = f.error_message
    form.value.component = f.component
    form.value.labels = [...f.labels]
    presetIndex.value++
  }
}

function confidenceColor(conf: number) {
  if (conf >= 70) return 'text-green-600 dark:text-green-400'
  if (conf >= 40) return 'text-amber-600 dark:text-amber-400'
  return 'text-gray-500'
}

function confidenceBarColor(conf: number) {
  if (conf >= 70) return 'bg-green-500'
  if (conf >= 40) return 'bg-amber-500'
  return 'bg-gray-400'
}

function statusBadgeClass(status: string) {
  const map: Record<string, string> = {
    OPEN: 'bg-blue-100 text-blue-800',
    IN_PROGRESS: 'bg-amber-100 text-amber-800',
    BLOCKED: 'bg-red-100 text-red-800',
    CLOSED: 'bg-green-100 text-green-800',
  }
  return map[status] || 'bg-gray-100 text-gray-800'
}
</script>
