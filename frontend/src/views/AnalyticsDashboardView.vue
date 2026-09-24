<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('analytics.title') }}</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('analytics.subtitle') }}</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <div class="flex rounded-lg border border-gray-200 bg-white p-0.5 dark:border-gray-700 dark:bg-gray-800">
          <button
            v-for="preset in presets"
            :key="preset.days"
            class="rounded-md px-2.5 py-1.5 text-xs font-medium"
            :class="store.rangeDays === preset.days
              ? 'bg-blue-600 text-white'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
            @click="store.setPreset(preset.days)"
          >
            {{ preset.label }}
          </button>
        </div>
        <input
          type="date"
          :value="store.dateRange.from"
          class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700 focus:border-blue-400 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
          @change="onFromChange(($event.target as HTMLInputElement).value)"
        >
        <span class="text-xs text-gray-400">→</span>
        <input
          type="date"
          :value="store.dateRange.to"
          class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700 focus:border-blue-400 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
          @change="onToChange(($event.target as HTMLInputElement).value)"
        >
      </div>
    </div>

    <!-- KPI tiles -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div
        v-for="kpi in store.kpis.kpiList.slice(0, 4)"
        :key="kpi.label"
        class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800"
      >
        <div class="text-2xl font-bold" :class="toneText(kpi.tone)">{{ kpi.value }}</div>
        <div class="mt-1 text-xs font-semibold uppercase text-gray-400">{{ t(`analytics.kpi_${kpi.label}`) }}</div>
        <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ kpi.sub }}</div>
      </div>
    </div>

    <!-- Period comparison -->
    <div class="flex flex-wrap items-center gap-3 rounded-xl border border-gray-200 bg-white px-5 py-3 text-xs dark:border-gray-700 dark:bg-gray-800">
      <span class="font-semibold uppercase text-gray-400">{{ t('analytics.vsPrevious') }}</span>
      <span class="text-gray-600 dark:text-gray-300">
        {{ t('analytics.resolved') }}:
        <strong>{{ store.comparison.resolved.current }}</strong>
        ({{ deltaLabel(store.comparison.resolved.deltaPct) }})
      </span>
      <span class="text-gray-600 dark:text-gray-300">
        {{ t('analytics.mttrShort') }}:
        <strong>{{ store.comparison.mttr.current }}h</strong>
        vs {{ store.comparison.mttr.previous }}h
        ({{ deltaLabel(store.comparison.mttr.deltaPct) }})
      </span>
      <span class="text-gray-500 dark:text-gray-400">{{ t('analytics.period') }}: {{ store.dateRange.from }} → {{ store.dateRange.to }}</span>
    </div>

    <!-- Charts row -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <MTTRComparisonChart :points="store.mttrSeries" />
      <HealingSuccessChart :points="store.healingSeries" :overall="store.healingRate" />
    </div>

    <!-- Budget + SLA row -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <BudgetByProjectChart :items="store.budgetByProject" :range-days="store.rangeDays" />
      <SLAMetricsCard :items="store.slaItems" :counts="store.slaCounts" @notify-risks="notifyRisks" />
    </div>

    <!-- Report generator -->
    <ReportExporter />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAnalyticsReportStore } from '@/stores/analyticsReportStore'
import { useIssuesStore } from '@/stores/issuesStore'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { useToast } from '@/composables/useToast'
import MTTRComparisonChart from '@/components/analytics/MTTRComparisonChart.vue'
import HealingSuccessChart from '@/components/analytics/HealingSuccessChart.vue'
import BudgetByProjectChart from '@/components/analytics/BudgetByProjectChart.vue'
import SLAMetricsCard from '@/components/analytics/SLAMetricsCard.vue'
import ReportExporter from '@/components/analytics/ReportExporter.vue'

const { t } = useI18n()
const store = useAnalyticsReportStore()
const issuesStore = useIssuesStore()
const notificationsStore = useNotificationsStore()
const toast = useToast()

const presets = computed(() => [
  { days: 7, label: t('analytics.last7') },
  { days: 30, label: t('analytics.last30') },
  { days: 90, label: t('analytics.last90') },
])

function onFromChange(value: string) {
  if (value) store.setCustomRange(value, store.dateRange.to)
}

function onToChange(value: string) {
  if (value) store.setCustomRange(store.dateRange.from, value)
}

function deltaLabel(deltaPct: number): string {
  const sign = deltaPct > 0 ? '+' : ''
  return `${sign}${deltaPct}%`
}

function toneText(tone: string): string {
  if (tone === 'good') return 'text-emerald-600 dark:text-emerald-400'
  if (tone === 'warn') return 'text-amber-600 dark:text-amber-400'
  if (tone === 'bad') return 'text-red-600 dark:text-red-400'
  return 'text-gray-900 dark:text-white'
}

function addRiskNotification(breached: number, atRisk: number) {
  notificationsStore.addNotification({
    title: t('sla.notificationTitle'),
    message: t('sla.notificationMessage', { breached, atRisk }),
    category: 'sla',
    requiresAction: true,
    linkTo: { name: 'Analytics' },
  })
}

function notifyRisks() {
  const { breached, atRisk } = store.slaCounts
  addRiskNotification(breached, atRisk)
  toast.success(t('sla.notifySent'))
}

onMounted(async () => {
  if (!issuesStore.issues.length) {
    await issuesStore.fetchIssues(1, 200).catch(() => undefined)
  }
  if ((store.slaCounts.breached > 0 || store.slaCounts.atRisk > 0) && !store.slaNotified) {
    store.slaNotified = true
    addRiskNotification(store.slaCounts.breached, store.slaCounts.atRisk)
  }
})
</script>
