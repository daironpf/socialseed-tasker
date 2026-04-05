<template>
  <div class="flex-1 overflow-x-auto">
    <div v-if="issuesStore.loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else class="flex gap-4 p-4 min-w-[800px]">
      <KanbanColumn
        v-for="col in columns"
        :key="col.status"
        :title="col.title"
        :status="col.status"
        :issues="issuesByStatus(col.status)"
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

onMounted(async () => {
  await Promise.all([
    issuesStore.fetchIssues(),
    componentsStore.fetchComponents(),
  ])
  // Auto-refresh every 10 seconds
  refreshInterval = setInterval(() => {
    issuesStore.fetchIssues()
  }, 10000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

watch(() => uiStore.filters, () => {
  issuesStore.fetchIssues()
}, { deep: true })

defineExpose({ showCreateModal })
</script>
