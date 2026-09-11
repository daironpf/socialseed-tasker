<template>
  <div class="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-white shadow-xl dark:bg-gray-800 overflow-y-auto">
    <div class="sticky top-0 z-10 border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div class="flex items-center justify-between px-6 py-4">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {{ issue.id }}
          </h2>
          <span
            v-if="issue.agent_working"
            class="inline-flex items-center gap-1.5 rounded-full bg-cyan-100 px-2.5 py-0.5 text-xs font-medium text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300"
          >
            <svg class="h-3.5 w-3.5 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2zM9.5 13a1.5 1.5 0 100 3 1.5 1.5 0 000-3zm5 0a1.5 1.5 0 100 3 1.5 1.5 0 000-3z"/>
            </svg>
            AI Agent Active
          </span>
        </div>
        <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" @click="$emit('close')">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex gap-0 border-b border-gray-200 dark:border-gray-700 px-6">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="border-b-2 px-3 py-2.5 text-sm font-medium transition-colors"
          :class="activeTab === tab.key
            ? 'border-blue-500 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
          <span
            v-if="tab.key === 'reasoning' && agentLogs.length"
            class="ml-1.5 rounded-full bg-purple-100 px-1.5 py-0.5 text-[10px] font-bold text-purple-700 dark:bg-purple-900/30 dark:text-purple-300"
          >
            {{ agentLogs.length }}
          </span>
        </button>
      </div>
    </div>

    <!-- DETAILS TAB -->
    <div v-if="activeTab === 'details'" class="p-6 space-y-6">
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Title</label>
        <input
          v-model="title"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div v-if="assigneeUser" class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <label class="block text-[10px] font-medium text-gray-400 dark:text-gray-500 mb-2 uppercase tracking-wider">Assignee</label>
          <div class="flex items-center gap-2">
            <span class="text-lg">{{ assigneeUser.avatar || '👤' }}</span>
            <div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">{{ assigneeUser.username }}</div>
              <div class="text-[10px] text-gray-500">{{ assigneeUser.role || assigneeUser.type }}</div>
            </div>
          </div>
        </div>
        <div v-if="creatorUser" class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <label class="block text-[10px] font-medium text-gray-400 dark:text-gray-500 mb-2 uppercase tracking-wider">Created by</label>
          <div class="flex items-center gap-2">
            <span class="text-lg">{{ creatorUser.avatar || '👤' }}</span>
            <div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">{{ creatorUser.username }}</div>
              <div class="text-[10px] text-gray-500">{{ creatorUser.role || creatorUser.type }}</div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Description</label>
        <textarea
          v-model="description"
          rows="4"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Status</label>
          <select
            v-model="status"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
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
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
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
            class="rounded-md border border-gray-300 bg-transparent px-2 py-0.5 text-xs focus:border-blue-500 focus:outline-none dark:border-gray-600"
            @keydown.enter.prevent="addLabel"
          />
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
          Dependencies ({{ issue.dependencies?.length || 0 }})
        </label>
        <div v-if="issue.dependencies?.length" class="space-y-1">
          <div
            v-for="depId in issue.dependencies"
            :key="depId"
            class="flex items-center justify-between rounded-md bg-gray-50 px-3 py-1.5 text-sm dark:bg-gray-700"
          >
            <span class="text-gray-600 dark:text-gray-300 truncate">{{ getIssueTitle(depId) }}</span>
          </div>
        </div>
        <div v-else class="text-sm text-gray-400">No dependencies</div>
      </div>

      <div class="text-xs text-gray-400 space-y-1">
        <p>Created: {{ new Date(issue.created_at).toLocaleString() }}</p>
        <p>Updated: {{ new Date(issue.updated_at).toLocaleString() }}</p>
      </div>
    </div>

    <!-- AI REASONING TAB -->
    <div v-else-if="activeTab === 'reasoning'" class="p-6">
      <div v-if="logsLoading" class="flex items-center justify-center py-12">
        <div class="h-6 w-6 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent"></div>
        <span class="ml-3 text-sm text-gray-500">Loading agent logs...</span>
      </div>
      <div v-else-if="reasoningLogs.length === 0" class="flex flex-col items-center justify-center py-12 text-gray-400">
        <svg class="mb-3 h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <p class="text-sm">No reasoning logs for this issue</p>
      </div>
      <div v-else class="space-y-4">
        <div
          v-for="(log, idx) in reasoningLogs"
          :key="idx"
          class="rounded-lg border border-gray-200 dark:border-gray-700 p-4"
        >
          <div class="mb-2 flex items-center gap-2">
            <span class="rounded bg-cyan-100 px-2 py-0.5 text-[10px] font-bold text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300">
              REASONING
            </span>
            <span class="text-[10px] text-gray-400">{{ new Date(log.timestamp).toLocaleString() }}</span>
          </div>
          <MarkdownRenderer :content="log.content_markdown" />
        </div>
      </div>
    </div>

    <!-- PROGRESS TAB -->
    <div v-else-if="activeTab === 'progress'" class="p-6 space-y-6">
      <div v-if="logsLoading" class="flex items-center justify-center py-12">
        <div class="h-6 w-6 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent"></div>
      </div>
      <template v-else>
        <div v-if="progressLogs.length > 0">
          <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">Task Checklist</h4>
          <div
            v-for="(log, idx) in progressLogs"
            :key="idx"
            class="rounded-lg border border-gray-200 dark:border-gray-700 p-4"
          >
            <div class="mb-2 flex items-center gap-2">
              <span class="rounded bg-green-100 px-2 py-0.5 text-[10px] font-bold text-green-700 dark:bg-green-900/30 dark:text-green-300">PROGRESS</span>
              <span class="text-[10px] text-gray-400">{{ new Date(log.timestamp).toLocaleString() }}</span>
            </div>
            <MarkdownRenderer :content="log.content_markdown" />
          </div>
        </div>

        <div v-if="fileLogs.length > 0">
          <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">Files Changed</h4>
          <div
            v-for="(log, idx) in fileLogs"
            :key="idx"
            class="rounded-lg border border-gray-200 dark:border-gray-700 p-4"
          >
            <div class="mb-2 flex items-center gap-2">
              <span class="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">FILES</span>
              <span class="text-[10px] text-gray-400">{{ new Date(log.timestamp).toLocaleString() }}</span>
            </div>
            <MarkdownRenderer :content="log.content_markdown" />
          </div>
        </div>

        <div v-if="debtLogs.length > 0">
          <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">Technical Debt</h4>
          <div
            v-for="(log, idx) in debtLogs"
            :key="idx"
            class="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/10 p-4"
          >
            <div class="mb-2 flex items-center gap-2">
              <span class="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">DEBT</span>
              <span class="text-[10px] text-gray-400">{{ new Date(log.timestamp).toLocaleString() }}</span>
            </div>
            <MarkdownRenderer :content="log.content_markdown" />
          </div>
        </div>

        <div v-if="!progressLogs.length && !fileLogs.length && !debtLogs.length" class="flex flex-col items-center justify-center py-12 text-gray-400">
          <p class="text-sm">No progress data for this issue</p>
        </div>
      </template>
    </div>

    <!-- ACTIONS -->
    <div class="sticky bottom-0 border-t border-gray-200 bg-white px-6 py-4 dark:border-gray-700 dark:bg-gray-800">
      <div class="flex gap-2">
        <button
          class="flex-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
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
import { ref, computed, onMounted, watch } from 'vue'
import type { Issue, AgentLog } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
import { fetchAgentLogs, fetchUsers } from '@/api/mockApi'
import MarkdownRenderer from '@/components/analysis/MarkdownRenderer.vue'

