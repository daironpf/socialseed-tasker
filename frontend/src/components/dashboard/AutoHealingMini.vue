<template>
  <ModuleCard :title="t('boardModules.autoHealingTitle')">
    <div class="grid grid-cols-3 gap-3 text-center">
      <div>
        <p class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ counts.running }}</p>
        <p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{{ t('autoHealing.active') }}</p>
      </div>
      <div>
        <p class="text-2xl font-bold text-green-600 dark:text-green-400">{{ counts.completed }}</p>
        <p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{{ t('autoHealing.completed') }}</p>
      </div>
      <div>
        <p class="text-2xl font-bold text-red-600 dark:text-red-400">{{ counts.failed }}</p>
        <p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{{ t('autoHealing.failed') }}</p>
      </div>
    </div>

    <div
      v-if="currentRun && currentStage"
      class="mt-4 flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-900/50"
    >
      <span class="h-2 w-2 flex-shrink-0 animate-pulse rounded-full bg-amber-500" />
      <span class="min-w-0 flex-1 truncate text-xs font-medium text-gray-700 dark:text-gray-300">
        {{ t(`autoHealing.stages.${currentStage.id}`) }}
      </span>
      <span class="flex-shrink-0 text-[10px] text-gray-400">{{ currentRun.id }}</span>
    </div>
    <p v-else class="mt-4 text-xs text-gray-400">{{ t('boardModules.autoHealingIdle') }}</p>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import ModuleCard from './ModuleCard.vue'
import { useAutoHealingStore } from '@/stores/autoHealingStore'

const { t } = useI18n()

const autoHealingStore = useAutoHealingStore()

const counts = computed(() => ({
  running: autoHealingStore.runs.filter((r) => r.status === 'running').length,
  completed: autoHealingStore.runs.filter((r) => r.status === 'completed').length,
  failed: autoHealingStore.runs.filter((r) => r.status === 'failed').length,
}))

const currentRun = computed(() => autoHealingStore.runs.find((r) => r.status === 'running'))

const currentStage = computed(() =>
  currentRun.value ? currentRun.value.stages[currentRun.value.currentStageIndex] : undefined
)
</script>
