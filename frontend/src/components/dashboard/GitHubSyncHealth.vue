<template>
  <ModuleCard :title="t('githubSync.title')">
    <template #action>
      <span
        class="text-xs font-semibold"
        :class="
          pct >= 80
            ? 'text-brand-600 dark:text-brand-400'
            : 'text-amber-600 dark:text-amber-400'
        "
      >
        {{ pct }}% {{ t('boardModules.pctSynced') }}
      </span>
    </template>

    <div v-if="total === 0" class="text-sm text-gray-400">
      {{ t('boardModules.syncNoData') }}
    </div>

    <div v-else>
      <div class="flex h-2.5 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
        <div class="bg-brand-500" :style="{ width: `${pcts.SYNCED}%` }" />
        <div class="bg-amber-400" :style="{ width: `${pcts.PENDING_PUSH}%` }" />
        <div class="bg-red-500" :style="{ width: `${pcts.ERROR}%` }" />
      </div>

      <ul class="mt-3 space-y-2">
        <li
          v-for="row in rows"
          :key="row.status"
          class="flex items-center justify-between text-xs"
        >
          <span class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
            <span class="h-2 w-2 rounded-full" :class="row.dot" />
            {{ row.label }}
          </span>
          <span class="font-semibold text-gray-900 dark:text-white">
            {{ row.count }}
            <span class="font-normal text-gray-400">({{ row.pct }}%)</span>
          </span>
        </li>
      </ul>

      <p
        class="mt-3 border-t border-gray-100 pt-2.5 text-[10px] text-gray-400 dark:border-gray-700 dark:text-gray-500"
      >
        {{ t('githubSync.lastSynced') }}: {{ lastSynced }}
      </p>
    </div>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'
import ModuleCard from './ModuleCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'

const { t, locale } = useI18n()

const props = defineProps<{ issues?: Issue[] }>()

const issuesStore = useIssuesStore()

const STATUSES = ['SYNCED', 'PENDING_PUSH', 'ERROR'] as const

const DOTS: Record<string, string> = {
  SYNCED: 'bg-brand-500',
  PENDING_PUSH: 'bg-amber-400',
  ERROR: 'bg-red-500',
}

const allIssues = computed(() => props.issues ?? issuesStore.issues)

const syncedIssues = computed(() => allIssues.value.filter((i) => i.github_sync))

const total = computed(() => syncedIssues.value.length)

const counts = computed(() => {
  const map: Record<string, number> = { SYNCED: 0, PENDING_PUSH: 0, ERROR: 0 }
  for (const issue of syncedIssues.value) {
    const status = issue.github_sync!.sync_status
    if (status in map) map[status]++
  }
  return map
})

const pcts = computed(() => {
  const base = Math.max(1, total.value)
  return {
    SYNCED: (counts.value.SYNCED / base) * 100,
    PENDING_PUSH: (counts.value.PENDING_PUSH / base) * 100,
    ERROR: (counts.value.ERROR / base) * 100,
  }
})

const pct = computed(() =>
  total.value === 0 ? 0 : Math.round((counts.value.SYNCED / total.value) * 100)
)

const rows = computed(() =>
  STATUSES.map((status) => ({
    status,
    label: t(`githubSync.status.${status}`),
    dot: DOTS[status],
    count: counts.value[status],
    pct: Math.round(pcts.value[status]),
  }))
)

const lastSynced = computed(() => {
  const stamps = syncedIssues.value
    .map((i) => i.github_sync!.last_synced_at)
    .filter(Boolean)
    .sort()
  if (stamps.length === 0) return '—'
  return new Date(stamps[stamps.length - 1]).toLocaleString(locale.value, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
})
</script>
