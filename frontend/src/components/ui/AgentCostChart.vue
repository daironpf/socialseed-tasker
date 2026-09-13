<template>
  <div class="agent-cost-chart rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{{ t('tokens.chartTitle') }}</h3>
      <div class="flex gap-2">
        <button
          v-for="period in periods"
          :key="period.key"
          class="rounded px-2 py-1 text-[10px] font-medium transition-colors"
          :class="selectedPeriod === period.key ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'"
          @click="selectedPeriod = period.key"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <div v-if="chartData.length === 0" class="flex items-center justify-center h-40 text-sm text-gray-400">
      {{ t('tokens.noData') }}
    </div>

    <div v-else class="relative">
      <svg :width="svgWidth" :height="svgHeight" class="w-full">
        <g :transform="`translate(${padding.left}, 0)`">
          <line
            v-for="i in 5"
            :key="'grid-' + i"
            :x1="0"
            :y1="(svgHeight - padding.bottom) * (i / 5)"
            :x2="svgWidth - padding.left - padding.right"
            :y2="(svgHeight - padding.bottom) * (i / 5)"
            stroke="currentColor"
            class="text-gray-100 dark:text-gray-800"
            stroke-dasharray="4"
          />

          <text
            v-for="(tick, i) in yTicks"
            :key="'tick-' + i"
            :x="-8"
            :y="tick.y + 4"
            text-anchor="end"
            class="fill-gray-400 text-[10px]"
          >
            {{ tick.label }}
          </text>

          <g v-for="(bar, idx) in chartData" :key="idx">
            <rect
              :x="bar.x"
              :y="bar.y"
              :width="bar.width"
              :height="bar.height"
              :fill="bar.color"
              rx="2"
              class="opacity-80 hover:opacity-100 transition-opacity"
            />
            <text
              :x="bar.x + barWidth / 2"
              :y="bar.y - 4"
              text-anchor="middle"
              class="fill-gray-500 text-[9px]"
            >
              {{ bar.costLabel }}
            </text>
          </g>

          <text
            v-for="(label, idx) in xLabels"
            :key="'xlabel-' + idx"
            :x="label.x"
            :y="svgHeight - padding.bottom + 16"
            text-anchor="middle"
            class="fill-gray-400 text-[10px]"
          >
            {{ label.text }}
          </text>
        </g>
      </svg>
    </div>

    <div class="flex items-center justify-between mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
      <div class="text-xs text-gray-500">
        {{ t('tokens.totalCost') }}: <span class="font-semibold text-gray-700 dark:text-gray-300">{{ formatCost(totalCost) }}</span>
      </div>
      <div class="text-xs text-gray-500">
        {{ t('tokens.totalTokens') }}: <span class="font-semibold text-gray-700 dark:text-gray-300">{{ formatTokens(totalTokens) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { calculateCost, formatCost, formatTokens } from '@/utils/modelPricing'

const { t } = useI18n()

interface DataPoint {
  date: string
  promptTokens: number
  completionTokens: number
  model: string
}

const props = defineProps<{
  data: DataPoint[]
}>()

const selectedPeriod = ref('7d')

const periods = [
  { key: '7d', label: '7D' },
  { key: '30d', label: '30D' },
  { key: 'all', label: 'All' },
]

const svgWidth = 400
const svgHeight = 180
const padding = { top: 20, right: 10, bottom: 30, left: 50 }

const filteredData = computed(() => {
  const now = new Date()
  const data = props.data
  if (selectedPeriod.value === 'all') return data
  const days = selectedPeriod.value === '7d' ? 7 : 30
  const cutoff = new Date(now.getTime() - days * 86400000)
  return data.filter(d => new Date(d.date) >= cutoff)
})

const dailyCosts = computed(() => {
  const map = new Map<string, number>()
  for (const point of filteredData.value) {
    const cost = calculateCost(point.model, point.promptTokens, point.completionTokens)
    const date = point.date.split('T')[0]
    map.set(date, (map.get(date) || 0) + cost)
  }
  return Array.from(map.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-14)
})

const maxCost = computed(() => Math.max(...dailyCosts.value.map(d => d[1]), 0.01))

const barWidth = computed(() => Math.max(20, (svgWidth - padding.left - padding.right) / dailyCosts.value.length - 8))

const chartData = computed(() => {
  const bw = barWidth.value
  const chartHeight = svgHeight - padding.bottom

  return dailyCosts.value.map(([_date, cost], idx) => {
    const height = (cost / maxCost.value) * chartHeight * 0.85
    const x = idx * (bw + 8)
    const y = chartHeight - height

    let color = '#22c55e'
    if (cost > maxCost.value * 0.8) color = '#ef4444'
    else if (cost > maxCost.value * 0.5) color = '#f59e0b'

    return {
      x,
      y,
      width: bw,
      height,
      color,
      costLabel: formatCost(cost),
    }
  })
})

const xLabels = computed(() => {
  const bw = barWidth.value
  return dailyCosts.value.map(([date], idx) => ({
    x: idx * (bw + 8) + bw / 2,
    text: new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
  }))
})

const yTicks = computed(() => {
  const chartHeight = svgHeight - padding.bottom
  return [0, 0.25, 0.5, 0.75, 1].map(pct => ({
    y: chartHeight * (1 - pct),
    label: formatCost(maxCost.value * pct),
  }))
})

const totalCost = computed(() =>
  filteredData.value.reduce((sum, d) =>
    sum + calculateCost(d.model, d.promptTokens, d.completionTokens), 0
  )
)

const totalTokens = computed(() =>
  filteredData.value.reduce((sum, d) => sum + d.promptTokens + d.completionTokens, 0)
)
</script>
