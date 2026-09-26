<template>
  <ModuleCard :title="t('boardModules.budgetTitle')">
    <p class="text-3xl font-bold" :class="valueClass">
      ${{ finopsStore.metrics.totalCost.toFixed(2) }}
    </p>
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
      {{ budgetSubtitle }}
    </p>
    <div class="mt-3 flex items-center gap-2">
      <span
        v-if="alertCount > 0"
        class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
        :class="alertChipClass"
      >
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M5.636 18.364a9 9 0 1112.728 0" />
        </svg>
        {{ t('boardModules.budgetAlerts', { count: alertCount }) }}
      </span>
      <span
        v-else
        class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/40 dark:text-green-300"
      >
        {{ t('boardModules.budgetOk') }}
      </span>
    </div>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import ModuleCard from './ModuleCard.vue'
import { useFinopsStore } from '@/stores/finopsStore'

const { t } = useI18n()

const finopsStore = useFinopsStore()

const alertCount = computed(
  () => finopsStore.criticalAlerts.length + finopsStore.warningAlerts.length
)

const budgetSubtitle = computed(() =>
  t('boardModules.budgetSubtitle', { count: finopsStore.alerts.length })
)

const valueClass = computed(() =>
  finopsStore.criticalAlerts.length > 0
    ? 'text-red-600 dark:text-red-400'
    : 'text-gray-900 dark:text-gray-100'
)

const alertChipClass = computed(() =>
  finopsStore.criticalAlerts.length > 0
    ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
    : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
)
</script>
