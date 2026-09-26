<template>
  <ModuleCard :title="t('boardModules.matrixTitle')">
    <div v-if="allIssues.length === 0" class="text-sm text-gray-400">
      {{ t('boardModules.matrixNoData') }}
    </div>
    <div v-else class="overflow-x-auto">
      <div
        class="grid min-w-[420px] gap-1.5"
        :style="{ gridTemplateColumns: 'auto repeat(5, minmax(0, 1fr))' }"
      >
        <div />
        <div
          v-for="s in STATUSES"
          :key="s"
          class="pb-1 text-center text-[10px] font-medium text-gray-400 dark:text-gray-500"
        >
          {{ statusLabel(s) }}
        </div>

        <template v-for="p in PRIORITIES" :key="p">
          <div class="flex items-center gap-1.5 pr-2 text-xs font-semibold" :class="PRIORITY_STYLE[p].text">
            <span class="h-2 w-2 flex-shrink-0 rounded-full" :class="PRIORITY_STYLE[p].dot" />
            {{ p }}
          </div>
          <div
            v-for="s in STATUSES"
            :key="s"
            class="flex h-8 items-center justify-center rounded-lg text-xs font-bold"
            :style="cellStyle(p, counts[p][s])"
          >
            {{ counts[p][s] || '' }}
          </div>
        </template>
      </div>
    </div>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'
import { IssuePriority, IssueStatus } from '@/types'
import ModuleCard from './ModuleCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'

const { t } = useI18n()

const props = defineProps<{ issues?: Issue[] }>()

const issuesStore = useIssuesStore()

const PRIORITIES: IssuePriority[] = [
  IssuePriority.CRITICAL,
  IssuePriority.HIGH,
  IssuePriority.MEDIUM,
  IssuePriority.LOW,
]

const STATUSES: IssueStatus[] = [
  IssueStatus.OPEN,
  IssueStatus.IN_PROGRESS,
  IssueStatus.WAITING_HUMAN_APPROVAL,
  IssueStatus.BLOCKED,
  IssueStatus.CLOSED,
]

const STATUS_KEY: Record<IssueStatus, string> = {
  OPEN: 'statusDistribution.open',
  IN_PROGRESS: 'statusDistribution.inProgress',
  WAITING_HUMAN_APPROVAL: 'statusDistribution.waitingApproval',
  BLOCKED: 'statusDistribution.blocked',
  CLOSED: 'statusDistribution.closed',
}

const PRIORITY_STYLE: Record<IssuePriority, { dot: string; text: string }> = {
  CRITICAL: { dot: 'bg-red-500', text: 'text-red-600 dark:text-red-400' },
  HIGH: { dot: 'bg-orange-400', text: 'text-orange-600 dark:text-orange-400' },
  MEDIUM: { dot: 'bg-blue-500', text: 'text-blue-600 dark:text-blue-400' },
  LOW: { dot: 'bg-gray-400', text: 'text-gray-500 dark:text-gray-400' },
}

const PRIORITY_RGB: Record<IssuePriority, [number, number, number]> = {
  CRITICAL: [239, 68, 68],
  HIGH: [249, 115, 22],
  MEDIUM: [59, 130, 246],
  LOW: [156, 163, 175],
}

const allIssues = computed(() => props.issues ?? issuesStore.issues)

const counts = computed(() => {
  const grid = {} as Record<IssuePriority, Record<IssueStatus, number>>
  for (const p of PRIORITIES) {
    grid[p] = {} as Record<IssueStatus, number>
    for (const s of STATUSES) grid[p][s] = 0
  }
  for (const issue of allIssues.value) {
    if (grid[issue.priority] && grid[issue.priority][issue.status] !== undefined) {
      grid[issue.priority][issue.status]++
    }
  }
  return grid
})

const maxCell = computed(() => {
  let max = 1
  for (const p of PRIORITIES) {
    for (const s of STATUSES) max = Math.max(max, counts.value[p][s])
  }
  return max
})

function statusLabel(s: IssueStatus): string {
  return t(STATUS_KEY[s])
}

function cellStyle(p: IssuePriority, n: number): Record<string, string> {
  if (n === 0) {
    return { backgroundColor: 'rgba(148, 163, 184, 0.07)', color: 'rgba(148, 163, 184, 0.75)' }
  }
  const alpha = 0.15 + (n / maxCell.value) * 0.7
  const [r, g, b] = PRIORITY_RGB[p]
  return {
    backgroundColor: `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(2)})`,
    color: alpha > 0.55 ? '#ffffff' : `rgb(${r}, ${g}, ${b})`,
  }
}
</script>
