<template>
  <ModuleCard :title="t('boardModules.componentWorkload')">
    <div v-if="rows.length === 0" class="text-sm text-gray-400">
      {{ t('boardModules.noOpenIssues') }}
    </div>
    <div v-else class="space-y-3">
      <div v-for="row in rows" :key="row.id" class="flex items-center gap-3">
        <span class="w-28 flex-shrink-0 truncate text-xs font-medium text-gray-700 dark:text-gray-300" :title="row.name">
          {{ row.name }}
        </span>
        <div class="h-2 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
          <div
            class="h-full rounded-full bg-brand-500 transition-all"
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
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'
import ModuleCard from './ModuleCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'
import { useComponentsStore } from '@/stores/componentsStore'

const { t } = useI18n()

const props = defineProps<{ issues?: Issue[] }>()

const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()

const rows = computed(() => {
  const counts = new Map<string, number>()
  for (const issue of props.issues ?? issuesStore.issues) {
    if (issue.status === 'CLOSED' || !issue.component_id) continue
    counts.set(issue.component_id, (counts.get(issue.component_id) ?? 0) + 1)
  }
  const max = Math.max(1, ...counts.values())
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([id, count]) => ({
      id,
      count,
      name: componentsStore.components.find((c) => c.id === id)?.name ?? id,
      pct: Math.round((count / max) * 100),
    }))
})

onMounted(() => {
  if (componentsStore.components.length === 0) {
    componentsStore.fetchComponents().catch(() => undefined)
  }
})
</script>
