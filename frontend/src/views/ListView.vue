<template>
  <div class="flex-1 overflow-auto p-4">
    <div v-if="issuesStore.loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else>
      <!-- Header -->
      <div class="mb-4 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('issues.title') }}</h1>
        <div class="flex items-center gap-2">
          <div class="relative" ref="exportDropdownRef">
            <button
              class="flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              @click="showExportMenu = !showExportMenu"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {{ t('export.title') }}
            </button>
            <Teleport to="body">
              <Transition
                enter-active-class="transition duration-100 ease-out"
                enter-from-class="scale-95 opacity-0"
                enter-to-class="scale-100 opacity-100"
                leave-active-class="transition duration-75 ease-in"
                leave-from-class="scale-100 opacity-100"
                leave-to-class="scale-95 opacity-0"
              >
                <div
                  v-if="showExportMenu"
                  class="fixed z-50 w-44 rounded-xl border border-gray-200 bg-white py-1 shadow-xl dark:border-gray-700 dark:bg-gray-900"
                  :style="{ top: '50px', right: '180px' }"
                >
                  <button class="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800" @click="downloadCSV">
                    <span class="rounded bg-green-100 px-1.5 py-0.5 text-[10px] font-bold text-green-700 dark:bg-green-900/30 dark:text-green-300">CSV</span>
                    {{ t('export.downloadCSV') }}
                  </button>
                  <button class="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800" @click="downloadJSON">
                    <span class="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">JSON</span>
                    {{ t('export.downloadJSON') }}
                  </button>
                </div>
              </Transition>
            </Teleport>
          </div>
          <button
            class="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
            @click="showCreateModal = true"
          >
            {{ t('issues.newIssue') }}
          </button>
        </div>
      </div>

      <div class="mb-4 flex items-center gap-2">
        <input
          v-model="search"
          :placeholder="t('issues.search')"
          :aria-label="t('issues.search')"
          class="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
        <select
          v-model="statusFilter"
          :aria-label="t('issues.allStatus')"
          class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        >
          <option value="">{{ t('issues.allStatus') }}</option>
          <option value="OPEN">{{ t('issues.open') }}</option>
          <option value="IN_PROGRESS">{{ t('issues.inProgress') }}</option>
          <option value="BLOCKED">{{ t('issues.blocked') }}</option>
          <option value="CLOSED">{{ t('issues.closed') }}</option>
        </select>
        <select
          v-model="priorityFilter"
          :aria-label="t('issues.allPriority')"
          class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        >
          <option value="">{{ t('issues.allPriority') }}</option>
          <option value="CRITICAL">{{ t('issues.critical') }}</option>
          <option value="HIGH">{{ t('issues.high') }}</option>
          <option value="MEDIUM">{{ t('issues.medium') }}</option>
          <option value="LOW">{{ t('issues.low') }}</option>
        </select>
        <select
          v-model="componentFilter"
          :aria-label="t('issues.allComponents')"
          class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        >
          <option value="">{{ t('issues.allComponents') }}</option>
          <option v-for="comp in componentsStore.components" :key="comp.id" :value="comp.id">{{ comp.name }}</option>
        </select>
      </div>

      <div class="mb-2 text-sm text-gray-500 dark:text-gray-400">
        {{ t('issues.showing') }} {{ filteredList.length }} {{ t('issues.of') }} {{ issuesStore.issues.length }} {{ t('issues.title').toLowerCase() }}
      </div>

      <div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400 w-10">
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  :indeterminate="isPartialSelected"
                  :aria-label="t('bulkActions.selectAll')"
                  class="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700"
                  @change="toggleSelectAll"
                />
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('issues.titleField') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('issues.status') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('issues.priority') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('issues.component') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('issues.labels') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('issues.created') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('components.actions') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
            <tr
              v-for="issue in filteredList"
              :key="issue.id"
              class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
              :class="{
                'border-l-4 border-l-red-500': issue.priority === 'CRITICAL',
                'border-l-4 border-l-orange-400': issue.priority === 'HIGH' && issue.status !== 'CLOSED',
                'bg-brand-50 dark:bg-brand-900/20': selectedIds.has(issue.id),
              }"
              @click="openIssue(issue)"
            >
              <td class="px-4 py-3 w-10">
                <input
                  type="checkbox"
                  :checked="selectedIds.has(issue.id)"
                  :aria-label="'Select issue ' + issue.id"
                  class="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700"
                  @click.stop="toggleSelect(issue.id)"
                />
              </td>
              <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100 max-w-xs truncate">{{ issue.title }}</td>
              <td class="px-4 py-3 text-sm"><StatusBadge :status="issue.status" /></td>
              <td class="px-4 py-3 text-sm"><PriorityBadge :priority="issue.priority" /></td>
              <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{{ getComponentName(issue.component_id) }}</td>
              <td class="px-4 py-3 text-sm">
                <div class="flex gap-1 flex-wrap">
                  <LabelTag v-for="label in issue.labels.slice(0, 2)" :key="label" :label="label" />
                  <span v-if="issue.labels.length > 2" class="text-xs text-gray-400">+{{ issue.labels.length - 2 }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{{ formatDate(issue.created_at) }}</td>
              <td class="px-4 py-3 text-sm">
                <div class="flex gap-1">
                  <button v-if="issue.status !== 'CLOSED'" class="text-amber-600 hover:text-amber-800 dark:text-amber-400" @click.stop="closeIssue(issue.id)" :title="t('issues.close')">
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                  </button>
                  <button class="text-red-600 hover:text-red-800 dark:text-red-400" @click.stop="deleteIssue(issue.id)" :title="t('issues.delete')">
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="filteredList.length === 0" class="py-12 text-center text-gray-400">
          {{ t('common.noData') }}
        </div>
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

    <BulkActionsBar
      v-if="selectedIds.size > 0"
      :count="selectedIds.size"
      @batch-status="batchStatusChange"
      @batch-assign="batchAssign"
      @batch-delete="batchDelete"
      @clear="clearSelection"
    />

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center"
      @click.self="showDeleteConfirm = false"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
        <div class="flex items-center gap-3 mb-4">
          <div class="flex-shrink-0 rounded-full bg-red-100 p-2 dark:bg-red-900/30">
            <svg class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('issues.delete') }}</h3>
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">{{ t('issues.deleteConfirm') }}</p>
        <div class="flex justify-end gap-3">
          <button
            type="button"
            class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
            @click="showDeleteConfirm = false"
          >
            {{ t('issues.cancel') }}
          </button>
          <button
            type="button"
            class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600"
            @click="confirmDeleteIssue"
          >
            {{ t('issues.delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue, IssueUpdateRequest } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
import { useComponentsStore } from '@/stores/componentsStore'
import { useUiStore } from '@/stores/uiStore'
import { useToast } from '@/composables/useToast'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import PriorityBadge from '@/components/ui/PriorityBadge.vue'
import LabelTag from '@/components/ui/LabelTag.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import IssueDetailView from '@/views/IssueDetailView.vue'
import CreateIssueModal from '@/components/issue/CreateIssueModal.vue'
import BulkActionsBar from '@/components/ui/BulkActionsBar.vue'
import { useExport } from '@/composables/useExport'

const { t } = useI18n()
const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()
const uiStore = useUiStore()
const toast = useToast()
const { exportCSV, exportJSON } = useExport()
const showCreateModal = ref(false)
const showExportMenu = ref(false)
const exportDropdownRef = ref<HTMLElement | null>(null)

const selectedIds = ref(new Set<string>())

const isAllSelected = computed(() => {
  if (filteredList.value.length === 0) return false
  return filteredList.value.every(i => selectedIds.value.has(i.id))
})

const isPartialSelected = computed(() => {
  if (selectedIds.value.size === 0) return false
  return !isAllSelected.value && filteredList.value.some(i => selectedIds.value.has(i.id))
})

function toggleSelect(id: string) {
  const newSet = new Set(selectedIds.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  selectedIds.value = newSet
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(filteredList.value.map(i => i.id))
  }
}

function clearSelection() {
  selectedIds.value = new Set()
}

async function batchStatusChange(status: string) {
  const ids = Array.from(selectedIds.value)
  await Promise.all(ids.map(id => issuesStore.updateIssue(id, { status: status as any })))
  toast.success(t('bulkActions.statusUpdated', { count: ids.length }))
  clearSelection()
}

async function batchAssign(userId: string) {
  const ids = Array.from(selectedIds.value)
  await Promise.all(ids.map(id => issuesStore.updateIssue(id, { assignee: userId || undefined })))
  toast.success(t('bulkActions.assigned', { count: ids.length }))
  clearSelection()
}

async function batchDelete() {
  const ids = Array.from(selectedIds.value)
  await Promise.all(ids.map(id => issuesStore.deleteIssue(id)))
  toast.success(t('bulkActions.deleted', { count: ids.length }))
  clearSelection()
}

const search = computed({
  get: () => uiStore.filters.search,
  set: (val: string) => uiStore.setFilter('search', val),
})

const statusFilter = computed({
  get: () => uiStore.filters.status[0] || '',
  set: (val: string) => uiStore.setFilter('status', val ? [val] : []),
})

const priorityFilter = computed({
  get: () => uiStore.filters.priority[0] || '',
  set: (val: string) => uiStore.setFilter('priority', val ? [val] : []),
})

const componentFilter = computed({
  get: () => uiStore.filters.component || '',
  set: (val: string) => uiStore.setFilter('component', val || null),
})

const filteredList = computed(() => {
  let result = issuesStore.issues
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter(i =>
      i.title.toLowerCase().includes(q) ||
      i.id.toLowerCase().includes(q) ||
      (i.description && i.description.toLowerCase().includes(q))
    )
  }
  if (statusFilter.value) {
    result = result.filter(i => i.status === statusFilter.value)
  }
  if (priorityFilter.value) {
    result = result.filter(i => i.priority === priorityFilter.value)
  }
  if (componentFilter.value) {
    result = result.filter(i => i.component_id === componentFilter.value)
  }
  return result
})

const selectedIssue = computed(() => {
  if (!uiStore.selectedIssueId) return null
  return issuesStore.issues.find((i) => i.id === uiStore.selectedIssueId) ?? null
})

function getComponentName(id: string): string {
  return componentsStore.getComponentById(id)?.name ?? ''
}

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString()
}

function openIssue(issue: Issue) {
  uiStore.setSelectedIssue(issue.id)
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

async function closeIssue(id: string) {
  await issuesStore.closeIssue(id)
}

const showDeleteConfirm = ref(false)
const deleteTargetId = ref('')

function deleteIssue(id: string) {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

async function confirmDeleteIssue() {
  await issuesStore.deleteIssue(deleteTargetId.value)
  showDeleteConfirm.value = false
  deleteTargetId.value = ''
}

async function fetchWithFilters() {
  const filters = uiStore.getBackendFilters()
  await issuesStore.fetchIssues(1, 100, filters)
}

function onIssueCreated() {
  showCreateModal.value = false
  fetchWithFilters()
}

async function downloadCSV() {
  showExportMenu.value = false
  const rows = filteredList.value.map(i => ({
    id: i.id,
    title: i.title,
    status: i.status,
    priority: i.priority,
    component: getComponentName(i.component_id),
    assignee: i.assignee || '',
    labels: i.labels.join('; '),
    created: i.created_at,
  }))
  await exportCSV(rows, 'issues-export')
}

async function downloadJSON() {
  showExportMenu.value = false
  await exportJSON(filteredList.value, 'issues-export')
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
</script>
