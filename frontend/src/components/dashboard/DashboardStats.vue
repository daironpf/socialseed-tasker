<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <StatsCard
      :title="t('dashboardStats.totalIssues')"
      :value="stats.totalIssues"
      :subtitle="t('dashboardStats.totalIssuesSubtitle')"
      color="blue"
      icon-path="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
    />

    <StatsCard
      :title="t('dashboardStats.resolvedThisMonth')"
      :value="stats.resolvedThisMonth"
      :subtitle="t('dashboardStats.resolvedThisMonthSubtitle')"
      color="green"
      icon-path="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
    />

    <StatsCard
      :title="t('dashboardStats.inProgress')"
      :value="stats.inProgress"
      :subtitle="t('dashboardStats.inProgressSubtitle')"
      color="orange"
      icon-path="M13 10V3L4 14h7v7l9-11h-7z"
    />

    <StatsCard
      :title="t('dashboardStats.blocked')"
      :value="stats.blocked"
      :subtitle="t('dashboardStats.blockedSubtitle')"
      color="red"
      icon-path="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import StatsCard from './StatsCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'
import type { Issue } from '@/types'

const { t } = useI18n()

const props = defineProps<{ issues?: Issue[] }>()

const issuesStore = useIssuesStore()

const stats = computed(() => {
  const issues = props.issues ?? issuesStore.issues
  const now = new Date()
  const thisMonth = now.getMonth()
  const thisYear = now.getFullYear()

  const resolvedThisMonth = issues.filter((i) => {
    if (i.status !== 'CLOSED' || !i.closed_at) return false
    const closedDate = new Date(i.closed_at)
    return closedDate.getMonth() === thisMonth && closedDate.getFullYear() === thisYear
  }).length

  return {
    totalIssues: issues.length,
    resolvedThisMonth,
    inProgress: issues.filter((i) => i.status === 'IN_PROGRESS').length,
    blocked: issues.filter((i) => i.status === 'BLOCKED').length,
  }
})
</script>
