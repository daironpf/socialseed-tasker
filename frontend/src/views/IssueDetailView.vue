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
            {{ t('issues.aiAgentActive') }}
          </span>
        </div>
        <div class="flex items-center gap-3">
          <PresenceAvatars :viewers="viewers" />
          <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" @click="$emit('close')" :aria-label="t('common.close')">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
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

    <!-- HITL APPROVAL BANNER -->
    <div v-if="issue.status === 'WAITING_HUMAN_APPROVAL'" class="px-6 pt-4">
      <HITLApprovalBanner
        :action-details="pendingAction"
        @approve="onApprove"
        @reject="onReject"
        @modify="onModify"
      />

      <TypingIndicator :agents="typingAgents" />
      <ConflictWarning :show="hasConflict" />
    </div>

    <!-- DETAILS TAB -->
    <div v-if="activeTab === 'details'" class="p-6 space-y-6">
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ t('issues.titleField') }}</label>
        <input
          v-model="title"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <label class="block text-[10px] font-medium text-gray-400 dark:text-gray-500 mb-2 uppercase tracking-wider">{{ t('issues.assignee') }}</label>
          <select
            v-model="assignee"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          >
            <option value="">{{ t('issues.unassigned') }}</option>
            <option v-for="u in users" :key="u.id" :value="u.id">
              {{ u.avatar }} {{ u.username }}
            </option>
          </select>
        </div>
        <div v-if="creatorUser" class="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <label class="block text-[10px] font-medium text-gray-400 dark:text-gray-500 mb-2 uppercase tracking-wider">{{ t('issues.createdBy') }}</label>
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
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ t('issues.description') }}</label>
        <RichTextEditor
          v-model="description"
          :rows="6"
          :placeholder="t('issues.description')"
        />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ t('issues.status') }}</label>
          <select
            v-model="status"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          >
            <option value="OPEN">{{ t('issues.open') }}</option>
            <option value="IN_PROGRESS">{{ t('issues.inProgress') }}</option>
            <option value="BLOCKED">{{ t('issues.blocked') }}</option>
            <option value="WAITING_HUMAN_APPROVAL">{{ t('hitl.title') }}</option>
            <option value="CLOSED">{{ t('issues.closed') }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ t('issues.priority') }}</label>
          <select
            v-model="priority"
            class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          >
            <option value="LOW">{{ t('issues.low') }}</option>
            <option value="MEDIUM">{{ t('issues.medium') }}</option>
            <option value="HIGH">{{ t('issues.high') }}</option>
            <option value="CRITICAL">{{ t('issues.critical') }}</option>
          </select>
        </div>
      </div>

      <!-- Assignee History -->
      <div v-if="assigneeHistoryWithUsers.length > 0">
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">{{ t('profile.assigneeHistory') }}</label>
        <div class="space-y-2">
          <div
            v-for="(entry, idx) in assigneeHistoryWithUsers"
            :key="idx"
            class="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2"
          >
            <div class="flex items-center gap-2">
              <span class="text-lg">{{ entry.user.avatar || '👤' }}</span>
              <div>
                <div class="text-sm font-medium text-gray-900 dark:text-white">{{ entry.user.username }}</div>
                <div class="text-[10px] text-gray-500">{{ entry.user.role || entry.user.type }}</div>
              </div>
            </div>
            <div class="text-right text-[10px] text-gray-500 dark:text-gray-400">
              <div>{{ t('profile.assigned') }}: {{ new Date(entry.assignedAt).toLocaleDateString() }}</div>
              <div v-if="entry.unassignedAt">{{ t('profile.unassigned') }}: {{ new Date(entry.unassignedAt).toLocaleDateString() }}</div>
              <div v-else class="text-green-600 dark:text-green-400 font-medium">{{ t('profile.currentAssignee') }}</div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ t('issues.labels') }}</label>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="(label, idx) in labels"
            :key="idx"
            class="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs dark:bg-gray-700"
          >
            {{ label }}
            <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" :aria-label="t('issues.removeLabel', { label })" @click="labels.splice(idx, 1)">x</button>
          </span>
          <input
            v-model="newLabel"
            :placeholder="t('issues.addLabelPlaceholder')"
            :aria-label="t('issues.addLabelPlaceholder')"
            class="rounded-md border border-gray-300 bg-transparent px-2 py-0.5 text-xs focus:border-blue-500 focus:outline-none dark:border-gray-600"
            @keydown.enter.prevent="addLabel"
          />
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
          {{ t('issues.dependencies') }} ({{ issue.dependencies?.length || 0 }})
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
        <div v-else class="text-sm text-gray-400">{{ t('issues.noDependencies') }}</div>
      </div>

      <div class="text-xs text-gray-400 space-y-1">
        <p>{{ t('issues.created') }}: {{ new Date(issue.created_at).toLocaleString() }}</p>
        <p>{{ t('issues.updated') }}: {{ new Date(issue.updated_at).toLocaleString() }}</p>
      </div>
    </div>

    <!-- AI REASONING TAB -->
    <div v-else-if="activeTab === 'reasoning'" class="p-6">
      <AgentLogStream
        :logs="agentLogs"
        :status="streamStatus"
        @kill-switch="onKillSwitch"
      />
    </div>

    <!-- PROGRESS TAB -->
    <div v-else-if="activeTab === 'progress'" class="p-6 space-y-6">
      <div v-if="logsLoading" class="flex items-center justify-center py-12">
        <div class="h-6 w-6 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent"></div>
      </div>
      <template v-else>
        <div v-if="progressLogs.length > 0">
          <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">{{ t('issues.taskChecklist') }}</h4>
          <div
            v-for="(log, idx) in progressLogs"
            :key="idx"
            class="rounded-lg border border-gray-200 dark:border-gray-700 p-4"
          >
            <div class="mb-2 flex items-center gap-2">
              <span class="rounded bg-green-100 px-2 py-0.5 text-[10px] font-bold text-green-700 dark:bg-green-900/30 dark:text-green-300">{{ t('issues.logTypeProgress') }}</span>
              <span class="text-[10px] text-gray-400">{{ new Date(log.timestamp).toLocaleString() }}</span>
            </div>
            <MarkdownRenderer :content="log.content_markdown" />
          </div>
        </div>

        <div v-if="fileLogs.length > 0">
          <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">{{ t('issues.filesChanged') }}</h4>
          <div
            v-for="(log, idx) in fileLogs"
            :key="idx"
            class="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <div class="flex items-center gap-2 bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
              <span class="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">{{ t('issues.logTypeFiles') }}</span>
              <span class="text-[10px] text-gray-400">{{ new Date(log.timestamp).toLocaleString() }}</span>
            </div>
            <DiffViewer :content="log.content_markdown" />
          </div>
        </div>

        <div v-if="debtLogs.length > 0">
          <h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">{{ t('issues.technicalDebt') }}</h4>
          <div
            v-for="(log, idx) in debtLogs"
            :key="idx"
            class="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/10 p-4"
          >
            <div class="mb-2 flex items-center gap-2">
              <span class="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">{{ t('issues.logTypeDebt') }}</span>
              <span class="text-[10px] text-gray-400">{{ new Date(log.timestamp).toLocaleString() }}</span>
            </div>
            <MarkdownRenderer :content="log.content_markdown" />
          </div>
        </div>

        <div v-if="!progressLogs.length && !fileLogs.length && !debtLogs.length" class="flex flex-col items-center justify-center py-12 text-gray-400">
          <p class="text-sm">{{ t('issues.noProgressData') }}</p>
        </div>

        <TokenMetrics
          v-if="agentLogs.length > 0"
          model="claude-3.5-sonnet"
          :prompt-tokens="estimatedPromptTokens"
          :completion-tokens="estimatedCompletionTokens"
          :budget="5.00"
        />
      </template>
    </div>

    <!-- AUDIT TAB -->
    <div v-if="activeTab === 'audit'" class="p-6">
      <AuditTrail :entries="auditEntries" />
    </div>

    <!-- ACTIONS -->
    <div class="sticky bottom-0 border-t border-gray-200 bg-white px-6 py-4 dark:border-gray-700 dark:bg-gray-800">
      <div class="flex gap-2">
        <button
          class="flex-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          @click="save"
        >
          {{ t('issues.save') }}
        </button>
        <button
          v-if="issue.status !== 'CLOSED'"
          class="rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
          @click="$emit('closeIssue', issue.id)"
        >
          {{ t('issues.close') }}
        </button>
        <button
          class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          @click="confirmDelete"
        >
          {{ t('issues.delete') }}
        </button>
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
            @click="executeDelete"
          >
            {{ t('issues.delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue, IssueUpdateRequest, AgentLog, User, AssigneeHistoryEntry } from '@/types'
import { IssueStatus } from '@/types'
import { useIssuesStore } from '@/stores/issuesStore'
import { fetchAgentLogs } from '@/api/agentLogsApi'
import { fetchUsers } from '@/api/usersApi'
import MarkdownRenderer from '@/components/analysis/MarkdownRenderer.vue'
import RichTextEditor from '@/components/ui/RichTextEditor.vue'
import DiffViewer from '@/components/ui/DiffViewer.vue'
import HITLApprovalBanner from '@/components/ui/HITLApprovalBanner.vue'
import AgentLogStream from '@/components/ui/AgentLogStream.vue'
import TokenMetrics from '@/components/ui/TokenMetrics.vue'
import PresenceAvatars from '@/components/ui/PresenceAvatars.vue'
import TypingIndicator from '@/components/ui/TypingIndicator.vue'
import ConflictWarning from '@/components/ui/ConflictWarning.vue'
import AuditTrail from '@/components/ui/AuditTrail.vue'
import { useAgentStream } from '@/composables/useAgentStream'
import { usePresence } from '@/composables/usePresence'
import type { AuditEntry } from '@/types/audit'

const { t } = useI18n()

const props = defineProps<{ issue: Issue }>()
const emit = defineEmits<{
  close: []
  update: [id: string, body: IssueUpdateRequest]
  delete: [id: string]
  closeIssue: [id: string]
}>()

const issuesStore = useIssuesStore()

const tabs = computed(() => [
  { key: 'details', label: t('issues.details') },
  { key: 'reasoning', label: t('issues.aiReasoning') },
  { key: 'progress', label: t('issues.progress') },
  { key: 'audit', label: t('audit.tab') },
])
const activeTab = ref('details')

const title = ref(props.issue.title)
const description = ref(props.issue.description)
const status = ref(props.issue.status)
const priority = ref(props.issue.priority)
const labels = ref([...props.issue.labels])
const assignee = ref(props.issue.assignee || '')
const newLabel = ref('')
const assigneeHistory = ref<AssigneeHistoryEntry[]>(props.issue.assignee_history || [])
const previousAssignee = ref(props.issue.assignee || '')
const historyInitialized = ref(false)

onMounted(() => {
  if (!historyInitialized.value) {
    assigneeHistory.value = props.issue.assignee_history || []
    previousAssignee.value = props.issue.assignee || ''
    historyInitialized.value = true
  }
})

watch(() => props.issue, (newIssue) => {
  title.value = newIssue.title
  description.value = newIssue.description
  status.value = newIssue.status
  priority.value = newIssue.priority
  labels.value = [...newIssue.labels]
  assignee.value = newIssue.assignee || ''
  if (!historyInitialized.value) {
    assigneeHistory.value = newIssue.assignee_history || []
    previousAssignee.value = newIssue.assignee || ''
    historyInitialized.value = true
  }
}, { deep: true })

watch(assignee, (newVal) => {
  const oldVal = previousAssignee.value
  if (newVal === oldVal) return
  
  const now = new Date().toISOString()
  
  if (oldVal) {
    const lastEntry = [...assigneeHistory.value].reverse().find(h => h.userId === oldVal && !h.unassignedAt)
    if (lastEntry) {
      lastEntry.unassignedAt = now
    }
  }
  
  if (newVal) {
    assigneeHistory.value.push({
      userId: newVal,
      assignedAt: now,
    })
  }
  
  previousAssignee.value = newVal
})

const agentLogs = ref<AgentLog[]>([])
const logsLoading = ref(false)
const users = ref<User[]>([])

const { status: streamStatus, connect: connectStream, disconnect: disconnectStream } = useAgentStream()
const { viewers, typingAgents, hasConflict } = usePresence(props.issue.id)

const auditEntries = computed<AuditEntry[]>(() => {
  const now = Date.now()
  const h = (hours: number) => new Date(now - hours * 3600000).toISOString()
  return [
    { id: 'a1', issueId: props.issue.id, action: 'status', actor: 'alice', actorAvatar: '👩‍💻', actorType: 'human', description: 'Changed status', details: { from: 'OPEN', to: 'IN_PROGRESS' }, timestamp: h(0.5) },
    { id: 'a2', issueId: props.issue.id, action: 'agent', actor: 'Arch-Bot', actorAvatar: '🏗️', actorType: 'agent', description: 'Started impact analysis', timestamp: h(1) },
    { id: 'a3', issueId: props.issue.id, action: 'assignment', actor: 'bob', actorAvatar: '👨‍💻', actorType: 'human', description: 'Assigned to alice', details: { from: 'unassigned', to: 'alice' }, timestamp: h(2) },
    { id: 'a4', issueId: props.issue.id, action: 'priority', actor: 'alice', actorAvatar: '👩‍💻', actorType: 'human', description: 'Changed priority', details: { from: 'MEDIUM', to: 'HIGH' }, timestamp: h(3) },
    { id: 'a5', issueId: props.issue.id, action: 'hitl', actor: 'alice', actorAvatar: '👩‍💻', actorType: 'human', description: 'Approved agent action: DELETE on users table', timestamp: h(5) },
    { id: 'a6', issueId: props.issue.id, action: 'system', actor: 'System', actorAvatar: '', actorType: 'system', description: 'Constraint violation detected: rate limit exceeded', timestamp: h(8) },
    { id: 'a7', issueId: props.issue.id, action: 'label', actor: 'bob', actorAvatar: '👨‍💻', actorType: 'human', description: 'Added labels', details: { to: 'backend, urgent' }, timestamp: h(12) },
    { id: 'a8', issueId: props.issue.id, action: 'comment', actor: 'alice', actorAvatar: '👩‍💻', actorType: 'human', description: 'Added comment: "Looks good, let\'s ship it"', timestamp: h(24) },
    { id: 'a9', issueId: props.issue.id, action: 'status', actor: 'System', actorAvatar: '', actorType: 'system', description: 'Auto-closed after merge to main', details: { from: 'IN_PROGRESS', to: 'CLOSED' }, timestamp: h(48) },
  ]
})

const creatorUser = computed(() => {
  if (!props.issue.created_by) return null
  return users.value.find(u => u.id === props.issue.created_by) || null
})

const assigneeHistoryWithUsers = computed(() => {
  return assigneeHistory.value.map(entry => {
    const user = users.value.find(u => u.id === entry.userId)
    return {
      ...entry,
      user: user || { username: entry.userId, avatar: '👤', role: 'unknown', type: 'human' as const },
    }
  }).sort((a, b) => new Date(b.assignedAt).getTime() - new Date(a.assignedAt).getTime())
})

const progressLogs = computed(() => agentLogs.value.filter(l => l.type === 'progress'))
const fileLogs = computed(() => agentLogs.value.filter(l => l.type === 'files'))
const debtLogs = computed(() => agentLogs.value.filter(l => l.type === 'debt'))

const estimatedPromptTokens = computed(() => {
  return agentLogs.value.reduce((sum, log) => {
    const text = log.content_markdown || ''
    return sum + Math.ceil(text.length / 4)
  }, 0)
})

const estimatedCompletionTokens = computed(() => {
  return Math.ceil(estimatedPromptTokens.value * 0.35)
})

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

function onKillSwitch() {
  disconnectStream()
  agentLogs.value.push({
    timestamp: new Date().toISOString(),
    type: 'debt',
    content_markdown: '**AGENT EXECUTION CANCELLED** by human operator.',
  })
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
  const body: IssueUpdateRequest = {
    title: title.value,
    description: description.value,
    status: status.value,
    priority: priority.value,
    labels: labels.value,
    assignee: assignee.value || undefined,
    assignee_history: assigneeHistory.value,
  }
  if (status.value === 'CLOSED' && props.issue.status !== 'CLOSED') {
    body.closed_at = new Date().toISOString()
  }
  if (status.value !== 'CLOSED' && props.issue.status === 'CLOSED') {
    body.closed_at = null
  }
  emit('update', props.issue.id, body)
}

const showDeleteConfirm = ref(false)

function confirmDelete() {
  showDeleteConfirm.value = true
}

function executeDelete() {
  showDeleteConfirm.value = false
  emit('delete', props.issue.id)
}

const pendingAction = computed(() => {
  if (props.issue.status !== 'WAITING_HUMAN_APPROVAL') return null
  const lastFileLog = fileLogs.value[fileLogs.value.length - 1]
  if (lastFileLog) {
    return {
      type: 'Code Change',
      command: lastFileLog.content_markdown.substring(0, 500),
      severity: 'HIGH',
      description: t('hitl.actionDescription'),
    }
  }
  return {
    type: 'Agent Action',
    command: t('hitl.defaultCommand'),
    severity: 'HIGH',
    description: t('hitl.actionDescription'),
  }
})

function onApprove() {
  status.value = IssueStatus.IN_PROGRESS
  save()
}

function onReject(feedback: string) {
  description.value = description.value + '\n\n---\n**HITL Rejection:** ' + feedback
  status.value = IssueStatus.BLOCKED
  save()
}

function onModify(params: string) {
  description.value = description.value + '\n\n---\n**HITL Modified Parameters:**\n```\n' + params + '\n```'
  status.value = IssueStatus.IN_PROGRESS
  save()
}

watch(activeTab, (tab) => {
  if (tab === 'reasoning' || tab === 'progress') {
    loadLogs()
    if (props.issue.agent_working) {
      connectStream(props.issue.id)
    }
  }
})

onMounted(async () => {
  try {
    users.value = await fetchUsers()
  } catch {
    users.value = []
  }
  if (props.issue.agent_working && activeTab.value === 'reasoning') {
    connectStream(props.issue.id)
  }
})

onUnmounted(() => {
  disconnectStream()
})
</script>
