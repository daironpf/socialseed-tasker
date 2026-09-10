<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Tiempo Promedio de Resolución</h3>
    
    <div class="flex items-center justify-center">
      <div class="relative">
        <!-- Circular progress -->
        <svg class="h-40 w-40" viewBox="0 0 120 120">
          <!-- Background circle -->
          <circle
            cx="60"
            cy="60"
            r="50"
            fill="none"
            stroke="currentColor"
            stroke-width="10"
            class="text-gray-100 dark:text-gray-700"
          />
          <!-- Progress circle -->
          <circle
            cx="60"
            cy="60"
            r="50"
            fill="none"
            :stroke="progressColor"
            stroke-width="10"
            stroke-linecap="round"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="progressOffset"
            transform="rotate(-90 60 60)"
            class="transition-all duration-1000"
          />
        </svg>
        
        <!-- Center text -->
        <div class="absolute inset-0 flex flex-col items-center justify-center">
          <span class="text-3xl font-bold text-gray-900 dark:text-white">{{ avgDays }}</span>
          <span class="text-sm text-gray-500 dark:text-gray-400">días</span>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="mt-6 grid grid-cols-2 gap-4">
      <div class="rounded-lg bg-gray-50 p-3 text-center dark:bg-gray-700/50">
        <p class="text-2xl font-bold text-green-600 dark:text-green-400">{{ fastest }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Más rápido</p>
      </div>
      <div class="rounded-lg bg-gray-50 p-3 text-center dark:bg-gray-700/50">
        <p class="text-2xl font-bold text-orange-500 dark:text-orange-400">{{ slowest }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Más lento</p>
      </div>
    </div>

    <!-- Info -->
    <div class="mt-4 rounded-lg bg-blue-50 p-3 dark:bg-blue-900/20">
      <div class="flex items-start gap-2">
        <svg class="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-xs text-blue-700 dark:text-blue-300">
          Basado en {{ resolvedCount }} issues resueltas de un total de {{ totalIssues }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Issue } from '@/types'

interface Props {
  issues: Issue[]
}

const props = defineProps<Props>()

const circumference = 2 * Math.PI * 50

const resolvedIssues = computed(() => {
  return props.issues.filter(i => i.status === 'CLOSED' && i.closed_at)
})

const resolvedCount = computed(() => resolvedIssues.value.length)
const totalIssues = computed(() => props.issues.length)

const resolutionTimes = computed(() => {
  return resolvedIssues.value.map(issue => {
    const created = new Date(issue.created_at)
    const closed = new Date(issue.closed_at!)
    return (closed.getTime() - created.getTime()) / (1000 * 60 * 60 * 24) // days
  })
})

const avgDays = computed(() => {
  if (resolutionTimes.value.length === 0) return 0
  const sum = resolutionTimes.value.reduce((a, b) => a + b, 0)
  return Math.round(sum / resolutionTimes.value.length * 10) / 10
})

const fastest = computed(() => {
  if (resolutionTimes.value.length === 0) return '0d'
  const min = Math.min(...resolutionTimes.value)
  return formatTime(min)
})

const slowest = computed(() => {
  if (resolutionTimes.value.length === 0) return '0d'
  const max = Math.max(...resolutionTimes.value)
  return formatTime(max)
})

function formatTime(days: number): string {
  if (days < 1) return `${Math.round(days * 24)}h`
  if (days < 7) return `${Math.round(days)}d`
  return `${Math.round(days / 7)}w`
}

const progressColor = computed(() => {
  if (avgDays.value <= 3) return '#22C55E' // green
  if (avgDays.value <= 7) return '#3B82F6' // blue
  if (avgDays.value <= 14) return '#F97316' // orange
  return '#EF4444' // red
})

const progressOffset = computed(() => {
  // Max 30 days scale
  const maxDays = 30
  const progress = Math.min(avgDays.value / maxDays, 1)
  return circumference - (progress * circumference)
})
</script>
