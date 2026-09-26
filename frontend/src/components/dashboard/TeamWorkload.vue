<template>
  <ModuleCard :title="t('boardModules.teamTitle')">
    <template #action>
      <span
        v-if="unassigned > 0"
        class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
      >
        {{ t('issues.unassigned') }}: {{ unassigned }}
      </span>
    </template>

    <div v-if="rows.length === 0" class="text-sm text-gray-400">
      {{ t('boardModules.noOpenIssues') }}
    </div>

    <ul v-else class="space-y-3">
      <li v-for="row in rows" :key="row.id" class="flex items-center gap-3">
        <span
          class="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 text-sm dark:bg-gray-700"
        >
          {{ row.avatar }}
        </span>
        <div class="min-w-0 flex-1">
          <div class="flex items-center justify-between gap-2">
            <span class="flex min-w-0 items-center gap-1.5">
              <span class="truncate text-xs font-semibold text-gray-900 dark:text-white">
                {{ row.name }}
              </span>
              <span
                v-if="row.badge"
                class="flex-shrink-0 rounded px-1 text-[9px] font-bold uppercase"
                :class="row.badgeClass"
              >
                {{ row.badge }}
              </span>
            </span>
            <span class="flex-shrink-0 text-xs font-bold text-gray-700 dark:text-gray-300">
              {{ row.open }}
              <span class="text-[10px] font-normal text-gray-400">/{{ row.total }}</span>
            </span>
          </div>
          <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
            <div
              class="h-full rounded-full"
              :class="row.type === 'agent' ? 'bg-brand-500' : 'bg-blue-500'"
              :style="{ width: `${row.pct}%` }"
            />
          </div>
        </div>
      </li>
    </ul>

    <div
      class="mt-3 flex items-center justify-between border-t border-gray-100 pt-3 text-[10px] uppercase tracking-wide text-gray-400 dark:border-gray-700 dark:text-gray-500"
    >
      <span>{{ t('users.humans') }}: {{ usersStore.humans.length }}</span>
      <span>{{ t('users.aiAgents') }}: {{ usersStore.agents.length }}</span>
    </div>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'
import ModuleCard from './ModuleCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'
import { useUsersStore } from '@/stores/usersStore'

const { t } = useI18n()

const props = defineProps<{ issues?: Issue[] }>()

const issuesStore = useIssuesStore()
const usersStore = useUsersStore()

onMounted(() => {
  if (usersStore.users.length === 0) {
    usersStore.fetchUsers().catch(() => undefined)
  }
})

const allIssues = computed(() => props.issues ?? issuesStore.issues)

const unassigned = computed(() => allIssues.value.filter((i) => !i.assignee).length)

const rows = computed(() => {
  const stats = new Map<string, { open: number; total: number }>()
  for (const issue of allIssues.value) {
    if (!issue.assignee) continue
    const entry = stats.get(issue.assignee) ?? { open: 0, total: 0 }
    entry.total++
    if (issue.status !== 'CLOSED') entry.open++
    stats.set(issue.assignee, entry)
  }
  const maxOpen = Math.max(1, ...[...stats.values()].map((s) => s.open))
  return [...stats.entries()]
    .map(([assignee, stat]) => {
      const user = usersStore.users.find((u) => u.id === assignee)
      const isAgent = user?.type === 'agent'
      return {
        id: assignee,
        name: user?.username ?? assignee.slice(0, 8),
        avatar: user?.avatar ?? '?',
        type: user?.type ?? 'human',
        badge: user ? t(isAgent ? 'users.aiBadge' : 'users.humanBadge') : '',
        badgeClass: isAgent
          ? 'bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300'
          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
        open: stat.open,
        total: stat.total,
        pct: Math.round((stat.open / maxOpen) * 100),
      }
    })
    .sort((a, b) => b.open - a.open || b.total - a.total)
    .slice(0, 6)
})
</script>
