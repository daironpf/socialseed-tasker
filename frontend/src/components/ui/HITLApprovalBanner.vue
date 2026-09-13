<template>
  <div class="hitl-banner rounded-lg border-2 border-amber-300 dark:border-amber-600 bg-amber-50 dark:bg-amber-900/20 overflow-hidden">
    <div class="flex items-center gap-3 px-4 py-3 bg-amber-100 dark:bg-amber-900/30 border-b border-amber-200 dark:border-amber-700">
      <div class="flex-shrink-0">
        <svg class="h-6 w-6 text-amber-600 dark:text-amber-400 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <div class="flex-1">
        <h3 class="text-sm font-semibold text-amber-800 dark:text-amber-200">{{ t('hitl.title') }}</h3>
        <p class="text-xs text-amber-600 dark:text-amber-400">{{ t('hitl.description') }}</p>
      </div>
    </div>

    <div class="p-4 space-y-4">
      <div v-if="actionDetails" class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
        <div class="flex items-center gap-2 mb-3">
          <span class="rounded bg-amber-100 dark:bg-amber-900/30 px-2 py-0.5 text-[10px] font-bold text-amber-700 dark:text-amber-300">
            {{ actionDetails.severity?.toUpperCase() || 'CRITICAL' }}
          </span>
          <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ actionDetails.type }}</span>
        </div>

        <div class="mb-3">
          <label class="block text-[10px] font-medium text-gray-400 dark:text-gray-500 mb-1 uppercase tracking-wider">
            {{ t('hitl.command') }}
          </label>
          <pre class="rounded bg-gray-50 dark:bg-gray-900 p-3 text-xs font-mono text-gray-800 dark:text-gray-200 overflow-x-auto border border-gray-200 dark:border-gray-700">{{ actionDetails.command }}</pre>
        </div>

        <div v-if="actionDetails.target" class="mb-3">
          <label class="block text-[10px] font-medium text-gray-400 dark:text-gray-500 mb-1 uppercase tracking-wider">
            {{ t('hitl.target') }}
          </label>
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ actionDetails.target }}</span>
        </div>

        <div v-if="actionDetails.description" class="text-sm text-gray-600 dark:text-gray-400">
          {{ actionDetails.description }}
        </div>
      </div>

      <div v-if="showRejectForm" class="space-y-2">
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('hitl.feedbackLabel') }}</label>
        <textarea
          v-model="rejectFeedback"
          rows="3"
          :placeholder="t('hitl.feedbackPlaceholder')"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
      </div>

      <div v-if="showModifyForm" class="space-y-2">
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400">{{ t('hitl.modifyLabel') }}</label>
        <textarea
          v-model="modifyParams"
          rows="3"
          :placeholder="t('hitl.modifyPlaceholder')"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-mono focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
      </div>

      <div v-if="!showRejectForm && !showModifyForm" class="flex gap-2">
        <button
          class="flex-1 rounded-md bg-green-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
          @click="approve"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          {{ t('hitl.approve') }}
        </button>
        <button
          class="rounded-md bg-red-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
          @click="showRejectForm = true"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          {{ t('hitl.reject') }}
        </button>
        <button
          class="rounded-md border border-gray-300 dark:border-gray-600 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
          @click="showModifyForm = true"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          {{ t('hitl.modify') }}
        </button>
      </div>

      <div v-else class="flex gap-2">
        <button
          class="flex-1 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          @click="submitModification"
        >
          {{ t('hitl.submitModification') }}
        </button>
        <button
          class="rounded-md border border-gray-300 dark:border-gray-600 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          @click="cancelForms"
        >
          {{ t('common.cancel') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface ActionDetails {
  type: string
  command: string
  target?: string
  description?: string
  severity?: string
  payload?: Record<string, unknown>
}

defineProps<{
  actionDetails?: ActionDetails | null
}>()

const emit = defineEmits<{
  approve: []
  reject: [feedback: string]
  modify: [params: string]
}>()

const showRejectForm = ref(false)
const showModifyForm = ref(false)
const rejectFeedback = ref('')
const modifyParams = ref('')

function approve() {
  emit('approve')
}

function submitModification() {
  if (showRejectForm.value) {
    emit('reject', rejectFeedback.value)
  } else if (showModifyForm.value) {
    emit('modify', modifyParams.value)
  }
  cancelForms()
}

function cancelForms() {
  showRejectForm.value = false
  showModifyForm.value = false
  rejectFeedback.value = ''
  modifyParams.value = ''
}
</script>
