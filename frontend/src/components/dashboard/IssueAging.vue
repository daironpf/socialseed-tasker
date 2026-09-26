<template>
  <ModuleCard :title="t('boardModules.agingTitle')">
    <div v-if="openIssues.length === 0" class="text-sm text-gray-400">
      {{ t('boardModules.noOpenIssues') }}
    </div>
    <div v-else class="space-y-3">
      <div v-for="b in buckets" :key="b.label" class="flex items-center gap-3">
        <span class="w-16 flex-shrink-0 text-xs font-medium text-gray-500 dark:text-gray-400">
          {{ b.label }}
        </span>
        <div class="h-2 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
          <div
            class="h-full rounded-full transition-all"
            :class="b.color"
            :style="{ width: `${b.pct}%` }"
          />
        </div>
        <span class="w-6 flex-shrink-0 text-right text-xs font-semibold text-gray-700 dark:text-gray-300">
          {{ b.count }}
        </span>
      </div>
      <div class="flex items-center justify-between border-t border-gray-100 pt-3 dark:border-gray-700">
        <div>
          <p class="text-lg font-bold text-gray-900 dark:text-white">{{ avgAge }}d</p>
          <p class="text-[10px] uppercase tracking-wide text-gray-400 dark:text-gray-500">
            {{ t('boardModules.agingAvg') }}
          </p>
        </div>
        <div class="text-right">
          <p class="text-lg font-bold text-red-600 dark:text-red-400">{{ oldestAge }}d</p>
          <p class="text-[10px] uppercase tracking-wide text-gray-400 dark:text-gray-500">
            {{ t('boardModules.agingOldest') }}
          </p>
        </div>
      </div>
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

const DAY = 86400000

const DEFS = [
  { max: 3, key: 'boardModules.agingB1', color: 'bg-brand-500' },
  { max: 7, key: 'boardModules.agingB2', color: 'bg-amber-400' },
  { max: 14, key: 'boardModules.agingB3', color: 'bg-orange-500' },
  { max: Number.POSITIVE_INFINITY, key: 'boardModules.agingB4', color: 'bg-red-500' },
]

const openIssues = computed(() =>
  (props.issues ?? issuesStore.issues).filter((i) => i.status !== 'CLOSED')
)

function ageOf(issue: Issue): number {
  return Math.max(0, Math.floor((Date.now() - new Date(issue.created_at).getTime()) / DAY))
}

const ages = computed(() => openIssues.value.map(ageOf))

const avgAge = computed(() => {
  if (ages.value.length === 0) return 0
  return Math.round(ages.value.reduce((a, b) => a + b, 0) / ages.value.length)
})

const oldestAge = computed(() => (ages.value.length === 0 ? 0 : Math.max(...ages.value)))

const buckets = computed(() => {
  const counts = DEFS.map((d) => ages.value.filter((a) => a <= d.max).length)
  const max = Math.max(1, ...counts)
  return DEFS.map((d, idx) => ({
    label: t(d.key),
    color: d.color,
    count: counts[idx],
    pct: Math.round((counts[idx] / max) * 100),
  }))
})
</script>
