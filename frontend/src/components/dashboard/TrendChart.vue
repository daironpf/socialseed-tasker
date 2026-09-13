<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('trendChart.title') }}</h3>
      <div class="flex gap-4 text-sm">
        <div class="flex items-center gap-2">
          <span class="h-3 w-3 rounded-full bg-blue-500"></span>
          <span class="text-gray-500 dark:text-gray-400">{{ t('trendChart.open') }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="h-3 w-3 rounded-full bg-green-500"></span>
          <span class="text-gray-500 dark:text-gray-400">{{ t('trendChart.closed') }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="h-3 w-3 rounded-full bg-orange-500"></span>
          <span class="text-gray-500 dark:text-gray-400">{{ t('trendChart.inProgress') }}</span>
        </div>
      </div>
    </div>

    <div class="relative h-64">
      <svg
        class="h-full w-full"
        viewBox="0 0 800 250"
        preserveAspectRatio="none"
      >
        <!-- Grid lines -->
        <g class="text-gray-200 dark:text-gray-700" stroke="currentColor" stroke-width="1">
          <line v-for="i in 5" :key="i" :x1="0" :y1="i * 50" :x2="800" :y2="i * 50" stroke-dasharray="4,4" />
        </g>

        <!-- Y-axis labels -->
        <g class="text-xs fill-gray-400 dark:fill-gray-500">
          <text v-for="(label, i) in yLabels" :key="i" x="5" :y="250 - i * 50 + 4">{{ label }}</text>
        </g>

        <!-- X-axis labels -->
        <g class="text-xs fill-gray-400 dark:fill-gray-500">
          <text
            v-for="(label, i) in xLabels"
            :key="i"
            :x="xLabels.length > 1 ? i * (780 / (xLabels.length - 1)) + 10 : 400"
            y="245"
            text-anchor="middle"
          >
            {{ label }}
          </text>
        </g>

        <!-- Lines -->
        <polyline
          :points="openPoints"
          fill="none"
          stroke="#3B82F6"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <polyline
          :points="closedPoints"
          fill="none"
          stroke="#22C55E"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <polyline
          :points="inProgressPoints"
          fill="none"
          stroke="#F97316"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <!-- Data points -->
        <g v-for="(point, i) in openDataPoints" :key="'open-' + i">
          <circle :cx="point.x" :cy="point.y" r="4" fill="#3B82F6" class="cursor-pointer" />
        </g>
        <g v-for="(point, i) in closedDataPoints" :key="'closed-' + i">
          <circle :cx="point.x" :cy="point.y" r="4" fill="#22C55E" class="cursor-pointer" />
        </g>
        <g v-for="(point, i) in inProgressDataPoints" :key="'progress-' + i">
          <circle :cx="point.x" :cy="point.y" r="4" fill="#F97316" class="cursor-pointer" />
        </g>
      </svg>
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

const chartData = computed(() => {
  const now = new Date()
  const weeks = 8
  const data = []

  for (let i = weeks - 1; i >= 0; i--) {
    const weekStart = new Date(now)
    weekStart.setDate(weekStart.getDate() - (i * 7))
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekEnd.getDate() + 7)

    const weekLabel = `${weekStart.getDate()}/${weekStart.getMonth() + 1}`

    const closedInWeek = props.issues.filter(issue => {
      if (issue.status !== 'CLOSED' || !issue.closed_at) return false
      const closed = new Date(issue.closed_at)
      return closed >= weekStart && closed < weekEnd
    }).length

    const openAtEnd = props.issues.filter(issue => {
      const created = new Date(issue.created_at)
      const closed = issue.closed_at ? new Date(issue.closed_at) : null
      return created < weekEnd && (!closed || closed >= weekEnd)
    }).length

    const inProgressAtEnd = props.issues.filter(issue => {
      if (issue.status !== 'IN_PROGRESS') return false
      const created = new Date(issue.created_at)
      return created < weekEnd
    }).length

    data.push({
      label: weekLabel,
      open: openAtEnd,
      closed: closedInWeek,
      inProgress: inProgressAtEnd,
    })
  }

  return data
})

const maxValue = computed(() => {
  const allValues = chartData.value.flatMap(d => [d.open, d.closed, d.inProgress])
  return Math.max(...allValues, 1)
})

const yLabels = computed(() => {
  const max = maxValue.value
  const step = Math.ceil(max / 4)
  return [0, step, step * 2, step * 3, max]
})

const xLabels = computed(() => chartData.value.map(d => d.label))

function scaleY(value: number): number {
  return 200 - (value / maxValue.value) * 180 + 10
}

function scaleX(index: number): number {
  if (chartData.value.length <= 1) return 400
  return (index / (chartData.value.length - 1)) * 780 + 10
}

const openPoints = computed(() => {
  return chartData.value
    .map((d, i) => `${scaleX(i)},${scaleY(d.open)}`)
    .join(' ')
})

const closedPoints = computed(() => {
  return chartData.value
    .map((d, i) => `${scaleX(i)},${scaleY(d.closed)}`)
    .join(' ')
})

const inProgressPoints = computed(() => {
  return chartData.value
    .map((d, i) => `${scaleX(i)},${scaleY(d.inProgress)}`)
    .join(' ')
})

const openDataPoints = computed(() => {
  return chartData.value.map((d, i) => ({ x: scaleX(i), y: scaleY(d.open) }))
})

const closedDataPoints = computed(() => {
  return chartData.value.map((d, i) => ({ x: scaleX(i), y: scaleY(d.closed) }))
})

const inProgressDataPoints = computed(() => {
  return chartData.value.map((d, i) => ({ x: scaleX(i), y: scaleY(d.inProgress) }))
})
</script>
