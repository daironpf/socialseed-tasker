<template>
  <div class="token-metrics rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
    <div class="flex items-center justify-between mb-3">
      <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{{ t('tokens.title') }}</h4>
      <span v-if="exceedsBudget" class="flex items-center gap-1 rounded-full bg-red-100 dark:bg-red-900/30 px-2 py-0.5 text-[10px] font-bold text-red-700 dark:text-red-300">
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        {{ t('tokens.overBudget') }}
      </span>
    </div>

    <div class="grid grid-cols-3 gap-3 mb-4">
      <div class="text-center">
        <div class="text-lg font-bold text-blue-600 dark:text-blue-400">{{ formatTokens(promptTokens) }}</div>
        <div class="text-[10px] text-gray-400 uppercase tracking-wider">{{ t('tokens.prompt') }}</div>
      </div>
      <div class="text-center">
        <div class="text-lg font-bold text-green-600 dark:text-green-400">{{ formatTokens(completionTokens) }}</div>
        <div class="text-[10px] text-gray-400 uppercase tracking-wider">{{ t('tokens.completion') }}</div>
      </div>
      <div class="text-center">
        <div class="text-lg font-bold text-purple-600 dark:text-purple-400">{{ formatCost(totalCost) }}</div>
        <div class="text-[10px] text-gray-400 uppercase tracking-wider">{{ t('tokens.cost') }}</div>
      </div>
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs">
        <span class="text-gray-500 dark:text-gray-400">{{ t('tokens.model') }}</span>
        <span class="font-medium text-gray-700 dark:text-gray-300">{{ modelInfo?.model || model }}</span>
      </div>
      <div class="flex items-center justify-between text-xs">
        <span class="text-gray-500 dark:text-gray-400">{{ t('tokens.provider') }}</span>
        <span class="font-medium text-gray-700 dark:text-gray-300">{{ modelInfo?.provider || '—' }}</span>
      </div>
      <div v-if="budget" class="flex items-center justify-between text-xs">
        <span class="text-gray-500 dark:text-gray-400">{{ t('tokens.budget') }}</span>
        <span class="font-medium" :class="exceedsBudget ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300'">
          {{ formatCost(budget) }}
        </span>
      </div>
    </div>

    <div v-if="budget" class="mt-3">
      <div class="flex items-center justify-between text-[10px] text-gray-400 mb-1">
        <span>{{ formatCost(totalCost) }}</span>
        <span>{{ formatCost(budget) }}</span>
      </div>
      <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all"
          :class="exceedsBudget ? 'bg-red-500' : budgetUsage > 70 ? 'bg-amber-500' : 'bg-green-500'"
          :style="{ width: Math.min(budgetUsage, 100) + '%' }"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { MODEL_PRICING, calculateCost, formatCost, formatTokens, type ModelPricing } from '@/utils/modelPricing'

const { t } = useI18n()

const props = withDefaults(defineProps<{
  model: string
  promptTokens: number
  completionTokens: number
  budget?: number
}>(), {
  budget: 0,
})

const modelInfo = computed<ModelPricing | undefined>(() => MODEL_PRICING[props.model])

const totalCost = computed(() =>
  calculateCost(props.model, props.promptTokens, props.completionTokens)
)

const exceedsBudget = computed(() =>
  props.budget > 0 && totalCost.value > props.budget
)

const budgetUsage = computed(() => {
  if (!props.budget) return 0
  return (totalCost.value / props.budget) * 100
})
</script>
