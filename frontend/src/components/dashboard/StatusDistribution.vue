<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('statusDistribution.title') }}</h3>
    </div>

    <div class="space-y-3">
      <div v-for="item in statusData" :key="item.status" class="flex items-center gap-3">
        <div class="flex items-center gap-2 w-32">
          <span class="h-3 w-3 rounded-full" :class="item.color"></span>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ item.label }}</span>
        </div>
        <div class="flex-1">
          <div class="h-6 rounded-lg bg-gray-100 dark:bg-gray-700 overflow-hidden">
            <div
              class="h-full rounded-lg transition-all duration-500"
              :class="item.color"
              :style="{ width: item.percentage + '%' }"
            ></div>
          </div>
        </div>
        <div class="flex items-center gap-2 w-24 justify-end">
          <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ item.count }}</span>
          <span class="text-xs text-gray-500 dark:text-gray-400">({{ item.percentage.toFixed(0) }}%)</span>
        </div>
      </div>
    </div>

    <!-- Summary -->
    <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between text-sm">
        <span class="text-gray-500 dark:text-gray-400">{{ t('statusDistribution.totalIssues') }}</span>
        <span class="font-semibold text-gray-900 dark:text-white">{{ total }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'

const { t } = useI18n()

interface Props {
  issues: Issue[]
}

const props = defineProps<Props>()

const statusConfig = computed(() => ({
  OPEN: { label: t('statusDistribution.open'), color: 'bg-blue-500' },
  IN_PROGRESS: { label: t('statusDistribution.inProgress'), color: 'bg-orange-500' },
  BLOCKED: { label: t('statusDistribution.blocked'), color: 'bg-red-500' },
  CLOSED: { label: t('statusDistribution.closed'), color: 'bg-green-500' },
  REVIEW: { label: t('statusDistribution.review'), color: 'bg-purple-500' },
}))

const total = computed(() => props.issues.length)

const statusData = computed(() => {
  const counts: Record<string, number> = {}
  props.issues.forEach(issue => {
    counts[issue.status] = (counts[issue.status] || 0) + 1
  })

  return Object.entries(statusConfig.value)
    .map(([status, config]) => ({
      status,
      label: config.label,
      color: config.color,
      count: counts[status] || 0,
      percentage: total.value > 0 ? ((counts[status] || 0) / total.value) * 100 : 0,
    }))
    .filter(item => item.count > 0)
    .sort((a, b) => b.count - a.count)
})
</script>
