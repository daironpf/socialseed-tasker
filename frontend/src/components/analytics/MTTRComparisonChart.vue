<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('analytics.mttrTitle') }}</h3>
        <p class="text-xs text-gray-400">{{ t('analytics.mttrSubtitle') }}</p>
      </div>
      <div class="flex gap-4 text-xs">
        <div class="flex items-center gap-1.5">
          <span class="h-3 w-3 rounded-sm bg-gray-400" />
          <span class="text-gray-500 dark:text-gray-400">{{ t('analytics.beforeAgents') }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="h-3 w-3 rounded-sm bg-blue-500" />
          <span class="text-gray-500 dark:text-gray-400">{{ t('analytics.withAgents') }}</span>
        </div>
      </div>
    </div>

    <div v-if="points.length" class="relative h-64">
      <svg class="h-full w-full" viewBox="0 0 800 250" preserveAspectRatio="none">
        <g class="text-gray-200 dark:text-gray-700" stroke="currentColor" stroke-width="1">
          <line v-for="i in 5" :key="i" :x1="0" :y1="i * 50" :x2="800" :y2="i * 50" stroke-dasharray="4,4" />
        </g>

        <g class="text-xs fill-gray-400 dark:fill-gray-500">
          <text v-for="(label, i) in yLabels" :key="i" x="5" :y="250 - i * 50 + 4">{{ label }}h</text>
        </g>

        <g v-for="(point, i) in points" :key="point.period">
          <rect
            :x="groupX(i)"
            :y="scaleY(point.before)"
            :width="barWidth"
            :height="210 - scaleY(point.before)"
            fill="#9CA3AF"
            rx="3"
            class="opacity-80 hover:opacity-100 transition-opacity"
          >
            <title>{{ point.period }} · {{ t('analytics.beforeAgents') }}: {{ point.before }}h</title>
          </rect>
          <rect
            v-if="point.after !== null"
            :x="groupX(i) + barWidth + 4"
            :y="scaleY(point.after)"
            :width="barWidth"
            :height="210 - scaleY(point.after)"
            fill="#3B82F6"
            rx="3"
            class="opacity-90 hover:opacity-100 transition-opacity"
          >
            <title>{{ point.period }} · {{ t('analytics.withAgents') }}: {{ point.after }}h</title>
          </rect>
          <text
            :x="groupX(i) + barWidth + 2"
            y="240"
            text-anchor="middle"
            class="text-xs fill-gray-400 dark:fill-gray-500"
          >
            {{ point.period }}
          </text>
        </g>
      </svg>
    </div>
    <div v-else class="flex h-64 items-center justify-center text-sm text-gray-400">{{ t('common.noData') }}</div>

    <div class="mt-3 flex flex-wrap gap-4 border-t border-gray-100 pt-3 text-xs dark:border-gray-700/60">
      <span class="text-gray-500 dark:text-gray-400">
        {{ t('analytics.avgImprovement') }}:
        <strong class="text-emerald-600 dark:text-emerald-400">-{{ improvement }}%</strong>
      </span>
      <span class="text-gray-500 dark:text-gray-400">
        {{ t('analytics.beforeAgents') }}: <strong class="text-gray-700 dark:text-gray-300">{{ avgBefore }}h</strong>
      </span>
      <span class="text-gray-500 dark:text-gray-400">
        {{ t('analytics.withAgents') }}: <strong class="text-blue-600 dark:text-blue-400">{{ avgAfter }}h</strong>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MTTRPoint } from '@/types/analytics'

const props = defineProps<{
  points: MTTRPoint[]
}>()

const { t } = useI18n()

const maxValue = computed(() => Math.max(...props.points.flatMap(p => [p.before, p.after ?? 0]), 10))

const yLabels = computed(() => {
  const step = Math.ceil(maxValue.value / 4)
  return [0, step, step * 2, step * 3, step * 4]
})

const barWidth = computed(() => Math.min(38, 700 / Math.max(1, props.points.length) - 6))

function groupX(index: number): number {
  const n = props.points.length || 1
  const groupWidth = 760 / n
  return 30 + index * groupWidth + (groupWidth - barWidth.value * 2 - 4) / 2
}

function scaleY(value: number): number {
  return 210 - (value / maxValue.value) * 190
}

const avgBefore = computed(() => {
  if (!props.points.length) return 0
  return Math.round((props.points.reduce((s, p) => s + p.before, 0) / props.points.length) * 10) / 10
})

const avgAfter = computed(() => {
  const values = props.points.filter(p => p.after !== null) as MTTRPoint[]
  if (!values.length) return 0
  return Math.round((values.reduce((s, p) => s + (p.after ?? 0), 0) / values.length) * 10) / 10
})

const improvement = computed(() => {
  if (!avgBefore.value) return 0
  return Math.round(((avgBefore.value - avgAfter.value) / avgBefore.value) * 100)
})
</script>
