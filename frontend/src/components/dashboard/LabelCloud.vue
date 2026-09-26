<template>
  <ModuleCard :title="t('boardModules.labelsTitle')">
    <div v-if="topLabels.length === 0" class="text-sm text-gray-400">
      {{ t('boardModules.labelsEmpty') }}
    </div>
    <div v-else class="flex flex-wrap items-baseline gap-x-3 gap-y-1.5">
      <span
        v-for="(l, idx) in topLabels"
        :key="l.label"
        class="cursor-default font-medium leading-tight transition-opacity hover:opacity-70"
        :class="PALETTE[idx % PALETTE.length]"
        :style="{ fontSize: `${l.size}px` }"
        :title="`${l.label} · ${l.count}`"
      >
        {{ l.label }}
        <span class="text-[10px] font-normal opacity-60">{{ l.count }}</span>
      </span>
    </div>
    <p class="mt-3 text-[10px] uppercase tracking-wide text-gray-400 dark:text-gray-500">
      {{ t('boardModules.labelsFooter', { count: uniqueCount }) }}
    </p>
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

const PALETTE = [
  'text-brand-600 dark:text-brand-400',
  'text-blue-600 dark:text-blue-400',
  'text-purple-600 dark:text-purple-400',
  'text-amber-600 dark:text-amber-400',
  'text-rose-600 dark:text-rose-400',
  'text-cyan-600 dark:text-cyan-400',
  'text-gray-700 dark:text-gray-300',
]

const allIssues = computed(() => props.issues ?? issuesStore.issues)

const uniqueCount = computed(() => {
  const set = new Set<string>()
  for (const issue of allIssues.value) for (const l of issue.labels ?? []) set.add(l)
  return set.size
})

const topLabels = computed(() => {
  const counts = new Map<string, number>()
  for (const issue of allIssues.value) {
    for (const l of issue.labels ?? []) counts.set(l, (counts.get(l) ?? 0) + 1)
  }
  const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 18)
  const max = sorted.length > 0 ? sorted[0][1] : 1
  return sorted.map(([label, count]) => ({
    label,
    count,
    size: 11 + Math.round((count / max) * 13),
  }))
})
</script>
