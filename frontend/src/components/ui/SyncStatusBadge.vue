<template>
  <div class="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors" :class="stateClasses">
    <span class="relative flex h-2.5 w-2.5">
      <span
        v-if="uiStore.connectionState === 'SYNCING'"
        class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
        :class="dotPingClass"
      ></span>
      <span class="relative inline-flex h-2.5 w-2.5 rounded-full" :class="dotClass"></span>
    </span>
    <span class="font-medium">{{ stateLabel }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/uiStore'

const { t } = useI18n()
const uiStore = useUiStore()

const stateLabel = computed(() => {
  switch (uiStore.connectionState) {
    case 'SYNCED':
      return t('sync.synced')
    case 'OFFLINE_QUEUED':
      return t('sync.offlineQueued', { count: uiStore.pendingSyncCount })
    case 'SYNCING':
      return t('sync.syncing')
    default:
      return t('sync.synced')
  }
})

const stateClasses = computed(() => {
  switch (uiStore.connectionState) {
    case 'SYNCED':
      return 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
    case 'OFFLINE_QUEUED':
      return 'border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20'
    case 'SYNCING':
      return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20'
    default:
      return 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
  }
})

const dotClass = computed(() => {
  switch (uiStore.connectionState) {
    case 'SYNCED':
      return 'bg-green-500'
    case 'OFFLINE_QUEUED':
      return 'bg-amber-500'
    case 'SYNCING':
      return 'bg-blue-500'
    default:
      return 'bg-green-500'
  }
})

const dotPingClass = computed(() => {
  switch (uiStore.connectionState) {
    case 'SYNCING':
      return 'bg-blue-400'
    default:
      return ''
  }
})
</script>
