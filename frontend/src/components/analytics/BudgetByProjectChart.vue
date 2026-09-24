<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('analytics.budgetTitle') }}</h3>
        <p class="text-xs text-gray-400">{{ t('analytics.budgetSubtitle', { days: rangeDays }) }}</p>
      </div>
      <span class="text-xs font-semibold text-gray-500 dark:text-gray-400">
        ${{ totalSpent }} / ${{ totalBudget }}
      </span>
    </div>

    <div v-if="items.length" class="space-y-4">
      <div v-for="item in items" :key="item.projectId">
        <div class="mb-1 flex items-center justify-between text-xs">
          <span class="font-medium text-gray-700 dark:text-gray-300">{{ item.label }}</span>
          <span class="text-gray-500 dark:text-gray-400">
            ${{ item.spent }} / ${{ item.budget }}
            <strong :class="pctClass(item)">{{ pct(item) }}%</strong>
          </span>
        </div>
        <div class="h-3 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
          <div
            class="h-full rounded-full transition-all"
            :class="barClass(item)"
            :style="{ width: Math.min(100, pct(item)) + '%' }"
          />
        </div>
      </div>
    </div>
    <div v-else class="py-10 text-center text-sm text-gray-400">{{ t('common.noData') }}</div>

    <div class="mt-4 flex flex-wrap gap-3 border-t border-gray-100 pt-3 text-[11px] dark:border-gray-700/60">
      <span class="flex items-center gap-1.5 text-gray-500 dark:text-gray-400">
        <span class="h-2.5 w-2.5 rounded-full bg-emerald-500" /> {{ t('analytics.under70') }}
      </span>
      <span class="flex items-center gap-1.5 text-gray-500 dark:text-gray-400">
        <span class="h-2.5 w-2.5 rounded-full bg-amber-500" /> {{ t('analytics.over70') }}
      </span>
      <span class="flex items-center gap-1.5 text-gray-500 dark:text-gray-400">
        <span class="h-2.5 w-2.5 rounded-full bg-red-500" /> {{ t('analytics.over90') }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ProjectBudget } from '@/types/analytics'

const props = defineProps<{
  items: ProjectBudget[]
  rangeDays: number
}>()

const { t } = useI18n()

const totalSpent = computed(() => Math.round(props.items.reduce((s, i) => s + i.spent, 0) * 100) / 100)
const totalBudget = computed(() => Math.round(props.items.reduce((s, i) => s + i.budget, 0) * 100) / 100)

function pct(item: ProjectBudget): number {
  if (!item.budget) return 0
  return Math.round((item.spent / item.budget) * 100)
}

function pctClass(item: ProjectBudget): string {
  const value = pct(item)
  if (value >= 90) return 'text-red-600 dark:text-red-400'
  if (value >= 70) return 'text-amber-600 dark:text-amber-400'
  return 'text-emerald-600 dark:text-emerald-400'
}

function barClass(item: ProjectBudget): string {
  const value = pct(item)
  if (value >= 90) return 'bg-red-500'
  if (value >= 70) return 'bg-amber-500'
  return 'bg-emerald-500'
}
</script>
