<template>
  <div class="flex-1 overflow-x-auto">
    <div v-if="usersStore.loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else class="p-6">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('users.title') }}</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('users.subtitle') }}</p>
        </div>
        <button
          class="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
          @click="showCreateModal = true"
        >
          {{ t('users.newUser') }}
        </button>
      </div>

      <!-- Stats -->
      <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="text-sm text-gray-500 dark:text-gray-400">{{ t('users.totalUsers') }}</div>
          <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ usersStore.users.length }}</div>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="text-sm text-gray-500 dark:text-gray-400">{{ t('users.humans') }}</div>
          <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ humans.length }}</div>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="text-sm text-gray-500 dark:text-gray-400">{{ t('users.aiAgents') }}</div>
          <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">{{ agents.length }}</div>
        </div>
      </div>

      <!-- Users Grid -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <div
          v-for="user in usersStore.users"
          :key="user.id"
          class="rounded-xl border border-gray-200 bg-white p-5 transition-shadow hover:shadow-lg dark:border-gray-700 dark:bg-gray-800"
        >
          <!-- Header -->
          <div class="mb-4 flex items-center gap-3">
            <div
              class="flex h-12 w-12 items-center justify-center rounded-full text-2xl"
              :class="user.type === 'human' ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-purple-100 dark:bg-purple-900/30'"
            >
              {{ user.avatar }}
            </div>
            <div class="flex-1">
              <h3 class="font-semibold text-gray-900 dark:text-white">{{ user.username }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ user.email }}</p>
            </div>
            <span
              class="rounded-full px-2 py-0.5 text-xs font-medium"
              :class="user.type === 'human' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'"
            >
              {{ user.type === 'human' ? t('users.humanBadge') : t('users.aiBadge') }}
            </span>
          </div>

          <!-- Role -->
          <div class="mb-3 text-sm text-gray-600 dark:text-gray-300">
            <span class="font-medium">{{ t('users.role') }}:</span> {{ formatRole(user.role) }}
          </div>

          <!-- Model (for agents) -->
          <div v-if="user.type === 'agent' && user.model" class="mb-3 text-sm text-gray-600 dark:text-gray-300">
            <span class="font-medium">{{ t('users.model') }}:</span> {{ user.model }}
          </div>

          <!-- Skills -->
          <div class="mb-4">
            <div class="mb-1 text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('users.skills') }}</div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="skill in user.skills"
                :key="skill"
                class="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300"
              >
                {{ skill }}
              </span>
            </div>
          </div>

          <!-- Stats -->
          <div class="grid grid-cols-3 gap-2 border-t border-gray-100 pt-3 dark:border-gray-700">
            <button
              @click="openIssuesModal(user, 'assigned')"
              class="cursor-pointer text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg p-1 -m-1"
            >
              <div class="text-lg font-bold text-blue-600 dark:text-blue-400">{{ getUserAssignedCount(user.id) }}</div>
              <div class="text-[10px] text-gray-500 dark:text-gray-400">{{ t('users.assigned') }}</div>
            </button>
            <button
              @click="openIssuesModal(user, 'created')"
              class="cursor-pointer text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg p-1 -m-1"
            >
              <div class="text-lg font-bold text-green-600 dark:text-green-400">{{ getUserCreatedCount(user.id) }}</div>
              <div class="text-[10px] text-gray-500 dark:text-gray-400">{{ t('users.created') }}</div>
            </button>
            <button
              @click="openIssuesModal(user, 'completed')"
              class="cursor-pointer text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg p-1 -m-1"
            >
              <div class="text-lg font-bold text-purple-600 dark:text-purple-400">{{ getUserCompletedCount(user.id) }}</div>
              <div class="text-[10px] text-gray-500 dark:text-gray-400">{{ t('users.completed') }}</div>
            </button>
          </div>

          <!-- Last Active -->
          <div class="mt-3 flex items-center justify-between">
            <div class="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ t('users.lastActive') }} {{ formatDate(user.last_active) }}
            </div>
            <div class="flex items-center gap-1">
              <button
                v-if="user.type === 'agent'"
                @click="openEditAgent(user)"
                class="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-purple-600 dark:hover:bg-gray-700 dark:hover:text-purple-400"
                :title="t('users.editAgent')"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button
                v-if="user.type === 'human'"
                @click="openEditUser(user)"
                class="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-blue-600 dark:hover:bg-gray-700 dark:hover:text-blue-400"
                :title="t('users.editUser')"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button
                v-if="user.type === 'agent'"
                @click="deleteAgent(user)"
                class="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-red-600 dark:hover:bg-gray-700 dark:hover:text-red-400"
                :title="t('users.deleteAgent')"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <button
                v-if="user.type === 'human'"
                @click="deleteUser(user)"
                class="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-red-600 dark:hover:bg-gray-700 dark:hover:text-red-400"
                :title="t('users.deleteUser')"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Issues Modal -->
    <div
      v-if="showIssuesModal"
      class="fixed inset-0 z-40 bg-black/50 flex items-center justify-center"
      @click.self="showIssuesModal = false"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-2xl max-h-[80vh] bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
        <!-- Modal Header -->
        <div class="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 p-4">
          <div class="flex items-center gap-3">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-full text-xl"
              :class="selectedUser?.type === 'human' ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-purple-100 dark:bg-purple-900/30'"
            >
              {{ selectedUser?.avatar }}
            </div>
            <div>
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ modalTitle }} {{ selectedUser?.username }}
              </h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ modalIssues.length }} {{ t('issues.title').toLowerCase() }}
              </p>
            </div>
          </div>
          <button
            @click="closeIssuesModal"
            class="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Modal Content -->
        <div class="overflow-y-auto max-h-[60vh] p-4">
          <div v-if="loadingIssues" class="flex items-center justify-center py-8">
            <LoadingSpinner />
          </div>
          <div v-else-if="modalIssues.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
            {{ t('common.noData') }}
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="issue in modalIssues"
              :key="issue.id"
              class="rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-700/50"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-mono text-gray-500 dark:text-gray-400">{{ issue.id }}</span>
                    <span
                      class="rounded px-1.5 py-0.5 text-xs font-medium"
                      :class="getStatusClass(issue.status)"
                    >
                      {{ issue.status }}
                    </span>
                    <span
                      class="rounded px-1.5 py-0.5 text-xs font-medium"
                      :class="getPriorityClass(issue.priority)"
                    >
                      {{ issue.priority }}
                    </span>
                  </div>
                  <h4 class="mt-1 font-medium text-gray-900 dark:text-white">{{ issue.title }}</h4>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Agent Modal -->
    <EditAgentModal
      :show="showEditModal"
      :agent="editingAgent"
      @close="closeEditAgent"
      @save="saveAgent"
      @delete="deleteAgent(editingAgent!)"
    />

    <!-- Edit User Modal -->
    <EditUserModal
      :show="showEditUserModal"
      :user="editingUser"
      @close="closeEditUser"
      @save="saveUser"
    />

    <!-- Create User Modal -->
    <CreateUserModal
      :show="showCreateModal"
      @close="showCreateModal = false"
      @save="createUser"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import EditAgentModal from '@/components/users/EditAgentModal.vue'
