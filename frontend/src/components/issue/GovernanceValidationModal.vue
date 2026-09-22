<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    @click.self="$emit('close')"
    role="dialog"
    aria-modal="true"
  >
    <div class="w-full max-w-md rounded-lg bg-white shadow-xl dark:bg-gray-800">
      <div class="flex items-center gap-3 border-b border-gray-200 px-6 py-4 dark:border-gray-700">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
          <svg class="h-5 w-5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ t('governance.title') }}</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ issueTitle }}</p>
        </div>
      </div>

      <div class="px-6 py-4 space-y-4">
        <div v-if="governance.policy_violations.length > 0">
          <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">{{ t('governance.violatedPolicies') }}</h4>
          <div class="space-y-2">
            <div
              v-for="(violation, idx) in governance.policy_violations"
              :key="idx"
              class="flex items-center gap-2 rounded-md bg-red-50 px-3 py-2 dark:bg-red-900/20"
            >
              <svg class="h-4 w-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <span class="text-sm text-red-700 dark:text-red-300">{{ violation }}</span>
            </div>
          </div>
        </div>

        <div>
          <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">{{ t('governance.missingRequirements') }}</h4>
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <svg v-if="governance.has_solution_summary" class="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <svg v-else class="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <span class="text-sm" :class="governance.has_solution_summary ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'">
                {{ t('governance.solutionSummary') }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <svg v-if="governance.has_file_impact" class="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <svg v-else class="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <span class="text-sm" :class="governance.has_file_impact ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'">
                {{ t('governance.fileImpact') }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-2 border-t border-gray-200 px-6 py-4 dark:border-gray-700">
        <button
          class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="$emit('close')"
        >
          {{ t('governance.fixIssues') }}
        </button>
        <button
          class="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
          @click="$emit('override')"
        >
          {{ t('governance.override') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { GovernanceValidation } from '../../types'

const { t } = useI18n()

defineProps<{
  issueTitle: string
  governance: GovernanceValidation
}>()

defineEmits<{
  (e: 'close'): void
  (e: 'override'): void
}>()
</script>
