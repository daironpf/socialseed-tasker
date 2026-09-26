<template>
  <ModuleCard :title="t('boardModules.activityMap')">
    <template #action>
      <span class="text-xs font-medium text-gray-400 dark:text-gray-500">
        {{ t('boardModules.activityTotal', { count: totalEvents }) }}
      </span>
    </template>

    <div class="flex gap-2">
      <div class="flex flex-col gap-1 pt-4 text-[9px] leading-none text-gray-400 dark:text-gray-500">
        <span
          v-for="(label, idx) in weekdayLabels"
          :key="idx"
          class="flex h-3.5 w-4 items-center"
        >
          {{ label }}
        </span>
      </div>
      <div class="min-w-0">
        <div class="flex gap-1 pb-1.5 text-[9px] leading-none text-gray-400 dark:text-gray-500">
          <span
            v-for="(m, i) in monthLabels"
            :key="i"
            class="w-3.5 whitespace-nowrap text-left"
          >
            {{ m }}
          </span>
        </div>
        <div class="flex gap-1">
          <div v-for="(week, wi) in weeks" :key="wi" class="flex flex-col gap-1">
            <div
              v-for="(day, di) in week"
              :key="di"
              class="h-3.5 w-3.5 rounded-[3px]"
              :class="LEVEL_CLASS[levelFor(countOf(day))]"
              :title="tooltipFor(day)"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="mt-3 flex items-center justify-end gap-1.5 text-[10px] text-gray-400 dark:text-gray-500">
      <span>{{ t('boardModules.heatmapLess') }}</span>
      <span
        v-for="lvl in 5"
        :key="lvl"
        class="h-2.5 w-2.5 rounded-[3px]"
        :class="LEVEL_CLASS[lvl - 1]"
      />
      <span>{{ t('boardModules.heatmapMore') }}</span>
    </div>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Issue } from '@/types'
import ModuleCard from './ModuleCard.vue'
import { useIssuesStore } from '@/stores/issuesStore'

const { t, locale } = useI18n()

const props = defineProps<{ issues?: Issue[] }>()

const issuesStore = useIssuesStore()

const WEEKS = 13

const LEVEL_CLASS = [
  'bg-gray-100 dark:bg-gray-700',
  'bg-brand-200 dark:bg-brand-800',
  'bg-brand-300 dark:bg-brand-700',
  'bg-brand-500 dark:bg-brand-600',
  'bg-brand-700 dark:bg-brand-500',
]

const weekdayLabels = ['Mon', '', 'Wed', '', 'Fri', '', '']

const allIssues = computed(() => props.issues ?? issuesStore.issues)

function dayKey(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

const counts = computed(() => {
  const map = new Map<string, number>()
  for (const issue of allIssues.value) {
    if (issue.created_at) {
      const k = dayKey(new Date(issue.created_at))
      map.set(k, (map.get(k) ?? 0) + 1)
    }
    if (issue.closed_at) {
      const k = dayKey(new Date(issue.closed_at))
      map.set(k, (map.get(k) ?? 0) + 1)
    }
  }
  return map
})

const weeks = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const dow = (today.getDay() + 6) % 7
  const thisMonday = new Date(today)
  thisMonday.setDate(today.getDate() - dow)
  const start = new Date(thisMonday)
  start.setDate(thisMonday.getDate() - (WEEKS - 1) * 7)
  const result: Date[][] = []
  for (let w = 0; w < WEEKS; w++) {
    const col: Date[] = []
    for (let d = 0; d < 7; d++) {
      const day = new Date(start)
      day.setDate(start.getDate() + w * 7 + d)
      col.push(day)
    }
    result.push(col)
  }
  return result
})

const monthLabels = computed(() => {
  let prev = -1
  return weeks.value.map((col) => {
    const m = col[0].getMonth()
    const label = m !== prev ? col[0].toLocaleDateString(locale.value, { month: 'short' }) : ''
    prev = m
    return label
  })
})

const totalEvents = computed(() => {
  let n = 0
  for (const v of counts.value.values()) n += v
  return n
})

function countOf(d: Date): number {
  return counts.value.get(dayKey(d)) ?? 0
}

function levelFor(n: number): number {
  if (n === 0) return 0
  if (n <= 2) return 1
  if (n <= 4) return 2
  if (n <= 7) return 3
  return 4
}

function tooltipFor(d: Date): string {
  const date = d.toLocaleDateString(locale.value, { month: 'short', day: 'numeric', year: 'numeric' })
  return t('boardModules.heatmapTooltip', { count: countOf(d), date })
}
</script>
