<template>
  <div class="flex-1 overflow-x-auto">
    <div v-if="issuesStore.loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="issuesStore.error" class="flex flex-col items-center justify-center h-64 text-center">
      <div class="text-red-500 text-lg font-semibold mb-2">{{ t('common.error') }}</div>
      <div class="text-gray-600 dark:text-gray-400 mb-4">{{ issuesStore.error }}</div>
      <button 
        @click="fetchWithFilters" 
        class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-md transition-colors"
      >
        {{ t('system.refresh') }}
      </button>
    </div>
    <div v-else class="flex flex-col h-full">
      <!-- Dashboard Stats -->
      <div class="p-6 pb-4">
        <DashboardStats :issues="allIssues" />
      </div>

      <!-- Operational Pulse -->
      <div class="px-6 pb-6">
        <DashboardPulse :issues="allIssues" />
      </div>

      <!-- Project Info Bar -->
      <div class="px-6 pb-4">
        <div class="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center gap-4">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 dark:bg-brand-900/30">
              <svg class="h-5 w-5 text-brand-600 dark:text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div>
              <h2 v-if="currentProject" class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ currentProject.name }}
              </h2>
              <p v-if="currentProject" class="text-sm text-gray-500 dark:text-gray-400">
                {{ currentProject.description || currentProject.slug }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ t('policies.active') }}:</span>
            <span class="rounded-full bg-green-100 px-2.5 py-0.5 text-sm font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
              {{ policies.length }}
            </span>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="px-6 pb-6">
        <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <!-- Trend Chart -->
          <div class="lg:col-span-2">
            <TrendChart :issues="allIssues" />
          </div>

          <!-- Avg Resolution Time -->
          <div class="lg:col-span-1">
            <AvgResolutionTime :issues="allIssues" />
          </div>
        </div>

        <!-- Daily Activity & Status Distribution -->
        <div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <DailyActivityChart :issues="allIssues" />
          <StatusDistribution :issues="allIssues" />
        </div>
      </div>

      <!-- Insight Modules -->
      <div class="grid grid-cols-1 gap-6 px-6 pb-6 lg:grid-cols-3">
        <PriorityBreakdown :issues="allIssues" />
        <ComponentWorkload :issues="allIssues" />
        <NotificationsFeed />
      </div>

      <!-- Operations Modules -->
      <div class="grid grid-cols-1 gap-6 px-6 pb-6 lg:grid-cols-3">
        <AutoHealingMini />
        <SyncStatusCard />
        <BudgetMini />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Policy } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
import client from '@/api/client'
import { fetchPolicies } from '@/api/policiesApi'
import { useComponentsStore } from '@/stores/componentsStore'
import { useUiStore } from '@/stores/uiStore'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import DashboardStats from '@/components/dashboard/DashboardStats.vue'

const { t } = useI18n()
import TrendChart from '@/components/dashboard/TrendChart.vue'
import AvgResolutionTime from '@/components/dashboard/AvgResolutionTime.vue'
import DailyActivityChart from '@/components/dashboard/DailyActivityChart.vue'
import StatusDistribution from '@/components/dashboard/StatusDistribution.vue'
import DashboardPulse from '@/components/dashboard/DashboardPulse.vue'
import PriorityBreakdown from '@/components/dashboard/PriorityBreakdown.vue'
import ComponentWorkload from '@/components/dashboard/ComponentWorkload.vue'
import NotificationsFeed from '@/components/dashboard/NotificationsFeed.vue'
import AutoHealingMini from '@/components/dashboard/AutoHealingMini.vue'
import SyncStatusCard from '@/components/dashboard/SyncStatusCard.vue'
import BudgetMini from '@/components/dashboard/BudgetMini.vue'

const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()
const uiStore = useUiStore()

const currentProject = ref<{ name: string; description?: string; slug?: string } | null>(null)
const policies = ref<Policy[]>([])
const allIssues = computed(() => issuesStore.issues)

async function fetchDashboardData() {
  try {
    policies.value = await fetchPolicies()
  } catch {
    // policies fetch failed
  }

  const projectName = uiStore.filters.project
  if (projectName) {
    try {
      const res = await client.get(`/projects/${projectName}/summary`)
      currentProject.value = res.data.data
    } catch {
      // project summary fetch failed
      try {
        const res = await client.get('/projects')
        const projects = res.data.data
        currentProject.value = projects.find((p: { name: string }) => p.name === projectName) || { name: projectName }
      } catch (e2) {
        currentProject.value = { name: projectName }
      }
    }
  } else {
    currentProject.value = null
  }
}

async function fetchWithFilters() {
  const filters = uiStore.getBackendFilters()
  await issuesStore.fetchIssues(1, 100, filters)
}

onMounted(async () => {
  await componentsStore.fetchComponents()
  await fetchWithFilters()
  await fetchDashboardData()
})

watch(
  () => [uiStore.filters.status, uiStore.filters.priority, uiStore.filters.component, uiStore.filters.project],
  () => {
    fetchWithFilters()
    fetchDashboardData()
  },
  { deep: true },
)

watch(
  () => componentsStore.projects,
  (projects) => {
    if (projects.length > 0 && !uiStore.filters.project) {
      uiStore.setFilter('project', projects[0])
    }
  },
  { immediate: true },
)
</script>
