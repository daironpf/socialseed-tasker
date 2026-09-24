<template>
  <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 px-5 py-4 dark:border-gray-700">
      <div>
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('analytics.reportTitle') }}</h3>
        <p class="text-xs text-gray-400">{{ t('analytics.reportSubtitle') }}</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          class="rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700"
          @click="store.generateReport('weekly')"
        >
          {{ t('analytics.weeklyReport') }}
        </button>
        <button
          class="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-medium text-white hover:bg-indigo-700"
          @click="store.generateReport('monthly')"
        >
          {{ t('analytics.monthlyReport') }}
        </button>
        <template v-if="store.report">
          <button
            class="rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            :disabled="exportingPdf"
            @click="exportPDF"
          >
            {{ exportingPdf ? t('common.loading') : 'PDF' }}
          </button>
          <button
            class="rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            :disabled="exportingPng"
            @click="exportPng"
          >
            {{ exportingPng ? t('common.loading') : 'PNG' }}
          </button>
          <button
            class="rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="exportJson"
          >
            JSON
          </button>
        </template>
      </div>
    </div>

    <!-- Preview -->
    <div v-if="store.report" id="analytics-report" class="p-5">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <div class="text-base font-bold text-gray-900 dark:text-white">
            {{ store.report.type === 'weekly' ? t('analytics.weeklyReport') : t('analytics.monthlyReport') }}
          </div>
          <div class="text-xs text-gray-400">
            {{ store.report.periodStart }} → {{ store.report.periodEnd }}
            · {{ t('analytics.generatedAt') }} {{ formatDateTime(store.report.generatedAt) }}
          </div>
        </div>
        <button
          class="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          @click="store.clearReport()"
        >
          {{ t('common.close') }}
        </button>
      </div>

      <!-- KPIs -->
      <div class="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <div
          v-for="kpi in store.report.kpis"
          :key="kpi.label"
          class="rounded-lg border p-3"
          :class="toneBorder(kpi.tone)"
        >
          <div class="text-lg font-bold" :class="toneText(kpi.tone)">{{ kpi.value }}</div>
          <div class="text-[10px] font-semibold uppercase text-gray-400">{{ t(`analytics.kpi_${kpi.label}`) }}</div>
          <div class="mt-0.5 text-[10px] text-gray-500 dark:text-gray-400">{{ kpi.sub }}</div>
        </div>
      </div>

      <!-- Exceptions table -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="border-b border-gray-200 text-[10px] uppercase text-gray-400 dark:border-gray-700">
              <th class="px-2 py-2">{{ t('analytics.exceptionKind') }}</th>
              <th class="px-2 py-2">{{ t('analytics.exceptionItem') }}</th>
              <th class="px-2 py-2">{{ t('analytics.exceptionDetail') }}</th>
              <th class="px-2 py-2">{{ t('analytics.exceptionSeverity') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="ex in store.report.exceptions"
              :key="ex.id"
              class="border-b border-gray-100 dark:border-gray-700/60"
            >
              <td class="px-2 py-2">
                <span class="rounded bg-gray-100 px-1.5 py-0.5 font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                  {{ t(`analytics.kind_${ex.kind}`) }}
                </span>
              </td>
              <td class="max-w-[220px] truncate px-2 py-2 font-medium text-gray-700 dark:text-gray-300">{{ ex.title }}</td>
              <td class="px-2 py-2 text-gray-500 dark:text-gray-400">{{ ex.detail }}</td>
              <td class="px-2 py-2">
                <span
                  class="rounded px-1.5 py-0.5 text-[10px] font-bold"
                  :class="ex.severity === 'HIGH'
                    ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                    : ex.severity === 'MEDIUM'
                      ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'"
                >
                  {{ ex.severity }}
                </span>
              </td>
            </tr>
            <tr v-if="!store.report.exceptions.length">
              <td colspan="4" class="px-2 py-6 text-center text-gray-400">{{ t('analytics.noExceptions') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else class="px-5 py-10 text-center text-sm text-gray-400">
      {{ t('analytics.noReport') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAnalyticsReportStore } from '@/stores/analyticsReportStore'
import { useExport } from '@/composables/useExport'

const { t, d } = useI18n()
const store = useAnalyticsReportStore()
const { exportJSON } = useExport()

const exportingPdf = ref(false)
const exportingPng = ref(false)

function formatDateTime(iso: string): string {
  try {
    return d(new Date(iso), 'short')
  } catch {
    return iso.slice(0, 16).replace('T', ' ')
  }
}

function toneBorder(tone: string): string {
  if (tone === 'good') return 'border-emerald-200 bg-emerald-50/50 dark:border-emerald-800 dark:bg-emerald-900/10'
  if (tone === 'warn') return 'border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-900/10'
  if (tone === 'bad') return 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-900/10'
  return 'border-gray-200 bg-gray-50/50 dark:border-gray-700 dark:bg-gray-900/30'
}

function toneText(tone: string): string {
  if (tone === 'good') return 'text-emerald-600 dark:text-emerald-400'
  if (tone === 'warn') return 'text-amber-600 dark:text-amber-400'
  if (tone === 'bad') return 'text-red-600 dark:text-red-400'
  return 'text-gray-700 dark:text-gray-300'
}

function exportPng() {
  const el = document.getElementById('analytics-report')
  if (!el) return
  exportingPng.value = true
  import('html2canvas')
    .then(({ default: html2canvas }) => html2canvas(el, { backgroundColor: '#ffffff', scale: 2 }))
    .then(canvas => {
      const link = document.createElement('a')
      link.download = `analytics-report-${store.report?.type ?? 'report'}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    })
    .finally(() => {
      exportingPng.value = false
    })
}

function exportPDF() {
  const el = document.getElementById('analytics-report')
  if (!el) return
  exportingPdf.value = true
  Promise.all([import('html2canvas'), import('jspdf')])
    .then(([html2canvasMod, jsPDFMod]) => {
      const { default: html2canvas } = html2canvasMod
      const { default: jsPDF } = jsPDFMod
      return html2canvas(el, { backgroundColor: '#ffffff', scale: 2 }).then(canvas => {
        const imgData = canvas.toDataURL('image/png')
        const pdf = new jsPDF('p', 'mm', 'a4')
        const pdfWidth = pdf.internal.pageSize.getWidth()
        const pdfHeight = (canvas.height * pdfWidth) / canvas.width
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
        pdf.save(`analytics-report-${store.report?.type ?? 'report'}.pdf`)
      })
    })
    .finally(() => {
      exportingPdf.value = false
    })
}

function exportJson() {
  if (!store.report) return
  exportJSON(store.report, `analytics-report-${store.report.type}`)
}
</script>
