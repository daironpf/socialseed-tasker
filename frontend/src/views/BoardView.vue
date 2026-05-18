<template>
  <div class="flex-1 overflow-x-auto">
    <div v-if="issuesStore.loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="issuesStore.error" class="flex flex-col items-center justify-center h-64 text-center">
      <div class="text-red-500 text-lg font-semibold mb-2">Error al cargar datos</div>
      <div class="text-gray-600 dark:text-gray-400 mb-4">{{ issuesStore.error }}</div>
      <button 
        @click="fetchWithFilters" 
        class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-md transition-colors"
      >
        Reintentar
      </button>
    </div>
    <div v-else class="flex flex-col h-full">
      <!-- Dashboard Summary -->
      <div class="p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <!-- Project Details -->
        <div class="p-4 border rounded-md dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <h3 class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">Proyecto</h3>
          <div v-if="currentProject">
            <p class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ currentProject.name }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ currentProject.slug }}</p>
            <p class="text-sm mt-1 text-gray-700 dark:text-gray-300">{{ currentProject.description }}</p>
          </div>
          <div v-else class="text-gray-400 dark:text-gray-500 text-sm">No hay proyecto seleccionado</div>
        </div>

        <!-- User Details -->
        <div class="p-4 border rounded-md dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <h3 class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">Usuario</h3>
          <div v-if="currentUser">
            <p class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ currentUser.username }}</p>
            <p class="text-sm text-brand-600 dark:text-brand-400 font-medium">{{ currentUser.role }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ currentUser.email }}</p>
          </div>
          <div v-else class="text-gray-400 dark:text-gray-500 text-sm">No hay datos de usuario</div>
        </div>

        <!-- Policies -->
        <div class="p-4 border rounded-md dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <h3 class="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">Políticas Activas</h3>
          <ul v-if="policies.length > 0" class="space-y-1 text-sm text-gray-700 dark:text-gray-300">
            <li v-for="policy in policies" :key="policy.id" class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full flex-shrink-0" :class="policy.is_active ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'"></span>
              <span class="truncate" :title="policy.description">{{ policy.name }}</span>
            </li>
          </ul>
          <div v-else class="text-gray-400 dark:text-gray-500 text-sm">No se encontraron políticas</div>
        </div>
      </div>

      <!-- Kanban Columns -->
      <div class="flex-1 flex gap-4 p-4 overflow-x-auto">
        <KanbanColumn
          v-for="col in columns"
          :key="col.status"
          :title="col.title"
          :status="col.status"
          :issues="issuesByStatus(col.status)"
          class="flex-1 min-w-[280px] max-w-[400px]"
          @openIssue="openIssue"
          @dropIssue="onDropIssue"
        />
      </div>
    </div>

    <div
      v-if="selectedIssue"
      class="fixed inset-0 z-40 bg-black/50 flex justify-end"
      @click.self="uiStore.setSelectedIssue(null)"
    >
      <IssueDetailView
        :issue="selectedIssue"
        @close="uiStore.setSelectedIssue(null)"
        @update="onUpdateIssue"
        @delete="onDeleteIssue"
        @close-issue="onCloseIssue"
      />
    </div>

    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-40 bg-black/50 flex items-center justify-center"
      @click.self="showCreateModal = false"
    >
      <CreateIssueModal @close="showCreateModal = false" @created="onIssueCreated" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref, watch } from 'vue'
import type { Issue, IssueStatus, IssueUpdateRequest, Policy } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
import client from '@/api/client'
import { fetchPolicies } from '@/api/policiesApi'
import { useComponentsStore } from '@/stores/componentsStore'
import { useUiStore } from '@/stores/uiStore'
import KanbanColumn from '@/components/board/KanbanColumn.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import IssueDetailView from '@/views/IssueDetailView.vue'
import CreateIssueModal from '@/components/issue/CreateIssueModal.vue'

const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()
const uiStore = useUiStore()

const showCreateModal = ref(false)
let refreshInterval: ReturnType<typeof setInterval> | null = null

const currentProject = ref<any>(null)
const currentUser = ref<any>(null)
const policies = ref<Policy[]>([])

async function fetchDashboardData() {
  try {
    policies.value = await fetchPolicies()
  } catch (e) {
    console.error('Failed to fetch policies:', e)
  }

  const projectName = uiStore.filters.project
  if (projectName) {
    try {
      const res = await client.get(`/projects/${projectName}/summary`)
      currentProject.value = res.data.data
    } catch (e) {
      console.error('Failed to fetch project summary:', e)
      try {
        const res = await client.get('/projects')
        const projects = res.data.data
        currentProject.value = projects.find((p: any) => p.name === projectName) || { name: projectName }
      } catch (e2) {
        currentProject.value = { name: projectName }
      }
    }
  } else {
    currentProject.value = null
  }

  try {
    const res = await client.get('/users')
    const users = res.data.data
    currentUser.value = users[0] || null
  } catch (e) {
    console.error('Failed to fetch users:', e)
  }
}

const columns = [
  { title: 'Open', status: 'OPEN' as IssueStatus },
  { title: 'In Progress', status: 'IN_PROGRESS' as IssueStatus },
  { title: 'Blocked', status: 'BLOCKED' as IssueStatus },
  { title: 'Closed', status: 'CLOSED' as IssueStatus },
]

function issuesByStatus(status: IssueStatus) {
  return issuesStore.issues.filter((i) => i.status === status)
}

const selectedIssue = computed(() => {
  if (!uiStore.selectedIssueId) return null
  return issuesStore.issues.find((i) => i.id === uiStore.selectedIssueId) ?? null
})

function openIssue(issue: Issue) {
  uiStore.setSelectedIssue(issue.id)
}

async function onDropIssue(issue: Issue, newStatus: IssueStatus) {
  await issuesStore.updateIssue(issue.id, { status: newStatus })
}

async function onUpdateIssue(id: string, body: IssueUpdateRequest) {
  await issuesStore.updateIssue(id, body)
}

async function onDeleteIssue(id: string) {
  const ok = await issuesStore.deleteIssue(id)
  if (ok) uiStore.setSelectedIssue(null)
}

async function onCloseIssue(id: string) {
  await issuesStore.closeIssue(id)
}

function onIssueCreated() {
  showCreateModal.value = false
  const filters = uiStore.getBackendFilters()
  issuesStore.fetchIssues(1, 100, filters)
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

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

watch(
  () => uiStore.filters,
  () => {
    fetchWithFilters()
  },
  { deep: true },
)

watch(
  () => uiStore.filters.project,
  () => {
    fetchDashboardData()
  }
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

defineExpose({ showCreateModal })
</script>
