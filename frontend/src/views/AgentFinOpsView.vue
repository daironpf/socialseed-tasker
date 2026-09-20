<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('finops.title') }}</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('finops.subtitle') }}</p>
      </div>
    </div>

    <!-- Budget Alerts -->
    <div v-if="store.criticalAlerts.length > 0" class="rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
      <div class="flex items-center gap-2 mb-3">
        <svg class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
        <h3 class="text-sm font-semibold text-red-800 dark:text-red-200">{{ t('finops.budgetAlerts') }}</h3>
      </div>
      <div class="space-y-2">
        <div v-for="alert in store.criticalAlerts" :key="alert.id" class="flex items-center justify-between rounded-lg bg-white p-3 dark:bg-gray-800">
          <div class="flex items-center gap-3">
            <span class="inline-flex h-2 w-2 rounded-full bg-red-500"></span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ alert.name }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-red-600 dark:text-red-400">${{ alert.currentCost.toFixed(2) }}</span>
            <span class="text-xs text-gray-400">/ ${{ alert.threshold.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ROI Cards -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
      <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-xs text-gray-500 dark:text-gray-400">{{ t('finops.totalTokenCost') }}</div>
        <div class="mt-1 text-2xl font-bold text-gray-900 dark:text-white">${{ store.metrics.totalCost.toFixed(2) }}</div>
        <div class="mt-1 text-xs text-gray-400">{{ store.metrics.totalTokens.toLocaleString() }} {{ t('finops.tokens') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-xs text-gray-500 dark:text-gray-400">{{ t('finops.humanHoursSaved') }}</div>
        <div class="mt-1 text-2xl font-bold text-green-600 dark:text-green-400">{{ store.metrics.estimatedHumanHoursSaved.toFixed(1) }}h</div>
        <div class="mt-1 text-xs text-gray-400">${{ store.metrics.estimatedHumanCostSaved.toLocaleString() }} {{ t('finops.equivalentValue') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-xs text-gray-500 dark:text-gray-400">{{ t('finops.overallROI') }}</div>
        <div class="mt-1 text-2xl font-bold text-blue-600 dark:text-blue-400">{{ store.metrics.overallROI.toFixed(0) }}%</div>
        <div class="mt-1 text-xs text-gray-400">{{ t('finops.returnOnInvestment') }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
        <div class="text-xs text-gray-500 dark:text-gray-400">{{ t('finops.avgCostPerRequest') }}</div>
        <div class="mt-1 text-2xl font-bold text-gray-900 dark:text-white">${{ store.metrics.avgCostPerRequest.toFixed(3) }}</div>
        <div class="mt-1 text-xs text-gray-400">{{ store.metrics.totalRequests }} {{ t('finops.requests') }}</div>
      </div>
    </div>

    <!-- Cost by Model -->
    <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('finops.costByModel') }}</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 dark:border-gray-700">
              <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.model') }}</th>
              <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.provider') }}</th>
              <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.promptTokens') }}</th>
              <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.completionTokens') }}</th>
              <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.cost') }}</th>
              <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.requests') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700/50">
            <tr v-for="m in store.models" :key="m.model" class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
              <td class="px-5 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ m.model }}</td>
              <td class="px-5 py-3 text-sm text-gray-500 dark:text-gray-400">{{ m.provider }}</td>
              <td class="px-5 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ m.promptTokens.toLocaleString() }}</td>
              <td class="px-5 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ m.completionTokens.toLocaleString() }}</td>
              <td class="px-5 py-3 text-right text-sm font-medium text-gray-900 dark:text-white">${{ m.cost.toFixed(2) }}</td>
              <td class="px-5 py-3 text-right text-sm text-gray-500 dark:text-gray-400">{{ m.requests }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Cost by Component Heatmap -->
    <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('finops.costByComponent') }}</h3>
      </div>
      <div class="p-5">
        <div class="space-y-3">
          <div v-for="c in store.components" :key="c.component" class="flex items-center gap-3">
            <span class="w-28 text-xs text-gray-700 dark:text-gray-300 truncate">{{ c.component }}</span>
            <div class="flex-1 h-6 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
              <div class="h-full rounded bg-blue-500 dark:bg-blue-600 transition-all" :style="{ width: componentBarWidth(c.totalCost) }"></div>
            </div>
            <span class="w-16 text-right text-xs font-medium text-gray-900 dark:text-white">${{ c.totalCost.toFixed(2) }}</span>
            <span class="w-12 text-right text-xs text-gray-400">{{ c.requests }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Top Expensive Tasks -->
    <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('finops.topExpensiveTasks') }}</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 dark:border-gray-700">
              <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.issue') }}</th>
              <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.model') }}</th>
              <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.tokens') }}</th>
              <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.cost') }}</th>
              <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.time') }}</th>
              <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{{ t('finops.status') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700/50">
            <tr v-for="t_item in topTasks" :key="t_item.issueId" class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
              <td class="px-5 py-3">
                <div class="text-sm font-medium text-gray-900 dark:text-white">{{ t_item.issueTitle }}</div>
                <div class="text-xs text-gray-400">{{ t_item.issueId }}</div>
              </td>
              <td class="px-5 py-3 text-sm text-gray-500 dark:text-gray-400">{{ t_item.model }}</td>
              <td class="px-5 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ t_item.tokensUsed.toLocaleString() }}</td>
              <td class="px-5 py-3 text-right">
                <span class="text-sm font-medium" :class="t_item.cost >= 5 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'">${{ t_item.cost.toFixed(2) }}</span>
              </td>
              <td class="px-5 py-3 text-right text-sm text-gray-500 dark:text-gray-400">{{ (t_item.executionTimeMs / 1000).toFixed(1) }}s</td>
              <td class="px-5 py-3 text-right">
                <span v-if="t_item.cost >= 5" class="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-700 dark:bg-red-900/30 dark:text-red-300">{{ t('finops.overBudget') }}</span>
                <span v-else class="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-bold text-green-700 dark:bg-green-900/30 dark:text-green-300">{{ t('finops.withinBudget') }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Cost Caps -->
    <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('finops.costCaps') }}</h3>
          </div>
      <div class="p-5 space-y-4">
        <div v-for="cap in store.caps" :key="cap.id" class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-900 dark:text-white">{{ cap.name }}</span>
              <span class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold" :class="cap.scope === 'project' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'">{{ cap.scope }}</span>
              <span class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold" :class="cap.period === 'daily' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'">{{ cap.period }}</span>
            </div>
            <button class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors" :class="cap.isActive ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'" @click="store.toggleCap(cap.id)" :aria-label="cap.isActive ? t('finops.disable') : t('finops.enable')">
              <span class="inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform" :class="cap.isActive ? 'translate-x-4.5' : 'translate-x-0.5'"></span>
            </button>
          </div>
          <div class="flex items-center gap-3">
            <div class="flex-1">
              <div class="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                <div class="h-full rounded-full transition-all" :class="capUsedPercent(cap) >= 90 ? 'bg-red-500' : capUsedPercent(cap) >= 70 ? 'bg-amber-500' : 'bg-blue-500'" :style="{ width: capUsedPercent(cap) + '%' }"></div>
              </div>
            </div>
            <span class="text-xs font-medium text-gray-700 dark:text-gray-300">${{ cap.used.toFixed(2) }} / ${{ cap.limit.toFixed(2) }}</span>
            <span class="text-xs text-gray-400">{{ capUsedPercent(cap).toFixed(0) }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFinopsStore } from '@/stores/finopsStore'
import type { CostByTask } from '@/types/finops'

const { t } = useI18n()
const store = useFinopsStore()

const topTasks = computed(() => [...store.tasks].sort((a: CostByTask, b: CostByTask) => b.cost - a.cost))

const maxComponentCost = computed(() => Math.max(...store.components.map(c => c.totalCost)))

function componentBarWidth(cost: number) {
  return ((cost / maxComponentCost.value) * 100) + '%'
}

function capUsedPercent(cap: { used: number; limit: number }) {
  return Math.min((cap.used / cap.limit) * 100, 100)
}
</script>
