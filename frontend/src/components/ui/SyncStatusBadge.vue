<template>
  <button
    type="button"
    class="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors"
    :class="stateClasses"
    :aria-label="t('syncQueue.title')"
    :title="t('syncQueue.title')"
    @click="drawerOpen = true"
  >
    <span class="relative flex h-2.5 w-2.5">
      <span
        v-if="uiStore.connectionState === 'SYNCING'"
        class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
        :class="dotPingClass"
      ></span>
      <span class="relative inline-flex h-2.5 w-2.5 rounded-full" :class="dotClass"></span>
    </span>
    <span class="font-medium">{{ stateLabel }}</span>
    <span
      v-if="uiStore.pendingSyncCount"
      class="rounded-full bg-white/70 px-1.5 text-[10px] font-bold text-amber-700 dark:bg-black/40 dark:text-amber-300"
    >
      {{ uiStore.pendingSyncCount }}
    </span>
  </button>
  <SyncQueueDrawer v-if="drawerOpen" @close="drawerOpen = false" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/uiStore'
import SyncQueueDrawer from '@/components/sync/SyncQueueDrawer.vue'

const { t } = useI18n()
const uiStore = useUiStore()

const drawerOpen = ref(false)

const stateLabel = computed(() => {
  if (uiStore.networkMode === 'offline' && uiStore.connectionState === 'SYNCED' && !uiStore.syncQueue.length) {
    return t('offline.offline')
  }
  switch (uiStore.connectionState) {
    case 'OFFLINE_QUEUED':
      return t('sync.offlineQueued', { count: uiStore.pendingSyncCount })
    case 'SYNCING':
      return t('sync.syncing')
    case 'DEGRADED':
      return t('offline.degraded')
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
    case 'DEGRADED':
      return 'border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20'
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
    case 'DEGRADED':
      return 'bg-amber-500'
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
