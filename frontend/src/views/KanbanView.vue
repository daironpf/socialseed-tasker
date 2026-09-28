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
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white sm:text-2xl">{{ t('header.kanban') }}</h1>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ issuesStore.filteredIssues.length }} {{ t('issues.title').toLowerCase() }}
          </span>
          <button
            class="min-h-[44px] rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
            @click="showCreateModal = true"
          >
            {{ t('issues.newIssue') }}
          </button>
        </div>
      </div>

      <!-- Filter Bar -->
      <div class="mb-4">
        <FilterBuilder />
      </div>

      <!-- Kanban Columns -->
      <div class="relative flex-1">
        <div
          ref="boardRef"
          role="listbox"
          tabindex="-1"
          class="flex h-full gap-4 overflow-x-auto snap-x snap-mandatory md:snap-none scroll-smooth pb-2 focus:outline-none"
          :aria-label="t('header.kanban')"
          :aria-activedescendant="activeCardId"
        >
          <KanbanColumn
            v-for="col in columns"
            :key="col.status"
            :title="col.title"
            :status="col.status"
            :issues="issuesByStatus(col.status)"
            :active-issue-id="activeIssueId"
            class="flex-1 min-w-[85vw] max-w-[400px] sm:min-w-[280px] snap-start scroll-mt-4"
            @openIssue="openIssue"
            @dropIssue="onDropIssue"
          />
        </div>
        <div class="pointer-events-none absolute inset-y-0 left-0 z-10 w-8 bg-gradient-to-r from-gray-50 to-transparent dark:from-gray-900 md:hidden"></div>
        <div class="pointer-events-none absolute inset-y-0 right-0 z-10 w-8 bg-gradient-to-l from-gray-50 to-transparent dark:from-gray-900 md:hidden"></div>
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
      role="dialog"
      aria-modal="true"
      :aria-label="selectedIssue.title"
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

    <!-- Governance Validation Modal -->
    <GovernanceValidationModal
      v-if="showGovernanceModal && governanceTargetIssue"
      :issue-title="`${governanceTargetIssue.id} — ${governanceTargetIssue.title}`"
      :governance="governanceTargetIssue.governance!"
      @close="onGovernanceClose"
      @override="onGovernanceOverride"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue, IssueUpdateRequest } from '@/types'
import { IssueStatus } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
import { useComponentsStore } from '@/stores/componentsStore'
import { useUiStore } from '@/stores/uiStore'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import KanbanColumn from '@/components/board/KanbanColumn.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import FilterBuilder from '@/components/ui/FilterBuilder.vue'
import IssueDetailView from '@/views/IssueDetailView.vue'
import CreateIssueModal from '@/components/issue/CreateIssueModal.vue'
import GovernanceValidationModal from '@/components/issue/GovernanceValidationModal.vue'

const { t } = useI18n()

const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()
const uiStore = useUiStore()
const { register, unregisterAll } = useKeyboardShortcuts()

const showCreateModal = ref(false)
const showDeleteConfirm = ref(false)
const deleteTargetId = ref('')
const showGovernanceModal = ref(false)
const governanceTargetIssue = ref<Issue | null>(null)
const boardRef = ref<HTMLElement | null>(null)
const cursorIndex = ref(-1)

const priorityOrder: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }

const flatIssues = computed(() =>
  columns.value.flatMap((col) =>
    [...issuesByStatus(col.status)].sort(
      (a, b) => (priorityOrder[a.priority] ?? 99) - (priorityOrder[b.priority] ?? 99),
    ),
  ),
)

const activeIssueId = computed(() => flatIssues.value[cursorIndex.value]?.id)

const activeCardId = computed(() => {
  const issue = flatIssues.value[cursorIndex.value]
  return issue ? `issue-card-${issue.id}` : undefined
})

function moveCursor(delta: number) {
  const list = flatIssues.value
  if (list.length === 0) return
  if (cursorIndex.value < 0) {
    cursorIndex.value = delta > 0 ? 0 : list.length - 1
  } else {
    cursorIndex.value = Math.max(0, Math.min(list.length - 1, cursorIndex.value + delta))
  }
  nextTick(() => {
    const id = activeCardId.value
    if (id) document.getElementById(id)?.scrollIntoView({ block: 'nearest' })
    boardRef.value?.focus()
  })
}

function moveCursorDown() {
  moveCursor(1)
}

function moveCursorUp() {
  moveCursor(-1)
}

function openCursorIssue() {
  const issue = flatIssues.value[cursorIndex.value]
  if (issue) openIssue(issue)
}

function onEscapeKey() {
  if (showDeleteConfirm.value) {
    showDeleteConfirm.value = false
    return
  }
  if (showCreateModal.value) {
    showCreateModal.value = false
    return
  }
  if (showGovernanceModal.value) {
    onGovernanceClose()
    return
  }
  if (uiStore.selectedIssueId) {
    uiStore.setSelectedIssue(null)
    nextTick(() => boardRef.value?.focus())
  }
}

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
  if (newStatus === 'CLOSED' && issue.governance) {
    const g = issue.governance
    if (!g.has_solution_summary || !g.has_file_impact || g.policy_violations.length > 0) {
      governanceTargetIssue.value = issue
      showGovernanceModal.value = true
      return
    }
  }
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

function onGovernanceClose() {
  showGovernanceModal.value = false
  governanceTargetIssue.value = null
}

function onGovernanceOverride() {
  if (!governanceTargetIssue.value) return
  const issue = governanceTargetIssue.value
  const update: IssueUpdateRequest = { status: IssueStatus.CLOSED, closed_at: new Date().toISOString() }
  issuesStore.updateIssue(issue.id, update)
  uiStore.simulateSync()
  showGovernanceModal.value = false
  governanceTargetIssue.value = null
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
  register({
    key: 'j',
    label: 'Next card',
    description: t('shortcuts.nextItem'),
    scope: 'local',
    action: moveCursorDown,
  })
  register({
    key: 'k',
    label: 'Previous card',
    description: t('shortcuts.prevItem'),
    scope: 'local',
    action: moveCursorUp,
  })
  register({
    key: 'enter',
    label: 'Open card',
    description: t('shortcuts.openDetail'),
    scope: 'local',
    action: openCursorIssue,
  })
  register({
    key: 'escape',
    label: 'Close panel',
    description: t('shortcuts.closePanel'),
    scope: 'local',
    action: onEscapeKey,
  })
  await componentsStore.fetchComponents()
  await fetchWithFilters()
})

onUnmounted(() => {
  unregisterAll('local')
})

watch(
  () => flatIssues.value.length,
  (length) => {
    if (cursorIndex.value >= length) {
      cursorIndex.value = length - 1
    }
  },
)

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
