<template>
  <ModuleCard :title="t('boardModules.complianceTitle')">
    <div v-if="govIssues.length === 0" class="text-sm text-gray-400">
      {{ t('boardModules.govNoData') }}
    </div>

    <div v-else class="flex items-center gap-4">
      <div class="relative h-24 w-24 flex-shrink-0">
        <svg viewBox="0 0 80 80" class="h-24 w-24 -rotate-90">
          <circle
            cx="40"
            cy="40"
            r="32"
            fill="none"
            stroke-width="8"
            class="stroke-gray-100 dark:stroke-gray-700"
          />
          <circle
            cx="40"
            cy="40"
            r="32"
            fill="none"
            stroke-width="8"
            stroke-linecap="round"
            :stroke-dasharray="CIRC"
            :stroke-dashoffset="offset"
            :style="{ stroke: ringColor }"
          />
        </svg>
        <div class="absolute inset-0 flex items-center justify-center">
          <span class="text-xl font-bold text-gray-900 dark:text-white">{{ pct }}%</span>
        </div>
      </div>

      <ul class="min-w-0 flex-1 space-y-2">
        <li v-for="row in rows" :key="row.key" class="flex items-center justify-between gap-2">
          <span class="flex min-w-0 items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
            <span class="h-2 w-2 flex-shrink-0 rounded-full" :class="row.dot" />
            <span class="truncate">{{ row.label }}</span>
          </span>
          <span class="flex-shrink-0 text-xs font-bold" :class="row.text">{{ row.count }}</span>
        </li>
      </ul>
    </div>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'
import ModuleCard from './ModuleCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'

const { t } = useI18n()

const props = defineProps<{ issues?: Issue[] }>()

const issuesStore = useIssuesStore()

const CIRC = 2 * Math.PI * 32

const allIssues = computed(() => props.issues ?? issuesStore.issues)

const govIssues = computed(() => allIssues.value.filter((i) => i.governance))

const compliant = computed(() =>
  govIssues.value.filter(
    (i) =>
      i.governance!.has_solution_summary &&
      i.governance!.has_file_impact &&
      i.governance!.policy_violations.length === 0
  ).length
)

const pct = computed(() =>
  govIssues.value.length === 0
    ? 0
    : Math.round((compliant.value / govIssues.value.length) * 100)
)

const offset = computed(() => CIRC * (1 - pct.value / 100))

const ringColor = computed(() => {
  if (pct.value >= 80) return '#22c55e'
  if (pct.value >= 60) return '#f59e0b'
  return '#ef4444'
})

const rows = computed(() => [
  {
    key: 'violations',
    label: t('governance.violatedPolicies'),
    count: govIssues.value.filter((i) => i.governance!.policy_violations.length > 0).length,
    dot: 'bg-red-500',
    text: 'text-red-600 dark:text-red-400',
  },
  {
    key: 'summary',
    label: t('boardModules.govMissingSummary'),
    count: govIssues.value.filter((i) => !i.governance!.has_solution_summary).length,
    dot: 'bg-amber-500',
    text: 'text-amber-600 dark:text-amber-400',
  },
  {
    key: 'files',
    label: t('boardModules.govMissingFiles'),
    count: govIssues.value.filter((i) => !i.governance!.has_file_impact).length,
    dot: 'bg-blue-500',
    text: 'text-blue-600 dark:text-blue-400',
  },
])
</script>
