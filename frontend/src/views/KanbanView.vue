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
    <div v-else-if="issuesStore.filteredIssues.length === 0" class="flex flex-col items-center justify-center h-64 text-center">
      <svg class="h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-1">{{ t('issues.noProjectIssues') }}</h3>
      <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('issues.noProjectIssuesHint') }}</p>
    </div>
    <div v-else class="flex flex-col h-full p-6">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('header.kanban') }}</h1>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ issuesStore.filteredIssues.length }} {{ t('issues.title').toLowerCase() }}
          </span>
          <button
            class="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
            @click="showCreateModal = true"
          >
            {{ t('issues.newIssue') }}
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

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showDeleteConfirm = false"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('issues.delete') }}</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">{{ t('issues.deleteConfirm') }}</p>
        <div class="flex justify-end gap-2">
          <button @click="showDeleteConfirm = false" class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700">
            {{ t('common.cancel') }}
          </button>
          <button @click="confirmDeleteIssue" class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
            {{ t('issues.delete') }}
          </button>
        </div>
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
import { useI18n } from 'vue-i18n'
import type { Issue, IssueStatus, IssueUpdateRequest } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
import { useComponentsStore } from '@/stores/componentsStore'
import { useUiStore } from '@/stores/uiStore'
import KanbanColumn from '@/components/board/KanbanColumn.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import IssueDetailView from '@/views/IssueDetailView.vue'
import CreateIssueModal from '@/components/issue/CreateIssueModal.vue'

const { t } = useI18n()

const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()
const uiStore = useUiStore()

const showCreateModal = ref(false)
const showDeleteConfirm = ref(false)
const deleteTargetId = ref('')

function deleteIssue(id: string) {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

async function confirmDeleteIssue() {
  const ok = await issuesStore.deleteIssue(deleteTargetId.value)
  if (ok) uiStore.setSelectedIssue(null)
  uiStore.simulateSync()
  showDeleteConfirm.value = false
  deleteTargetId.value = ''
}

const columns = computed(() => [
  { title: t('issues.open'), status: 'OPEN' as IssueStatus },
  { title: t('issues.inProgress'), status: 'IN_PROGRESS' as IssueStatus },
  { title: t('issues.blocked'), status: 'BLOCKED' as IssueStatus },
  { title: t('issues.closed'), status: 'CLOSED' as IssueStatus },
])

function issuesByStatus(status: IssueStatus) {
  return issuesStore.filteredIssues.filter((i) => i.status === status)
}

const selectedIssue = computed(() => {
  if (!uiStore.selectedIssueId) return null
  return issuesStore.filteredIssues.find((i) => i.id === uiStore.selectedIssueId) ?? null
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
  uiStore.simulateSync()
}

async function onUpdateIssue(id: string, body: IssueUpdateRequest) {
  await issuesStore.updateIssue(id, body)
  uiStore.simulateSync()
}

function onDeleteIssue(id: string) {
  deleteIssue(id)
}

async function onCloseIssue(id: string) {
  await issuesStore.closeIssue(id)
  uiStore.simulateSync()
}

function onIssueCreated() {
  showCreateModal.value = false
  uiStore.simulateSync()
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
