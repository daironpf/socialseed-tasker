<template>
  <div class="flex flex-wrap items-center gap-2">
    <!-- Zoom controls -->
    <div class="flex items-center rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <button
        class="flex h-8 w-8 items-center justify-center rounded-l-lg text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
        :aria-label="t('graphExplorer.zoomIn')"
        :title="t('graphExplorer.zoomIn')"
        @click="$emit('zoom-in')"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M11 18a7 7 0 100-14 7 7 0 000 14zM11 8v6M8 11h6" />
        </svg>
      </button>
      <button
        class="flex h-8 w-8 items-center justify-center text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
        :aria-label="t('graphExplorer.zoomOut')"
        :title="t('graphExplorer.zoomOut')"
        @click="$emit('zoom-out')"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M11 18a7 7 0 100-14 7 7 0 000 14zM8 11h6" />
        </svg>
      </button>
      <button
        class="flex h-8 w-8 items-center justify-center rounded-r-lg text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
        :aria-label="t('graphExplorer.fit')"
        :title="t('graphExplorer.fit')"
        @click="$emit('fit')"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
      </button>
    </div>

    <div class="border-l border-gray-300 dark:border-gray-600"></div>

    <!-- Cluster toggle -->
    <button
      class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs transition-colors"
      :class="clustered
        ? 'bg-violet-600 text-white hover:bg-violet-700'
        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'"
      @click="$emit('update:clustered', !clustered)"
    >
      <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      {{ clustered ? t('graphExplorer.clusterOn') : t('graphExplorer.cluster') }}
    </button>

    <div class="border-l border-gray-300 dark:border-gray-600"></div>

    <!-- Impact path tracing -->
    <div class="flex flex-wrap items-center gap-1.5">
      <select
        :value="traceSource"
        :aria-label="t('graphExplorer.traceSource')"
        class="max-w-[150px] rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
        @change="$emit('update:traceSource', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">{{ t('graphExplorer.traceSource') }}</option>
        <option v-for="opt in traceOptions" :key="opt.id" :value="opt.id">{{ opt.label }}</option>
      </select>
      <svg class="h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
      </svg>
      <select
        :value="traceTarget"
        :aria-label="t('graphExplorer.traceTarget')"
        class="max-w-[150px] rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
        @change="$emit('update:traceTarget', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">{{ t('graphExplorer.traceTarget') }}</option>
        <option v-for="opt in traceOptions" :key="opt.id" :value="opt.id">{{ opt.label }}</option>
      </select>
      <button
        class="rounded-lg bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-700"
        @click="$emit('trace')"
      >
        {{ t('graphExplorer.trace') }}
      </button>
      <button
        v-if="traceMessage"
        class="rounded-lg px-2 py-1.5 text-xs text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
        @click="$emit('clear-trace')"
      >
        {{ t('graphExplorer.clearTrace') }}
      </button>
      <span
        v-if="traceMessage"
        class="text-xs"
        :class="traceOk ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'"
      >
        {{ traceMessage }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { TraceSelectOption } from '@/types/graphExplorer'

defineProps<{
  clustered: boolean
  traceSource: string
  traceTarget: string
  traceOptions: TraceSelectOption[]
  traceMessage: string
  traceOk: boolean
}>()

defineEmits<{
  'zoom-in': []
  'zoom-out': []
  fit: []
  'update:clustered': [value: boolean]
  'update:traceSource': [value: string]
  'update:traceTarget': [value: string]
  trace: []
  'clear-trace': []
}>()

const { t } = useI18n()
</script>
