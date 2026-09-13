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
    <div v-else class="flex flex-col h-full p-6">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Kanban Board</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">Arrastra las tarjetas para cambiar su estado</p>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ issuesStore.issues.length }} issues
          </span>
          <button
            class="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
            @click="showCreateModal = true"
          >
            + Nuevo Issue
          </button>
        </div>
      </div>

      <!-- Kanban Columns -->
      <div class="flex-1 flex gap-4 overflow-x-auto">
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

    <!-- Issue Detail Modal -->
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

    <!-- Create Issue Modal -->
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
import { onMounted, computed, ref, watch } from 'vue'
import type { Issue, IssueStatus, IssueUpdateRequest } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
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
  const update: IssueUpdateRequest = { status: newStatus }
  if (newStatus === 'CLOSED') {
    update.closed_at = new Date().toISOString()
  } else if (issue.status === 'CLOSED') {
    update.closed_at = null
  }
  await issuesStore.updateIssue(issue.id, update)
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
})

watch(
  () => [uiStore.filters.status, uiStore.filters.priority, uiStore.filters.component, uiStore.filters.project],
  () => {
    fetchWithFilters()
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

defineExpose({ showCreateModal })
</script>
