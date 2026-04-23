<template>
  <div class="flex-1 overflow-x-auto">
    <div v-if="issuesStore.loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else class="flex gap-4 p-4">
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
let refreshInterval: ReturnType<typeof setInterval> | null = null

const columns = [
  { title: 'Open', status: 'OPEN' as IssueStatus },
  { title: 'In Progress', status: 'IN_PROGRESS' as IssueStatus },
  { title: 'Blocked', status: 'BLOCKED' as IssueStatus },
  { title: 'Closed', status: 'CLOSED' as IssueStatus },
]

function issuesByStatus(status: IssueStatus) {
  return uiStore.filteredIssues.filter((i) => i.status === status)
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
  issuesStore.fetchIssues()
}

async function fetchWithFilters() {
  await issuesStore.fetchIssues({
    status: uiStore.filters.status.join(',') || undefined,
    component: uiStore.filters.component || undefined,
    project: uiStore.filters.project || undefined,
  })
}

onMounted(async () => {
  await componentsStore.fetchComponents()
  await fetchWithFilters()
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
