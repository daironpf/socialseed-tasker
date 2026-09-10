<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Actividad Diaria</h3>
      <div class="flex items-center gap-3">
        <!-- Month selector -->
        <select
          v-model="selectedMonth"
          class="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
        >
          <option v-for="m in availableMonths" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
        <!-- Legend -->
        <div class="flex gap-4 text-sm">
          <div class="flex items-center gap-2">
            <span class="h-3 w-3 rounded-full bg-blue-500"></span>
            <span class="text-gray-500 dark:text-gray-400">Creadas</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="h-3 w-3 rounded-full bg-green-500"></span>
            <span class="text-gray-500 dark:text-gray-400">Solucionadas</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats summary -->
    <div class="mb-4 flex gap-6 text-sm">
      <div class="text-gray-600 dark:text-gray-400">
        <span class="font-medium text-blue-600 dark:text-blue-400">{{ totalCreated }}</span> creadas
      </div>
      <div class="text-gray-600 dark:text-gray-400">
        <span class="font-medium text-green-600 dark:text-green-400">{{ totalClosed }}</span> solucionadas
      </div>
      <div class="text-gray-600 dark:text-gray-400">
        Balance: <span :class="balance >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">{{ balance >= 0 ? '+' : '' }}{{ balance }}</span>
      </div>
    </div>

    <div class="relative h-64">
      <svg
        class="h-full w-full"
        viewBox="0 0 900 250"
        preserveAspectRatio="none"
      >
        <!-- Grid lines -->
        <g class="text-gray-200 dark:text-gray-700" stroke="currentColor" stroke-width="1">
          <line v-for="i in 5" :key="i" :x1="40" :y1="i * 45" :x2="880" :y2="i * 45" stroke-dasharray="4,4" />
        </g>

        <!-- Y-axis labels -->
        <g class="text-xs fill-gray-400 dark:fill-gray-500">
          <text v-for="(label, i) in yLabels" :key="'y-' + i" x="5" :y="225 - i * 45 + 4">{{ label }}</text>
        </g>

        <!-- X-axis labels (days) -->
        <g class="text-xs fill-gray-400 dark:fill-gray-500">
          <text
            v-for="(point, i) in createdPoints"
            :key="'xlabel-' + i"
            :x="point.x"
            y="245"
            text-anchor="middle"
            font-size="10"
          >
            {{ chartData[i]?.day }}
          </text>
        </g>

        <!-- Created bars (blue) -->
        <g>
          <rect
            v-for="(point, i) in createdPoints"
            :key="'bar-created-' + i"
            :x="point.x - 4"
            :y="point.y"
            width="8"
            :height="225 - point.y"
            fill="#3B82F6"
            rx="2"
            opacity="0.8"
            class="cursor-pointer"
          >
            <title>Creadas {{ chartData[i]?.day }}: {{ chartData[i]?.created }}</title>
          </rect>
        </g>

        <!-- Closed bars (green) -->
        <g>
          <rect
            v-for="(point, i) in closedPoints"
            :key="'bar-closed-' + i"
            :x="point.x + 5"
            :y="point.y"
            width="8"
            :height="225 - point.y"
            fill="#22C55E"
            rx="2"
            opacity="0.8"
            class="cursor-pointer"
          >
            <title>Solucionadas {{ chartData[i]?.day }}: {{ chartData[i]?.closed }}</title>
          </rect>
        </g>

        <!-- Day number labels on top of bars -->
        <g class="text-xs fill-gray-600 dark:fill-gray-400">
          <text
            v-for="(point, i) in createdPoints"
            :key="'lbl-created-' + i"
            :x="point.x - 1"
            :y="point.y - 4"
            text-anchor="middle"
            font-size="8"
          >
            {{ chartData[i]?.created || '' }}
          </text>
          <text
            v-for="(point, i) in closedPoints"
            :key="'lbl-closed-' + i"
            :x="point.x + 9"
            :y="point.y - 4"
            text-anchor="middle"
            font-size="8"
          >
            {{ chartData[i]?.closed || '' }}
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Issue } from '@/types'

interface Props {
  issues: Issue[]
}

const props = defineProps<Props>()

// Available months from data
const availableMonths = computed(() => {
  const months = new Set<string>()
  props.issues.forEach(issue => {
    const d = new Date(issue.created_at)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    months.add(key)
  })
  
  return [...months].sort().reverse().map(m => {
    const [year, month] = m.split('-')
    const date = new Date(parseInt(year), parseInt(month) - 1)
    return {
      value: m,
      label: date.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' }),
    }
  })
})

const selectedMonth = ref(availableMonths.value[0]?.value || '')

const chartData = computed(() => {
  if (!selectedMonth.value) return []
  
  const [year, month] = selectedMonth.value.split('-').map(Number)
  const daysInMonth = new Date(year, month, 0).getDate()
  
  const data = []
  
  for (let day = 1; day <= daysInMonth; day++) {
    const dayStart = new Date(year, month - 1, day)
    const dayEnd = new Date(year, month - 1, day + 1)
    
    const created = props.issues.filter(issue => {
      const created = new Date(issue.created_at)
      return created >= dayStart && created < dayEnd
    }).length
    
    const closed = props.issues.filter(issue => {
      if (issue.status !== 'CLOSED' || !issue.closed_at) return false
      const closed = new Date(issue.closed_at)
      return closed >= dayStart && closed < dayEnd
    }).length
    
    data.push({
      day: String(day),
      created,
      closed,
    })
  }
  
  return data
})

const totalCreated = computed(() => chartData.value.reduce((sum, d) => sum + d.created, 0))
const totalClosed = computed(() => chartData.value.reduce((sum, d) => sum + d.closed, 0))
const balance = computed(() => totalCreated.value - totalClosed.value)

const maxValue = computed(() => {
  const allValues = chartData.value.flatMap(d => [d.created, d.closed])
  return Math.max(...allValues, 1)
})

const yLabels = computed(() => {
  const max = maxValue.value
  const step = Math.ceil(max / 4)
  return [0, step, step * 2, step * 3, max]
})

function scaleY(value: number): number {
  return 225 - (value / maxValue.value) * 200
}

const createdPoints = computed(() => {
  const chartWidth = 840
  const barGroupWidth = chartData.value.length > 0 ? chartWidth / chartData.value.length : 0
  
  return chartData.value.map((d, i) => ({
    x: 40 + i * barGroupWidth + barGroupWidth / 2 - 5,
    y: scaleY(d.created),
  }))
})

const closedPoints = computed(() => {
  const chartWidth = 840
  const barGroupWidth = chartData.value.length > 0 ? chartWidth / chartData.value.length : 0
  
  return chartData.value.map((d, i) => ({
    x: 40 + i * barGroupWidth + barGroupWidth / 2 + 5,
    y: scaleY(d.closed),
  }))
})
</script>
