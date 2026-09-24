<template>
  <div class="flex items-center gap-1 rounded-lg border border-gray-200 bg-white p-0.5 dark:border-gray-700 dark:bg-gray-800">
    <span class="px-1.5 text-[10px] font-semibold uppercase text-gray-400">{{ t('offline.networkLabel') }}</span>
    <button
      v-for="mode in modes"
      :key="mode.value"
      class="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-colors"
      :class="uiStore.networkMode === mode.value
        ? mode.activeClass
        : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200'"
      :aria-pressed="uiStore.networkMode === mode.value"
      :title="t(`offline.${mode.value}`)"
      @click="uiStore.setNetworkMode(mode.value)"
    >
      <span class="h-1.5 w-1.5 rounded-full" :class="mode.dotClass" />
      {{ t(`offline.${mode.value}`) }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useUiStore, type NetworkMode } from '@/stores/uiStore'

const { t } = useI18n()
const uiStore = useUiStore()

const modes: Array<{
  value: NetworkMode
  dotClass: string
  activeClass: string
}> = [
  {
    value: 'online',
    dotClass: 'bg-emerald-500',
    activeClass: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  },
  {
    value: 'degraded',
    dotClass: 'bg-amber-500',
    activeClass: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  },
  {
    value: 'offline',
    dotClass: 'bg-red-500',
    activeClass: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  },
]
</script>
