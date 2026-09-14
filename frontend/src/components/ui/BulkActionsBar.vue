<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-full opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-full opacity-0"
    >
      <div class="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
        <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div class="flex items-center gap-3">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ count }} {{ count === 1 ? t('bulkActions.selected') : t('bulkActions.selectedPlural') }}
            </span>
            <button
              class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              @click="$emit('clear')"
            >
              {{ t('bulkActions.clearSelection') }}
            </button>
          </div>
          <div class="flex items-center gap-2">
            <!-- Batch Status Change -->
            <div class="relative" ref="statusDropdownRef">
              <button
                class="flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
                @click="showStatusMenu = !showStatusMenu"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ t('bulkActions.changeStatus') }}
              </button>
              <Transition
                enter-active-class="transition duration-100 ease-out"
                enter-from-class="scale-95 opacity-0"
                enter-to-class="scale-100 opacity-100"
                leave-active-class="transition duration-75 ease-in"
                leave-from-class="scale-100 opacity-100"
                leave-to-class="scale-95 opacity-0"
              >
                <div
                  v-if="showStatusMenu"
                  class="absolute bottom-full right-0 mb-1 w-48 rounded-xl border border-gray-200 bg-white py-1 shadow-xl dark:border-gray-700 dark:bg-gray-900"
                >
                  <button
                    v-for="status in statuses"
                    :key="status.value"
                    class="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                    @click="handleStatusChange(status.value)"
                  >
                    <span class="h-2 w-2 rounded-full" :class="status.color" />
                    {{ status.label }}
                  </button>
                </div>
              </Transition>
            </div>

            <!-- Batch Assign -->
            <div class="relative" ref="assignDropdownRef">
              <button
                class="flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
                @click="showAssignMenu = !showAssignMenu"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                {{ t('bulkActions.assign') }}
              </button>
              <Transition
                enter-active-class="transition duration-100 ease-out"
                enter-from-class="scale-95 opacity-0"
                enter-to-class="scale-100 opacity-100"
                leave-active-class="transition duration-75 ease-in"
                leave-from-class="scale-100 opacity-100"
                leave-to-class="scale-95 opacity-0"
              >
                <div
                  v-if="showAssignMenu"
                  class="absolute bottom-full right-0 mb-1 w-56 rounded-xl border border-gray-200 bg-white py-1 shadow-xl dark:border-gray-700 dark:bg-gray-900"
                >
                  <button
                    class="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                    @click="handleAssign('')"
                  >
                    <span class="text-gray-400">-</span>
                    {{ t('bulkActions.unassign') }}
                  </button>
                  <button
                    v-for="user in users"
                    :key="user.id"
                    class="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                    @click="handleAssign(user.id)"
                  >
                    <span>{{ user.avatar || '👤' }}</span>
                    {{ user.username }}
                    <span v-if="user.type === 'agent'" class="ml-auto rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">AI</span>
                  </button>
                </div>
              </Transition>
            </div>

            <!-- Batch Delete -->
            <button
              class="flex items-center gap-1.5 rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 dark:border-red-600 dark:bg-gray-700 dark:text-red-400 dark:hover:bg-red-900/30"
              @click="showDeleteModal = true"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              {{ t('bulkActions.delete') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Delete Confirmation Modal -->
  <div
    v-if="showDeleteModal"
    class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center"
    @click.self="showDeleteModal = false"
  >
    <div class="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
      <div class="flex items-center gap-3 mb-4">
        <div class="flex-shrink-0 rounded-full bg-red-100 p-2 dark:bg-red-900/30">
          <svg class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('bulkActions.confirmDelete') }}</h3>
      </div>
      <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
        {{ t('bulkActions.deleteWarning', { count }) }}
      </p>
      <div class="flex justify-end gap-3">
        <button
          type="button"
          class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
          @click="showDeleteModal = false"
        >
          {{ t('issues.cancel') }}
        </button>
        <button
          type="button"
          class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600"
          @click="confirmDelete"
        >
          {{ t('bulkActions.delete') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUsersStore } from '@/stores/usersStore'

const { t } = useI18n()
const usersStore = useUsersStore()

defineProps<{
  count: number
}>()

const emit = defineEmits<{
  batchStatus: [status: string]
  batchAssign: [userId: string]
  batchDelete: []
  clear: []
}>()

const users = computed(() => usersStore.users)
const showStatusMenu = ref(false)
const showAssignMenu = ref(false)
const showDeleteModal = ref(false)
const statusDropdownRef = ref<HTMLElement | null>(null)
const assignDropdownRef = ref<HTMLElement | null>(null)

const statuses = computed(() => [
  { value: 'OPEN', label: t('issues.open'), color: 'bg-blue-500' },
  { value: 'IN_PROGRESS', label: t('issues.inProgress'), color: 'bg-yellow-500' },
  { value: 'BLOCKED', label: t('issues.blocked'), color: 'bg-red-500' },
  { value: 'CLOSED', label: t('issues.closed'), color: 'bg-green-500' },
])

function handleStatusChange(status: string) {
  emit('batchStatus', status)
  showStatusMenu.value = false
}

function handleAssign(userId: string) {
  emit('batchAssign', userId)
  showAssignMenu.value = false
}

function confirmDelete() {
  emit('batchDelete')
  showDeleteModal.value = false
}

function handleClickOutside(e: MouseEvent) {
  if (statusDropdownRef.value && !statusDropdownRef.value.contains(e.target as Node)) {
    showStatusMenu.value = false
  }
  if (assignDropdownRef.value && !assignDropdownRef.value.contains(e.target as Node)) {
    showAssignMenu.value = false
  }
}

onMounted(async () => {
  await usersStore.fetchUsers()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
