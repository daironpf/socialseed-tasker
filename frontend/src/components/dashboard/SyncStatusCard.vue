<template>
  <ModuleCard :title="t('boardModules.syncTitle')">
    <p class="text-3xl font-bold text-gray-900 dark:text-gray-100">
      {{ uiStore.pendingSyncCount }}
    </p>
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
      {{ t('boardModules.syncQueued') }}
    </p>
    <div class="mt-3 flex items-center gap-2">
      <span
        class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium"
        :class="modeChipClass"
      >
        <span class="h-1.5 w-1.5 rounded-full" :class="modeDotClass" />
        {{ modeLabel }}
      </span>
      <span class="text-xs text-gray-400 dark:text-gray-500">{{ uiStore.connectionState }}</span>
    </div>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import ModuleCard from './ModuleCard.vue'
import { useUiStore } from '@/stores/uiStore'

const { t } = useI18n()

const uiStore = useUiStore()

const modeLabel = computed(() => {
  const keys = {
    online: 'boardModules.modeOnline',
    degraded: 'boardModules.modeDegraded',
    offline: 'boardModules.modeOffline',
  } as const
  return t(keys[uiStore.networkMode])
})

const modeChipClass = computed(() => {
  const map = {
    online: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    degraded: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    offline: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  } as const
  return map[uiStore.networkMode]
})

const modeDotClass = computed(() => {
  const map = {
    online: 'bg-green-500',
    degraded: 'bg-amber-500',
    offline: 'bg-red-500',
  } as const
  return map[uiStore.networkMode]
})
</script>
