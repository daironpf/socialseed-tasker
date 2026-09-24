<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('sla.title') }}</h3>
        <p class="text-xs text-gray-400">{{ t('sla.subtitle') }}</p>
      </div>
      <button
        v-if="counts.breached > 0 || counts.atRisk > 0"
        class="rounded-lg border border-amber-300 bg-amber-50 px-2.5 py-1.5 text-[11px] font-semibold text-amber-700 hover:bg-amber-100 dark:border-amber-700 dark:bg-amber-900/30 dark:text-amber-300 dark:hover:bg-amber-900/50"
        @click="$emit('notify-risks')"
      >
        {{ t('sla.notifyTeam') }}
      </button>
    </div>

    <!-- Counters -->
    <div class="mb-4 grid grid-cols-3 gap-3">
      <div class="rounded-lg bg-emerald-50 p-3 text-center dark:bg-emerald-900/20">
        <div class="text-xl font-bold text-emerald-600 dark:text-emerald-400">{{ counts.onTrack }}</div>
        <div class="text-[10px] font-semibold uppercase text-emerald-700/70 dark:text-emerald-400/70">{{ t('sla.onTrack') }}</div>
      </div>
      <div class="rounded-lg bg-amber-50 p-3 text-center dark:bg-amber-900/20">
        <div class="text-xl font-bold text-amber-600 dark:text-amber-400">{{ counts.atRisk }}</div>
        <div class="text-[10px] font-semibold uppercase text-amber-700/70 dark:text-amber-400/70">{{ t('sla.atRisk') }}</div>
      </div>
      <div class="rounded-lg bg-red-50 p-3 text-center dark:bg-red-900/20">
        <div class="text-xl font-bold text-red-600 dark:text-red-400">{{ counts.breached }}</div>
        <div class="text-[10px] font-semibold uppercase text-red-700/70 dark:text-red-400/70">{{ t('sla.breached') }}</div>
      </div>
    </div>

    <!-- Breach-risk banner -->
    <div
      v-if="counts.breached > 0 || counts.atRisk > 0"
      class="mb-4 flex items-start gap-2 rounded-lg border px-3 py-2 text-xs"
      :class="counts.breached > 0
        ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300'
        : 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300'"
    >
      <span class="font-bold">{{ counts.breached > 0 ? '!' : '~' }}</span>
      <span>
        {{ counts.breached > 0
          ? t('sla.breachBanner', { n: counts.breached })
          : t('sla.riskBanner', { n: counts.atRisk }) }}
      </span>
    </div>

    <!-- SLA definitions -->
    <div class="mb-4 flex flex-wrap gap-1.5 text-[10px]">
      <span v-for="(hours, priority) in SLA_HOURS" :key="priority" class="rounded bg-gray-100 px-1.5 py-0.5 font-medium text-gray-500 dark:bg-gray-700 dark:text-gray-300">
        {{ priority }}: {{ hours }}h
      </span>
    </div>

    <!-- Items -->
    <div v-if="items.length" class="space-y-2.5">
      <div
        v-for="item in items.slice(0, 6)"
        :key="item.issueId"
        class="rounded-lg border border-gray-100 p-2.5 dark:border-gray-700/60"
      >
        <div class="flex items-center gap-2">
          <span
            class="rounded px-1.5 py-0.5 text-[9px] font-bold"
            :class="priorityClass(item.priority)"
          >
            {{ item.priority }}
          </span>
          <span class="min-w-0 flex-1 truncate text-xs font-medium text-gray-700 dark:text-gray-300" :title="item.title">
            {{ item.title }}
          </span>
          <span
            class="shrink-0 text-[10px] font-semibold"
            :class="statusClass(item.status)"
          >
            {{ statusLabel(item) }}
          </span>
        </div>
        <div class="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
          <div
            class="h-full rounded-full"
            :class="item.status === 'breached' ? 'bg-red-500' : item.status === 'at_risk' ? 'bg-amber-500' : 'bg-emerald-500'"
            :style="{ width: Math.min(100, item.percentUsed) + '%' }"
          />
        </div>
      </div>
      <div v-if="items.length > 6" class="text-center text-[11px] text-gray-400">
        {{ t('sla.moreItems', { n: items.length - 6 }) }}
      </div>
    </div>
    <div v-else class="py-8 text-center text-sm text-gray-400">{{ t('sla.noOpen') }}</div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { SLAIssueMetric, SLAStatus } from '@/types/analytics'
import { SLA_HOURS } from '@/types/analytics'

defineProps<{
  items: SLAIssueMetric[]
  counts: { onTrack: number; atRisk: number; breached: number; total: number }
}>()

defineEmits<{
  'notify-risks': []
}>()

const { t } = useI18n()

function priorityClass(priority: string): string {
  if (priority === 'CRITICAL') return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
  if (priority === 'HIGH') return 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300'
  if (priority === 'MEDIUM') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
  return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
}

function statusClass(status: SLAStatus): string {
  if (status === 'breached') return 'text-red-600 dark:text-red-400'
  if (status === 'at_risk') return 'text-amber-600 dark:text-amber-400'
  return 'text-emerald-600 dark:text-emerald-400'
}

function statusLabel(item: SLAIssueMetric): string {
  if (item.status === 'breached') return t('sla.overdueBy', { h: Math.abs(item.hoursLeft) })
  if (item.status === 'at_risk') return t('sla.hoursLeft', { h: item.hoursLeft })
  return t('sla.onTrack')
}
</script>
