<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <StatsCard
      :title="t('boardModules.agentsWorking')"
      :value="agentsWorking"
      :subtitle="t('boardModules.agentsSubtitle', { count: activeAgents })"
      color="purple"
      icon-path="M9 3v2m6-2v2M9 19v2m6-2v2M4 9h16M4 15h16M8 6h8v12H8z"
    />

    <StatsCard
      :title="t('boardModules.hitlPending')"
      :value="hitlStore.pendingCount"
      :subtitle="t('boardModules.hitlSubtitle', { count: hitlStore.urgentPendingCount })"
      color="orange"
      icon-path="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
    />

    <StatsCard
      :title="t('boardModules.slaRisk')"
      :value="sla.total"
      :subtitle="t('boardModules.slaSubtitle', { count: sla.breached })"
      color="red"
      icon-path="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
    />

    <StatsCard
      :title="t('boardModules.unreadNotifications')"
      :value="notificationsStore.unreadCount"
      :subtitle="t('boardModules.unreadSubtitle', { count: emergencyUnread })"
      color="blue"
      icon-path="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'
import { SLA_HOURS } from '@/types/analytics'
import StatsCard from './StatsCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'
import { useUsersStore } from '@/stores/usersStore'
import { useHitlStore } from '@/stores/hitlStore'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { SEVERITY_GROUPS } from '@/types/notifications'

const { t } = useI18n()

const props = defineProps<{ issues?: Issue[] }>()

const issuesStore = useIssuesStore()
const usersStore = useUsersStore()
const hitlStore = useHitlStore()
const notificationsStore = useNotificationsStore()

const agentsWorking = computed(
  () => (props.issues ?? issuesStore.issues).filter((i) => i.agent_working).length
)

const activeAgents = computed(() => usersStore.activeAgents.length)

const sla = computed(() => {
  let breached = 0
  let atRisk = 0
  for (const issue of props.issues ?? issuesStore.issues) {
    if (issue.status === 'CLOSED') continue
    const limit = SLA_HOURS[issue.priority] ?? 72
    const ageHours = (Date.now() - new Date(issue.created_at).getTime()) / 3_600_000
    if (ageHours > limit) breached++
    else if (ageHours > limit * 0.8) atRisk++
  }
  return { breached, atRisk, total: breached + atRisk }
})

const emergencyUnread = computed(() => {
  const emergencyCategories = SEVERITY_GROUPS.emergency
  return notificationsStore.notifications.filter(
    (n) => !n.read && emergencyCategories.includes(n.category)
  ).length
})

onMounted(() => {
  if (usersStore.users.length === 0) {
    usersStore.fetchUsers().catch(() => undefined)
  }
})
</script>