import EditUserModal from '@/components/users/EditUserModal.vue'
import CreateUserModal from '@/components/users/CreateUserModal.vue'
import { useUsersStore } from '@/stores/usersStore'
import { useIssuesStore } from '@/stores/issuesStore'
import { useUiStore } from '@/stores/uiStore'
import { useToast } from '@/composables/useToast'
import type { User, Issue } from '@/types'

const { t } = useI18n()

const usersStore = useUsersStore()
const issuesStore = useIssuesStore()
const uiStore = useUiStore()
const toast = useToast()

const showIssuesModal = ref(false)
const selectedUser = ref<User | null>(null)
const modalIssues = ref<Issue[]>([])
const loadingIssues = ref(false)
const modalType = ref<'assigned' | 'created' | 'completed'>('assigned')

const showEditModal = ref(false)
const editingAgent = ref<User | null>(null)

const showEditUserModal = ref(false)
const editingUser = ref<User | null>(null)

const showCreateModal = ref(false)

const humans = computed(() => usersStore.humans)
const agents = computed(() => usersStore.agents)
const allIssues = computed(() => issuesStore.issues)

function getUserAssignedCount(userId: string): number {
  return allIssues.value.filter(i => i.assignee === userId && i.status !== 'CLOSED').length
}

function getUserCreatedCount(userId: string): number {
  return allIssues.value.filter(i => i.created_by === userId && i.status !== 'CLOSED').length
}

