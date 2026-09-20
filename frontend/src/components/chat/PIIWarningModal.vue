<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="fixed inset-0 bg-black/50" @click="$emit('cancel')"></div>
      <div class="relative z-10 w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-xl dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-4 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
            <svg class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('pii.warningTitle') }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('pii.warningSubtitle') }}</p>
          </div>
        </div>

        <div class="mb-4 max-h-40 overflow-auto space-y-1.5">
          <div v-for="(d, idx) in detections" :key="idx" class="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs" :class="getSeverityBg(d.severity)">
            <span class="font-medium" :class="getSeverityColor(d.severity)">{{ d.label }}</span>
            <code class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] text-gray-600 dark:bg-gray-800 dark:text-gray-400">{{ d.masked }}</code>
          </div>
        </div>

        <div class="flex gap-2">
          <button @click="$emit('cancel')" class="flex-1 rounded-lg border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700">
            {{ t('pii.cancel') }}
          </button>
          <button @click="$emit('mask')" class="flex-1 rounded-lg border border-amber-300 bg-amber-50 px-4 py-2.5 text-sm font-medium text-amber-700 hover:bg-amber-100 dark:border-amber-700 dark:bg-amber-900/20 dark:text-amber-300 dark:hover:bg-amber-900/30">
            {{ t('pii.maskAndSend') }}
          </button>
          <button v-if="allowConfirm" @click="$emit('confirm')" class="flex-1 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600">
            {{ t('pii.sendAnyway') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { getSeverityColor, getSeverityBg } from '@/utils/piiDetector'
import type { PIIDetection } from '@/utils/piiDetector'

const { t } = useI18n()
defineProps<{
  visible: boolean
  detections: PIIDetection[]
  allowConfirm?: boolean
}>()

defineEmits<{
  cancel: []
  mask: []
  confirm: []
}>()
</script>
