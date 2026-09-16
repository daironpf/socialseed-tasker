<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('analysis.issueToAnalyze') }}</label>
      <select
        v-model="selectedIssueId"
        class="flex-1 max-w-md rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        @change="analyze"
      >
        <option value="">{{ t('analysis.selectIssuePlaceholder') }}</option>
        <option v-for="issue in issuesStore.issues" :key="issue.id" :value="issue.id">
          {{ issue.id }} - {{ issue.title }}
        </option>
      </select>
      <button
        v-if="selectedIssueId"
        :disabled="analysisStore.loadingImpact"
        class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        @click="analyze"
      >
        {{ analysisStore.loadingImpact ? t('analysis.loading') : t('analysis.analyze') }}
      </button>
    </div>

    <div v-if="analysisStore.loadingImpact" class="flex items-center justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
      <span class="ml-3 text-sm text-gray-500">{{ t('analysis.runningBFS') }}</span>
    </div>

    <div v-else-if="analysisStore.impactResult" class="space-y-6">
      <div class="flex items-center gap-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ analysisStore.impactResult.issue_id }} — {{ analysisStore.impactResult.issue_title }}
        </h3>
        <span
          class="rounded-full px-3 py-1 text-xs font-bold"
          :class="riskBadgeClass(analysisStore.impactResult.risk_level)"
        >
          {{ analysisStore.impactResult.risk_level }}
        </span>
      </div>

      <BlastRadiusSlider
        v-model="blastDepth"
        :total-components="componentsStore.components.length"
        :affected-count="analysisStore.impactResult.total_affected"
        :depth-counts="depthCounts"
      />

      <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center">
          <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ analysisStore.impactResult.total_affected }}</div>
          <div class="text-xs text-gray-500">{{ t('analysis.totalAffected') }}</div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center">
          <div class="text-2xl font-bold text-blue-600">{{ analysisStore.impactResult.directly_affected.length }}</div>
          <div class="text-xs text-gray-500">{{ t('analysis.directDependencies') }}</div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center">
          <div class="text-2xl font-bold text-amber-600">{{ analysisStore.impactResult.transitively_affected.length }}</div>
          <div class="text-xs text-gray-500">{{ t('analysis.transitive') }}</div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center">
          <div class="text-2xl font-bold text-red-600">{{ analysisStore.impactResult.blocked_issues.length }}</div>
          <div class="text-xs text-gray-500">{{ t('analysis.cascadeBlocked') }}</div>
        </div>
      </div>

      <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">{{ t('analysis.dependencyGraphBFS') }}</h4>
        <ImpactSvgTree
          :root-id="analysisStore.impactResult.issue_id"
          :root-title="analysisStore.impactResult.issue_title"
          :root-status="analysisStore.impactResult.issue_status"
          :direct-deps="analysisStore.impactResult.directly_affected.map(d => ({ id: d.id, title: d.title, status: d.status, level: 1 }))"
          :transitive-deps="analysisStore.impactResult.transitively_affected.map(t => ({ id: t.id, title: t.title, status: t.status, level: t.level || 2 }))"
          @select-issue="onSelectIssue"
        />
      </div>

      <div v-if="analysisStore.impactResult.directly_affected.length" class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
          {{ t('analysis.directDepsDistance1') }}
        </h4>
        <div class="space-y-2">
          <div
            v-for="dep in analysisStore.impactResult.directly_affected"
            :key="dep.id"
            class="flex items-center justify-between rounded-md border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 px-3 py-2"
          >
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs font-bold text-blue-700 dark:text-blue-400">{{ dep.id }}</span>
              <span class="text-sm text-gray-800 dark:text-gray-200">{{ dep.title }}</span>
            </div>
            <span
              class="rounded px-1.5 py-0.5 text-[10px] font-bold"
              :class="statusBadgeClass(dep.status)"
            >
              {{ dep.status }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="analysisStore.impactResult.transitively_affected.length" class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
          {{ t('analysis.transitiveDepsDistance2') }}
        </h4>
        <div class="space-y-2">
          <div
            v-for="dep in analysisStore.impactResult.transitively_affected"
            :key="dep.id"
            class="flex items-center justify-between rounded-md border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 px-3 py-2"
          >
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs font-bold text-amber-700 dark:text-amber-400">{{ dep.id }}</span>
              <span class="text-sm text-gray-800 dark:text-gray-200">{{ dep.title }}</span>
              <span class="rounded bg-amber-200 px-1.5 py-0.5 text-[10px] font-bold text-amber-800 dark:bg-amber-800 dark:text-amber-200">
                L{{ dep.level }}
              </span>
            </div>
            <span
              class="rounded px-1.5 py-0.5 text-[10px] font-bold"
              :class="statusBadgeClass(dep.status)"
            >
              {{ dep.status }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="analysisStore.impactResult.blocked_issues.length" class="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10 p-4">
        <h4 class="mb-3 text-sm font-semibold text-red-700 dark:text-red-400">
          {{ t('analysis.cascadeBlockedIssues') }}
        </h4>
        <div class="space-y-2">
          <div
            v-for="blocked in analysisStore.impactResult.blocked_issues"
            :key="blocked.id"
            class="flex items-center justify-between rounded-md border border-red-200 dark:border-red-800 bg-white dark:bg-gray-800 px-3 py-2"
          >
            <div class="flex items-center gap-2">
              <svg class="h-4 w-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clip-rule="evenodd" />
              </svg>
              <span class="font-mono text-xs font-bold text-red-700 dark:text-red-400">{{ blocked.id }}</span>
              <span class="text-sm text-gray-800 dark:text-gray-200">{{ blocked.title }}</span>
            </div>
            <span
              class="rounded px-1.5 py-0.5 text-[10px] font-bold"
              :class="statusBadgeClass(blocked.status)"
            >
              {{ blocked.status }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="analysisStore.impactResult.affected_components.length" class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">{{ t('analysis.affectedComponents') }}</h4>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="comp in analysisStore.impactResult.affected_components"
            :key="comp"
            class="rounded-full bg-purple-100 px-3 py-1 text-xs font-medium text-purple-800 dark:bg-purple-900/30 dark:text-purple-300"
          >
            {{ comp }}
          </span>
        </div>
      </div>
    </div>

    <div v-else-if="selectedIssueId === ''" class="flex flex-col items-center justify-center py-16 text-gray-400">
      <svg class="mb-3 h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
      <p class="text-sm">{{ t('analysis.selectIssueToAnalyze') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useIssuesStore } from '@/stores/issuesStore'
import { useComponentsStore } from '@/stores/componentsStore'
import ImpactSvgTree from './ImpactSvgTree.vue'
import BlastRadiusSlider from './BlastRadiusSlider.vue'

const { t } = useI18n()

const analysisStore = useAnalysisStore()
const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()

const selectedIssueId = ref('')
const blastDepth = ref(3)

const depthCounts = computed(() => {
  if (!analysisStore.impactResult) return {}
  const counts: Record<number, number> = {}
  counts[1] = analysisStore.impactResult.directly_affected.length
  for (const t of analysisStore.impactResult.transitively_affected) {
    const lvl = t.level || 2
    counts[lvl] = (counts[lvl] || 0) + 1
  }
  return counts
})

onMounted(() => {
  issuesStore.fetchIssues(1, 200)
  componentsStore.fetchComponents()
})

async function analyze() {
  if (!selectedIssueId.value) return
  await analysisStore.analyzeImpact(selectedIssueId.value)
}

function onSelectIssue(id: string) {
  selectedIssueId.value = id
  analyze()
}

function riskBadgeClass(level: string) {
  const map: Record<string, string> = {
    LOW: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
    MEDIUM: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    HIGH: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
    CRITICAL: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  }
  return map[level] || map.MEDIUM
}

function statusBadgeClass(status: string) {
  const map: Record<string, string> = {
    OPEN: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    IN_PROGRESS: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
    BLOCKED: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    CLOSED: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  }
  return map[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300'
}
</script>