function getUserCompletedCount(userId: string): number {
  return allIssues.value.filter(i => (i.assignee === userId || i.created_by === userId) && i.status === 'CLOSED').length
}

const modalTitle = computed(() => {
  const map: Record<string, string> = {
    assigned: t('users.assigned'),
    created: t('users.created'),
    completed: t('users.completed'),
  }
  return map[modalType.value] || ''
})

function formatRole(role: string): string {
  const roles: Record<string, string> = {
    'lead-developer': t('users.leadDeveloper'),
    'developer': t('users.developer'),
    'ai-agent': t('users.aiAgentRole'),
  }
  return roles[role] || role
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return t('users.today')
  if (diffDays === 1) return t('users.yesterday')
  if (diffDays < 7) return `${diffDays} ${t('users.daysAgo')}`
  return date.toLocaleDateString(uiStore.locale === 'es' ? 'es-ES' : 'en-US', { day: 'numeric', month: 'short' })
}

function getStatusClass(status: string): string {
  const classes: Record<string, string> = {
    'OPEN': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'IN_PROGRESS': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    'BLOCKED': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    'CLOSED': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  }
  return classes[status] || 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400'
}

function getPriorityClass(priority: string): string {
  const classes: Record<string, string> = {
    'CRITICAL': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    'HIGH': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    'MEDIUM': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    'LOW': 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
  }
  return classes[priority] || 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400'
}

async function openIssuesModal(user: User, type: 'assigned' | 'created' | 'completed') {
  selectedUser.value = user
  modalType.value = type
  showIssuesModal.value = true
  loadingIssues.value = true
  
  try {
    if (allIssues.value.length === 0) {
      await issuesStore.fetchIssues(1, 200)
    }
    const issues = allIssues.value
    if (type === 'assigned') {
      modalIssues.value = issues.filter(issue => issue.assignee === user.id && issue.status !== 'CLOSED')
    } else if (type === 'created') {
      modalIssues.value = issues.filter(issue => issue.created_by === user.id && issue.status !== 'CLOSED')
    } else {
      modalIssues.value = issues.filter(issue => (issue.assignee === user.id || issue.created_by === user.id) && issue.status === 'CLOSED')
    }
  } catch (e) {
    console.error('Failed to fetch issues:', e)
    modalIssues.value = []
  } finally {
    loadingIssues.value = false
  }
}

function closeIssuesModal() {
  showIssuesModal.value = false
  selectedUser.value = null
  modalIssues.value = []
}

function openEditAgent(user: User) {
  editingAgent.value = { ...user }
  showEditModal.value = true
}

function closeEditAgent() {
  showEditModal.value = false
  editingAgent.value = null
}

async function saveAgent(updatedAgent: Record<string, any>) {
  try {
    await usersStore.updateUser(updatedAgent.id, updatedAgent as User)
    closeEditAgent()
  } catch (e) {
    console.error('Failed to save agent:', e)
    toast.error(t('common.error'))
  }
}

function openEditUser(user: User) {
  editingUser.value = { ...user }
  showEditUserModal.value = true
}

function closeEditUser() {
  showEditUserModal.value = false
  editingUser.value = null
}

async function saveUser(updatedUser: User) {
  try {
    await usersStore.updateUser(updatedUser.id, updatedUser)
    closeEditUser()
  } catch (e) {
    console.error('Failed to save user:', e)
    toast.error(t('common.error'))
  }
}

async function deleteUser(user: User) {
  try {
    await usersStore.deleteUser(user.id)
  } catch (e) {
    console.error('Failed to delete user:', e)
    toast.error(t('common.error'))
  }
}

async function deleteAgent(user: User) {
  try {
    await usersStore.deleteUser(user.id)
    closeEditAgent()
  } catch (e) {
    console.error('Failed to delete agent:', e)
    toast.error(t('common.error'))
  }
}

async function createUser(data: { username: string; email: string; role: string; type: string; avatar: string; skills: string[] }) {
  try {
    await usersStore.createUser(data)
    showCreateModal.value = false
  } catch (e) {
    console.error('Failed to create user:', e)
    toast.error(t('common.error'))
  }
}

onMounted(async () => {
  await Promise.all([usersStore.fetchUsers(), issuesStore.fetchIssues(1, 200)])
})
</script>
