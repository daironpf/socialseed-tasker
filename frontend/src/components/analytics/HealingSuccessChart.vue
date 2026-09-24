<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('analytics.healingTitle') }}</h3>
        <p class="text-xs text-gray-400">{{ t('analytics.healingSubtitle') }}</p>
      </div>
      <span
        class="rounded-full px-2.5 py-1 text-xs font-bold"
        :class="overall >= 80
          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
          : overall >= 60
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
            : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'"
      >
        {{ overall }}%
      </span>
    </div>

    <div v-if="points.length" class="relative h-64">
      <svg class="h-full w-full" viewBox="0 0 800 250" preserveAspectRatio="none">
        <g class="text-gray-200 dark:text-gray-700" stroke="currentColor" stroke-width="1">
          <line v-for="i in 5" :key="i" :x1="0" :y1="i * 50" :x2="800" :y2="i * 50" stroke-dasharray="4,4" />
        </g>

        <g class="text-xs fill-gray-400 dark:fill-gray-500">
          <text v-for="(label, i) in yLabels" :key="i" x="5" :y="250 - i * 50 + 4">{{ label }}%</text>
        </g>

        <polyline
          :points="linePoints"
          fill="none"
          stroke="#22C55E"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <g v-for="(point, i) in points" :key="point.period">
          <circle :cx="scaleX(i)" :cy="scaleY(point.successRate)" r="4" fill="#22C55E">
            <title>{{ point.period }}: {{ point.successRate }}% ({{ point.completed }} ok / {{ point.failed }} failed)</title>
          </circle>
          <text
            :x="scaleX(i)"
            y="240"
            text-anchor="middle"
            class="text-xs fill-gray-400 dark:fill-gray-500"
          >
            {{ point.period }}
          </text>
        </g>

        <line x1="0" :y1="scaleY(target)" x2="800" :y2="scaleY(target)" stroke="#F59E0B" stroke-width="1.5" stroke-dasharray="6,4" />
        <text x="795" :y="scaleY(target) - 5" text-anchor="end" class="text-xs fill-amber-500">
          {{ t('analytics.target') }} {{ target }}%
        </text>
      </svg>
    </div>
    <div v-else class="flex h-64 items-center justify-center text-sm text-gray-400">{{ t('common.noData') }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { HealingPoint } from '@/types/analytics'

const props = defineProps<{
  points: HealingPoint[]
  overall: number
}>()

const { t } = useI18n()

const target = 85

const yLabels = [0, 25, 50, 75, 100]

function scaleY(rate: number): number {
  return 210 - (rate / 100) * 190
}

function scaleX(index: number): number {
  if (props.points.length <= 1) return 400
  return (index / (props.points.length - 1)) * 760 + 20
}

const linePoints = computed(() =>
  props.points.map((p, i) => `${scaleX(i)},${scaleY(p.successRate)}`).join(' ')
)
</script>
