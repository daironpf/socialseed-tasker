<template>
  <ModuleCard :title="t('boardModules.depTitle')">
    <div v-if="top.length === 0" class="text-sm text-gray-400">
      {{ t('issues.noDependencies') }}
    </div>

    <ul v-else class="space-y-2.5">
      <li v-for="row in top" :key="row.id" class="flex items-center gap-2">
        <span
          class="flex-shrink-0 rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-gray-600 dark:bg-gray-700 dark:text-gray-300"
        >
          {{ row.id }}
        </span>
        <span class="min-w-0 flex-1 truncate text-xs text-gray-700 dark:text-gray-300">
          {{ row.title }}
        </span>
        <span
          class="flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold"
          :class="row.chipClass"
          :title="t('boardModules.depDependents', { count: row.count })"
        >
          ×{{ row.count }}
        </span>
      </li>
    </ul>

    <div
      class="mt-3 flex items-center justify-between border-t border-gray-100 pt-3 text-[10px] uppercase tracking-wide text-gray-400 dark:border-gray-700 dark:text-gray-500"
    >
      <span>{{ t('boardModules.depLinks') }}: {{ totalEdges }}</span>
      <span :class="blockedCount > 0 ? 'text-red-600 dark:text-red-400' : ''">
        {{ t('statusDistribution.blocked') }}: {{ blockedCount }}
      </span>
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

const allIssues = computed(() => props.issues ?? issuesStore.issues)

const incoming = computed(() => {
  const map = new Map<string, number>()
  for (const issue of allIssues.value) {
    for (const dep of issue.dependencies ?? []) {
      map.set(dep, (map.get(dep) ?? 0) + 1)
    }
  }
  return map
})

const top = computed(() => {
  const byId = new Map(allIssues.value.map((i) => [i.id, i]))
  return [...incoming.value.entries()]
    .filter(([id, count]) => count > 0 && byId.has(id))
    .map(([id, count]) => ({ id, count, title: byId.get(id)!.title }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)
    .map((row) => ({
      ...row,
      chipClass:
        row.count >= 3
          ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
          : row.count === 2
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
            : 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    }))
})

const totalEdges = computed(() =>
  allIssues.value.reduce((sum, issue) => sum + (issue.dependencies?.length ?? 0), 0)
)

const blockedCount = computed(() => allIssues.value.filter((i) => i.status === 'BLOCKED').length)
</script>
