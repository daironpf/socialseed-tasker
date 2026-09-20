<template>
  <div v-if="detections.length > 0" class="space-y-1.5">
    <div v-for="(d, idx) in detections" :key="idx"
      class="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs"
      :class="getSeverityBg(d.severity)">
      <svg class="h-4 w-4 shrink-0" :class="getSeverityColor(d.severity)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span class="font-medium" :class="getSeverityColor(d.severity)">{{ d.label }}</span>
      <span class="text-gray-500 dark:text-gray-400">{{ t('pii.detected') }}</span>
      <code class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] text-gray-600 dark:bg-gray-800 dark:text-gray-400">{{ d.masked }}</code>
      <span class="ml-auto text-[10px] uppercase font-bold" :class="getSeverityColor(d.severity)">{{ d.severity }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { getSeverityColor, getSeverityBg } from '@/utils/piiDetector'
import type { PIIDetection } from '@/utils/piiDetector'

const { t } = useI18n()
defineProps<{ detections: PIIDetection[] }>()
</script>
