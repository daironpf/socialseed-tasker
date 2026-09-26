<template>
  <ModuleCard :title="t('boardModules.priorityBreakdown')">
    <div v-if="totalOpen === 0" class="text-sm text-gray-400">
      {{ t('boardModules.noOpenIssues') }}
    </div>
    <div v-else class="space-y-3">
      <div v-for="row in rows" :key="row.priority" class="flex items-center gap-3">
        <span class="w-16 flex-shrink-0 text-xs font-semibold" :class="row.textClass">
          {{ row.priority }}
        </span>
        <div class="h-2 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
          <div
            class="h-full rounded-full transition-all"
            :class="row.barClass"
            :style="{ width: `${row.pct}%` }"
          />
        </div>
        <span class="w-6 flex-shrink-0 text-right text-xs font-semibold text-gray-700 dark:text-gray-300">
          {{ row.count }}
        </span>
      </div>
    </div>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'
import { IssuePriority } from '@/types'
import ModuleCard from './ModuleCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'

const { t } = useI18n()

const props = defineProps<{ issues?: Issue[] }>()

const issuesStore = useIssuesStore()

const ORDER: IssuePriority[] = [
  IssuePriority.CRITICAL,
  IssuePriority.HIGH,
  IssuePriority.MEDIUM,
  IssuePriority.LOW,
]

const STYLES: Record<IssuePriority, { bar: string; text: string }> = {
  CRITICAL: { bar: 'bg-red-500', text: 'text-red-600 dark:text-red-400' },
  HIGH: { bar: 'bg-orange-400', text: 'text-orange-600 dark:text-orange-400' },
  MEDIUM: { bar: 'bg-blue-500', text: 'text-blue-600 dark:text-blue-400' },
  LOW: { bar: 'bg-gray-400', text: 'text-gray-500 dark:text-gray-400' },
}

const openIssues = computed(() =>
  (props.issues ?? issuesStore.issues).filter((i) => i.status !== 'CLOSED')
)

const totalOpen = computed(() => openIssues.value.length)

const rows = computed(() => {
  const counts = new Map<IssuePriority, number>(ORDER.map((p) => [p, 0]))
  for (const issue of openIssues.value) {
    counts.set(issue.priority, (counts.get(issue.priority) ?? 0) + 1)
  }
  const max = Math.max(1, ...counts.values())
  return ORDER.map((priority) => ({
    priority,
    count: counts.get(priority) ?? 0,
    pct: Math.round(((counts.get(priority) ?? 0) / max) * 100),
    barClass: STYLES[priority].bar,
    textClass: STYLES[priority].text,
  }))
})
</script>
