<template>
  <div class="flex-1 overflow-auto p-4">
    <div v-if="issuesStore.loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else>
      <div class="mb-4 flex items-center gap-2">
        <input
          v-model="search"
          placeholder="Search issues..."
          class="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
        <select
          v-model="statusFilter"
          class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        >
          <option value="">All Status</option>
          <option value="OPEN">Open</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="BLOCKED">Blocked</option>
          <option value="CLOSED">Closed</option>
        </select>
        <select
          v-model="priorityFilter"
          class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        >
          <option value="">All Priority</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      <div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Title</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Status</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Priority</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Component</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Labels</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Created</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Actions</th>
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
              }"
              @click="openIssue(issue)"
            >
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
                  <button v-if="issue.status !== 'CLOSED'" class="text-amber-600 hover:text-amber-800 dark:text-amber-400" @click.stop="closeIssue(issue.id)" title="Close">
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                  </button>
                  <button class="text-red-600 hover:text-red-800 dark:text-red-400" @click.stop="deleteIssue(issue.id)" title="Delete">
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="filteredList.length === 0" class="py-12 text-center text-gray-400">
          No issues found
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Issue, IssueUpdateRequest } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
import { useComponentsStore } from '@/stores/componentsStore'
import { useUiStore } from '@/stores/uiStore'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import PriorityBadge from '@/components/ui/PriorityBadge.vue'
import LabelTag from '@/components/ui/LabelTag.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import IssueDetailView from '@/views/IssueDetailView.vue'

const issuesStore = useIssuesStore()
const componentsStore = useComponentsStore()
const uiStore = useUiStore()

const search = ref('')
const statusFilter = ref('')
const priorityFilter = ref('')

const filteredList = computed(() => {
  let list = uiStore.filteredIssues
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter((i) => i.title.toLowerCase().includes(q) || i.description.toLowerCase().includes(q))
  }
  if (statusFilter.value) {
    list = list.filter((i) => i.status === statusFilter.value)
  }
  if (priorityFilter.value) {
    list = list.filter((i) => i.priority === priorityFilter.value)
  }
  return list
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

async function deleteIssue(id: string) {
  if (confirm('Delete this issue?')) {
    await issuesStore.deleteIssue(id)
  }
}

onMounted(async () => {
  await Promise.all([
    issuesStore.fetchIssues(),
    componentsStore.fetchComponents(),
  ])
})
</script>