const props = defineProps<{ issue: Issue }>()
const emit = defineEmits<{
  close: []
  update: [id: string, body: Record<string, unknown>]
  delete: [id: string]
  closeIssue: [id: string]
}>()

const issuesStore = useIssuesStore()

const tabs = [
  { key: 'details', label: 'Details' },
  { key: 'reasoning', label: 'AI Reasoning' },
  { key: 'progress', label: 'Progress' },
]
const activeTab = ref('details')

const title = ref(props.issue.title)
const description = ref(props.issue.description)
const status = ref(props.issue.status)
const priority = ref(props.issue.priority)
const labels = ref([...props.issue.labels])
const newLabel = ref('')

const agentLogs = ref<AgentLog[]>([])
const logsLoading = ref(false)
const users = ref<any[]>([])

const assigneeUser = computed(() => {
  if (!props.issue.assignee) return null
  return users.value.find(u => u.id === props.issue.assignee) || null
})

const creatorUser = computed(() => {
  if (!props.issue.created_by) return null
  return users.value.find(u => u.id === props.issue.created_by) || null
})

const reasoningLogs = computed(() => agentLogs.value.filter(l => l.type === 'reasoning'))
const progressLogs = computed(() => agentLogs.value.filter(l => l.type === 'progress'))
const fileLogs = computed(() => agentLogs.value.filter(l => l.type === 'files'))
const debtLogs = computed(() => agentLogs.value.filter(l => l.type === 'debt'))

async function loadLogs() {
  logsLoading.value = true
  try {
    const bundle = await fetchAgentLogs(props.issue.id)
    agentLogs.value = bundle.logs || []
  } catch {
    agentLogs.value = []
  } finally {
    logsLoading.value = false
  }
}

function addLabel() {
  const l = newLabel.value.trim()
  if (l && !labels.value.includes(l)) {
    labels.value.push(l)
  }
  newLabel.value = ''
}

function getIssueTitle(id: string): string {
  const found = issuesStore.issues.find((i) => i.id === id)
  return found ? `${found.id} — ${found.title}` : id
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

watch(activeTab, (tab) => {
  if (tab === 'reasoning' || tab === 'progress') {
    loadLogs()
  }
})

onMounted(async () => {
  issuesStore.fetchIssues()
  try {
    users.value = await fetchUsers()
  } catch {
    users.value = []
  }
})
</script>
