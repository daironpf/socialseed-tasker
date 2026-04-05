<template>
  <div
    class="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-white shadow-xl dark:bg-gray-800 overflow-y-auto"
  >
    <div class="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4 dark:border-gray-700 dark:bg-gray-800">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Issue Details</h2>
      <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" @click="$emit('close')">
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div class="p-6 space-y-6">
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Title</label>
        <input
          v-model="title"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Description</label>
        <textarea
          v-model="description"
          rows="4"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Status</label>
          <select
            v-model="status"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          >
            <option value="OPEN">Open</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="BLOCKED">Blocked</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Priority</label>
          <select
            v-model="priority"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          >
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Labels</label>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="(label, idx) in labels"
            :key="idx"
            class="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs dark:bg-gray-700"
          >
            {{ label }}
            <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" @click="labels.splice(idx, 1)">x</button>
          </span>
          <input
            v-model="newLabel"
            placeholder="Add label..."
            class="rounded-md border border-gray-300 bg-transparent px-2 py-0.5 text-xs focus:border-brand-500 focus:outline-none dark:border-gray-600"
            @keydown.enter.prevent="addLabel"
          />
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
          Dependencies ({{ issue.dependencies.length }})
        </label>
        <div v-if="issue.dependencies.length > 0" class="space-y-1">
          <div
            v-for="depId in issue.dependencies"
            :key="depId"
            class="flex items-center justify-between rounded-md bg-gray-50 px-3 py-1.5 text-sm dark:bg-gray-700"
          >
            <span class="text-gray-600 dark:text-gray-300 truncate">{{ getIssueTitle(depId) }}</span>
            <button class="text-red-500 hover:text-red-700 text-xs" @click="removeDep(depId)">Remove</button>
          </div>
        </div>
        <div v-else class="text-sm text-gray-400">No dependencies</div>
      </div>

      <div class="text-xs text-gray-400 space-y-1">
        <p>Created: {{ new Date(issue.created_at).toLocaleString() }}</p>
        <p>Updated: {{ new Date(issue.updated_at).toLocaleString() }}</p>
      </div>

      <div class="flex gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
        <button
          class="flex-1 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
          @click="save"
        >
          Save
        </button>
        <button
          v-if="issue.status !== 'CLOSED'"
          class="rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
          @click="$emit('closeIssue', issue.id)"
        >
          Close
        </button>
        <button
          class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          @click="confirmDelete"
        >
          Delete
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Issue } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'

const props = defineProps<{ issue: Issue }>()
const emit = defineEmits<{
  close: []
  update: [id: string, body: Record<string, unknown>]
  delete: [id: string]
  closeIssue: [id: string]
}>()

const issuesStore = useIssuesStore()

const title = ref(props.issue.title)
const description = ref(props.issue.description)
const status = ref(props.issue.status)
const priority = ref(props.issue.priority)
const labels = ref([...props.issue.labels])
const newLabel = ref('')

function addLabel() {
  const l = newLabel.value.trim()
  if (l && !labels.value.includes(l)) {
    labels.value.push(l)
  }
  newLabel.value = ''
}

function getIssueTitle(id: string): string {
  const found = issuesStore.issues.find((i) => i.id === id)
  return found ? found.title : id.slice(0, 8)
}

async function removeDep(depId: string) {
  try {
    const { removeDependency } = await import('@/api/dependenciesApi')
    await removeDependency(props.issue.id, depId)
    await issuesStore.fetchIssues()
  } catch {
    // ignore
  }
}

async function save() {
  emit('update', props.issue.id, {
    title: title.value,
    description: description.value,
    status: status.value,
    priority: priority.value,
    labels: labels.value,
  })
}

function confirmDelete() {
  if (confirm('Are you sure you want to delete this issue?')) {
    emit('delete', props.issue.id)
  }
}

onMounted(() => {
  issuesStore.fetchIssues()
})
</script>
