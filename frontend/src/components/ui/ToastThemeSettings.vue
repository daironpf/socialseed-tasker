<template>
  <div class="flex gap-1.5">
    <button
      v-for="option in options"
      :key="option.key"
      class="flex-1 rounded-lg border p-1.5 text-center transition-colors"
      :class="uiStore.toastTheme === option.key
        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
        : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600'"
      :aria-pressed="uiStore.toastTheme === option.key"
      @click="uiStore.setToastTheme(option.key)"
    >
      <div class="mb-1 h-8 overflow-hidden rounded border border-gray-200 bg-gray-50 p-1 dark:border-gray-600 dark:bg-gray-900">
        <div class="mb-0.5 flex items-center gap-1">
          <span class="h-1.5 w-1.5 rounded-full" :class="option.previewDot" />
          <span class="h-1 w-8 rounded-full" :class="option.previewLine" />
        </div>
        <div class="flex items-center gap-1">
          <span class="h-1 w-6 rounded-full bg-gray-300 dark:bg-gray-600" />
          <span class="h-1 flex-1 rounded-full" :class="option.previewBar" />
        </div>
      </div>
      <span
        class="text-[10px] font-semibold"
        :class="uiStore.toastTheme === option.key ? 'text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'"
      >
        {{ t(`toastTheme.${option.key}`) }}
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useUiStore, type ToastTheme } from '@/stores/uiStore'

const { t } = useI18n()
const uiStore = useUiStore()

const options: Array<{ key: ToastTheme; previewDot: string; previewLine: string; previewBar: string }> = [
  {
    key: 'minimal',
    previewDot: 'bg-gray-400',
    previewLine: 'bg-gray-400',
    previewBar: 'bg-gray-300 dark:bg-gray-600',
  },
  {
    key: 'rich',
    previewDot: 'bg-green-500',
    previewLine: 'bg-green-400',
    previewBar: 'bg-green-300 dark:bg-green-700',
  },
  {
    key: 'enterprise',
    previewDot: 'bg-blue-500',
    previewLine: 'bg-blue-500',
    previewBar: 'bg-blue-400',
  },
]
</script>
