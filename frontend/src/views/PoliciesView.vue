<template>
  <main class="flex-1 overflow-auto p-6">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('policies.title') }}</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ t('policies.subtitle') }}
        </p>
      </div>
      <button
        class="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
        @click="showCreateModal = true"
      >
        {{ t('policies.newPolicy') }}
      </button>
    </div>

    <div v-if="store.loading" class="flex justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
    </div>

    <div v-else-if="store.error" class="rounded-md bg-red-50 p-4 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-200">Error loading policies</h3>
          <div class="mt-2 text-sm text-red-700 dark:text-red-300">{{ store.error }}</div>
        </div>
      </div>
    </div>

    <div v-else-if="store.policies.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
      <div class="rounded-full bg-gray-100 p-4 dark:bg-gray-800">
        <svg class="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">{{ t('policies.noPolicies') }}</h3>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400 max-w-md">
        {{ t('policies.noPoliciesDesc') }}
      </p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div
        v-for="policy in store.policies"
        :key="policy.id"
        class="rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800 flex flex-col"
      >
        <div class="border-b border-gray-100 px-5 py-4 dark:border-gray-700 flex justify-between items-start">
          <h3 class="font-medium text-gray-900 dark:text-white truncate pr-2" :title="policy.name">
            {{ policy.name }}
          </h3>
          <div class="flex items-center gap-2">
            <span 
              class="inline-flex flex-shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
              :class="policy.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'"
            >
              {{ policy.is_active ? t('policies.active') : t('policies.inactive') }}
            </span>
            <button
              class="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
              @click="openEditModal(policy)"
              title="Edit"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              class="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/30 dark:hover:text-red-400"
              @click="confirmDelete(policy)"
              :title="t('policies.delete')"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        
        <div class="p-5 flex-1 flex flex-col">
          <div class="prose prose-sm dark:prose-invert max-w-none flex-1 text-gray-600 dark:text-gray-300 mb-4 whitespace-pre-line">
            {{ policy.description || t('policies.noDescription') }}
          </div>
          
          <div class="mt-auto space-y-2 text-sm">
            <div class="flex justify-between border-t border-gray-100 pt-3 dark:border-gray-700">
              <span class="text-gray-500 dark:text-gray-400">{{ t('policies.targetScope') }}</span>
              <span class="font-medium text-gray-700 dark:text-gray-300">{{ policy.target_scope }}</span>
            </div>
            
            <div v-if="policy.rules && policy.rules.length > 0" class="flex justify-between border-t border-gray-100 pt-2 dark:border-gray-700">
              <span class="text-gray-500 dark:text-gray-400">{{ t('policies.rulesCount') }}</span>
              <span class="font-medium text-gray-700 dark:text-gray-300">{{ policy.rules.length }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Policy Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-40 bg-black/50 flex items-center justify-center"
      @click.self="showCreateModal = false"
    >
      <div class="w-full max-w-md rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {{ t('policies.newPolicy') }}
        </h3>
        <form @submit.prevent="submitPolicy" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.name') }} *</label>
            <input 
              v-model="form.name" 
              required 
              placeholder="ej: no-circular-deps"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100" 
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.description') }}</label>
            <textarea 
              v-model="form.description" 
              rows="2"
              placeholder="Policy description..."
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            ></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.rule') }} *</label>
            <select 
              v-model="form.rule" 
              required
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="">{{ t('policies.selectRule') }}</option>
              <option value="no_circular_dependencies">{{ t('policies.noCircularDependencies') }}</option>
              <option value="max_dependencies">{{ t('policies.maxDependencies') }}</option>
              <option value="required_labels">{{ t('policies.requiredLabels') }}</option>
              <option value="component_ownership">{{ t('policies.componentOwnership') }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.level') }}</label>
            <select 
              v-model="form.level" 
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="SOFT">{{ t('policies.soft') }}</option>
              <option value="HARD">{{ t('policies.hard') }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.targetScope') }}</label>
            <input 
              v-model="form.target_scope" 
              placeholder="ej: project"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100" 
            />
          </div>
          <div v-if="createError" class="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
            {{ createError }}
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
              @click="showCreateModal = false"
            >
              {{ t('issues.cancel') }}
            </button>
            <button
              type="submit"
              :disabled="creating"
              class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50 dark:bg-brand-500 dark:hover:bg-brand-600"
            >
              {{ creating ? t('policies.creating') : t('policies.createPolicy') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Policy Modal -->
    <div
      v-if="showEditModal"
      class="fixed inset-0 z-40 bg-black/50 flex items-center justify-center"
      @click.self="showEditModal = false"
    >
      <div class="w-full max-w-md rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {{ t('policies.editPolicy') }}
        </h3>
        <form @submit.prevent="submitEdit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.name') }} *</label>
            <input 
              v-model="editForm.name" 
              required 
              placeholder="ej: no-circular-deps"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100" 
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.description') }}</label>
            <textarea 
              v-model="editForm.description" 
              rows="2"
              placeholder="Policy description..."
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            ></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.rule') }} *</label>
            <select 
              v-model="editForm.rule" 
              required
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="">{{ t('policies.selectRule') }}</option>
              <option value="no_circular_dependencies">{{ t('policies.noCircularDependencies') }}</option>
              <option value="max_dependencies">{{ t('policies.maxDependencies') }}</option>
              <option value="required_labels">{{ t('policies.requiredLabels') }}</option>
              <option value="component_ownership">{{ t('policies.componentOwnership') }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.level') }}</label>
            <select 
              v-model="editForm.level" 
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="SOFT">{{ t('policies.soft') }}</option>
              <option value="HARD">{{ t('policies.hard') }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('policies.targetScope') }}</label>
            <input 
              v-model="editForm.target_scope" 
              placeholder="ej: project"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100" 
            />
          </div>
          <div class="flex items-center gap-2">
            <input
              type="checkbox"
              v-model="editForm.is_active"
              id="edit-is-active"
              class="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
            />
            <label for="edit-is-active" class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('policies.active') }}</label>
          </div>
          <div v-if="editError" class="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
            {{ editError }}
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
              @click="showEditModal = false"
            >
              {{ t('issues.cancel') }}
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50 dark:bg-brand-500 dark:hover:bg-brand-600"
            >
              {{ saving ? t('policies.saving') : t('policies.saveChanges') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 z-40 bg-black/50 flex items-center justify-center"
      @click.self="showDeleteModal = false"
    >
      <div class="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
        <div class="flex items-center gap-3 mb-4">
          <div class="flex-shrink-0 rounded-full bg-red-100 p-2 dark:bg-red-900/30">
            <svg class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('policies.confirmDelete') }}</h3>
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {{ t('policies.deleteWarning', { name: deletingPolicy?.name }) }}
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
            :disabled="deleting"
            class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 dark:bg-red-500 dark:hover:bg-red-600"
            @click="executeDelete"
          >
            {{ deleting ? t('policies.deleting') : t('policies.delete') }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePoliciesStore } from '@/stores/policiesStore'
import { useToast } from '@/composables/useToast'
import type { Policy } from '@/types'

const { t } = useI18n()
const toast = useToast()

const store = usePoliciesStore()

const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref<string | null>(null)

const form = ref({
  name: '',
  description: '',
  rule: '',
  level: 'SOFT',
  target_scope: 'project',
})

const showEditModal = ref(false)
const saving = ref(false)
const editError = ref<string | null>(null)
const editingPolicy = ref<Policy | null>(null)

const editForm = ref({
  name: '',
  description: '',
  rule: '',
  level: 'SOFT',
  target_scope: 'project',
  is_active: true,
})

function openEditModal(policy: Policy) {
  editingPolicy.value = policy
  editForm.value = {
    name: policy.name,
    description: policy.description || '',
    rule: policy.rules?.[0]?.type || '',
    level: policy.rules?.[0]?.severity || 'SOFT',
    target_scope: policy.target_scope || 'project',
    is_active: policy.is_active,
  }
  showEditModal.value = true
}

async function submitEdit() {
  if (!editingPolicy.value) return
  saving.value = true
  editError.value = null
  const updated = await store.updatePolicy(editingPolicy.value.id, {
    name: editForm.value.name,
    description: editForm.value.description,
    rule: editForm.value.rule,
    level: editForm.value.level,
    target_scope: editForm.value.target_scope,
    is_active: editForm.value.is_active,
  })
  if (updated) {
    showEditModal.value = false
    editingPolicy.value = null
  } else {
    editError.value = store.error || 'Failed to update policy'
  }
  saving.value = false
}

async function submitPolicy() {
  creating.value = true
  createError.value = null
  const policy = await store.createPolicy(form.value)
  if (policy) {
    showCreateModal.value = false
    form.value = { name: '', description: '', rule: '', level: 'SOFT', target_scope: 'project' }
    toast.success(t('policies.created'))
  } else {
    createError.value = store.error || 'Failed to create policy'
  }
  creating.value = false
}

const showDeleteModal = ref(false)
const deleting = ref(false)
const deletingPolicy = ref<Policy | null>(null)

function confirmDelete(policy: Policy) {
  deletingPolicy.value = policy
  showDeleteModal.value = true
}

async function executeDelete() {
  if (!deletingPolicy.value) return
  deleting.value = true
  const success = await store.deletePolicy(deletingPolicy.value.id)
  if (success) {
    toast.success(t('policies.deleted'))
    showDeleteModal.value = false
  } else {
    toast.error(store.error || t('policies.failedDelete'))
  }
  deleting.value = false
}

onMounted(() => store.fetchPolicies())
</script>
