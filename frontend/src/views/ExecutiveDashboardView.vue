<template>
  <div class="space-y-6" id="executive-dashboard">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('executive.title') }}</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('executive.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="exportPNG" class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700">
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          PNG
        </button>
        <button @click="exportPDF" class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700">
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
          PDF
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="kpi in store.kpis" :key="kpi.label" class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
        <div class="flex items-center justify-between mb-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg" :class="kpiBg(kpi.color)">
            <svg class="h-5 w-5" :class="kpiTextColor(kpi.color)" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="kpi.icon" /></svg>
          </div>
          <span class="inline-flex items-center gap-0.5 text-xs font-medium" :class="kpi.trend === 'up' ? 'text-green-600 dark:text-green-400' : kpi.trend === 'down' ? 'text-red-600 dark:text-red-400' : 'text-gray-500'">
            <svg v-if="kpi.trend === 'up'" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
            <svg v-else-if="kpi.trend === 'down'" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
            {{ store.formatTrend(kpi.trend, kpi.trendValue) }}
          </span>
        </div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ kpi.value }}<span class="text-sm font-normal text-gray-500">{{ kpi.unit }}</span></div>
        <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ kpi.label }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('executive.cycleTimeComparison') }}</h3>
          <p class="text-xs text-gray-400">{{ t('executive.avgSpeedup', { x: store.avgSpeedup }) }}</p>
        </div>
        <div class="p-5 space-y-4">
          <div v-for="ct in store.cycleTime" :key="ct.category" class="space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="font-medium text-gray-700 dark:text-gray-300">{{ ct.category }}</span>
              <span class="text-gray-400">{{ ct.humanMinutes }}m vs {{ ct.agentMinutes }}m</span>
            </div>
            <div class="relative h-5 space-y-0.5">
              <div class="h-2.5 rounded bg-gray-200 dark:bg-gray-700"><div class="h-2.5 rounded bg-gray-400 dark:bg-gray-500" :style="{ width: humanBarWidth(ct.humanMinutes) }"></div></div>
              <div class="h-2.5 rounded bg-gray-200 dark:bg-gray-700"><div class="h-2.5 rounded bg-blue-500" :style="{ width: agentBarWidth(ct.agentMinutes) }"></div></div>
            </div>
          </div>
          <div class="flex items-center gap-4 pt-2 border-t border-gray-100 dark:border-gray-700">
            <div class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded bg-gray-400"></span><span class="text-[10px] text-gray-500">{{ t('executive.human') }}</span></div>
            <div class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded bg-blue-500"></span><span class="text-[10px] text-gray-500">{{ t('executive.agent') }}</span></div>
          </div>
        </div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('executive.debtReduction') }}</h3>
          <p class="text-xs text-gray-400">{{ t('executive.totalReduced', { n: store.totalDebtReduction }) }}</p>
        </div>
        <div class="p-5">
          <div class="flex items-end gap-1.5 h-40">
            <div v-for="d in store.debt" :key="d.month" class="flex-1 flex flex-col items-center gap-1">
              <div class="w-full flex flex-col items-center justify-end h-32">
                <div class="w-full rounded-t bg-green-400 dark:bg-green-500" :style="{ height: debtBarHeight(d.resolved) + 'px' }"></div>
                <div class="w-full rounded-b bg-red-300 dark:bg-red-600" :style="{ height: debtBarHeight(d.created) + 'px' }"></div>
              </div>
              <span class="text-[10px] text-gray-400">{{ d.month }}</span>
            </div>
          </div>
          <div class="flex items-center gap-4 mt-3 pt-2 border-t border-gray-100 dark:border-gray-700">
            <div class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded bg-green-400"></span><span class="text-[10px] text-gray-500">{{ t('executive.resolved') }}</span></div>
            <div class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded bg-red-300"></span><span class="text-[10px] text-gray-500">{{ t('executive.created') }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div class="border-b border-gray-200 px-5 py-4 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ t('executive.archCompliance') }}</h3>
            <p class="text-xs text-gray-400">{{ t('executive.overallScore', { score: store.overallCompliance }) }}</p>
          </div>
          <div class="text-3xl font-bold" :class="store.complianceColor(store.overallCompliance)">{{ store.overallCompliance }}</div>
        </div>
      </div>
      <div class="p-5">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="c in store.compliance" :key="c.area" class="flex items-center gap-3 rounded-lg border border-gray-100 p-3 dark:border-gray-700">
            <div class="relative h-10 w-10 shrink-0">
              <svg class="h-10 w-10 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15" fill="none" stroke-width="3" class="stroke-gray-200 dark:stroke-gray-700" />
                <circle cx="18" cy="18" r="15" fill="none" stroke-width="3" :stroke-dasharray="`${c.score * 0.942} 100`" :class="store.complianceBg(c.score)" stroke-linecap="round" />
              </svg>
              <span class="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-gray-900 dark:text-white">{{ c.score }}</span>
            </div>
            <div>
              <div class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ c.area }}</div>
              <div class="text-[10px] uppercase font-bold" :class="c.status === 'pass' ? 'text-green-600 dark:text-green-400' : c.status === 'warn' ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'">{{ c.status }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useExecutiveStore } from '@/stores/executiveStore'

const { t } = useI18n()
const store = useExecutiveStore()

const maxHuman = computed(() => Math.max(...store.cycleTime.map(c => c.humanMinutes)))
const maxAgent = computed(() => Math.max(...store.cycleTime.map(c => c.agentMinutes)))
const maxDebt = computed(() => Math.max(...store.debt.map(d => Math.max(d.resolved, d.created))))

function humanBarWidth(min: number) { return ((min / maxHuman.value) * 100) + '%' }
function agentBarWidth(min: number) { return ((min / maxAgent.value) * 100) + '%' }
function debtBarHeight(n: number) { return (n / maxDebt.value) * 128 }

function kpiBg(color: string) {
  if (color === 'green') return 'bg-green-100 dark:bg-green-900/30'
  if (color === 'blue') return 'bg-blue-100 dark:bg-blue-900/30'
  if (color === 'purple') return 'bg-purple-100 dark:bg-purple-900/30'
  return 'bg-amber-100 dark:bg-amber-900/30'
}

function kpiTextColor(color: string) {
  if (color === 'green') return 'text-green-600 dark:text-green-400'
  if (color === 'blue') return 'text-blue-600 dark:text-blue-400'
  if (color === 'purple') return 'text-purple-600 dark:text-purple-400'
  return 'text-amber-600 dark:text-amber-400'
}

function exportPNG() {
  const el = document.getElementById('executive-dashboard')
  if (!el) return
  import('html2canvas').then(({ default: html2canvas }) => {
    html2canvas(el, { backgroundColor: '#ffffff', scale: 2 }).then(canvas => {
      const link = document.createElement('a')
      link.download = 'executive-dashboard.png'
      link.href = canvas.toDataURL('image/png')
      link.click()
    })
  })
}

function exportPDF() {
  const el = document.getElementById('executive-dashboard')
  if (!el) return
  Promise.all([import('html2canvas'), import('jspdf')]).then(([html2canvasMod, jsPDFMod]) => {
    const { default: html2canvas } = html2canvasMod
    const { default: jsPDF } = jsPDFMod
    html2canvas(el, { backgroundColor: '#ffffff', scale: 2 }).then(canvas => {
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF('l', 'mm', 'a4')
      const pdfWidth = pdf.internal.pageSize.getWidth()
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
      pdf.save('executive-dashboard.pdf')
    })
  })
}
</script>
