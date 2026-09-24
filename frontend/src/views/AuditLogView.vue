<template>
  <div class="space-y-4">
    <!-- Header -->
    <div id="audit-log-report" class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('auditLog.title') }}</h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('auditLog.subtitle') }}</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button
            class="rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="exportCSV(exportRows(), 'audit-log')"
          >
            {{ t('export.downloadCSV') }}
          </button>
          <button
            class="rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="exportJSON(exportRows(), 'audit-log')"
          >
            {{ t('export.downloadJSON') }}
          </button>
          <button
            class="rounded-lg bg-gray-900 px-3 py-2 text-xs font-medium text-white hover:bg-gray-700 disabled:opacity-50 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-200"
            :disabled="exportingPdf"
            @click="exportPDF"
          >
            {{ exportingPdf ? t('auditLog.generatingPdf') : t('auditLog.exportPdf') }}
          </button>
        </div>
      </div>

      <!-- Immutable chain indicator -->
      <div class="mt-4 border-t border-gray-100 pt-4 dark:border-gray-700">
        <div class="mb-2 flex items-center gap-2">
          <span class="text-[10px] font-semibold uppercase text-gray-400">{{ t('auditLog.chain.title') }}</span>
          <span class="flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
            <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            {{ t('auditLog.chain.verified') }}
          </span>
          <span class="text-[10px] text-gray-400">{{ t('auditLog.chain.blocks', { count: auditStore.chain.length }) }}</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="block in visibleChain"
            :key="block.id"
            class="rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-900/50"
            :title="t('auditLog.chain.blockTooltip', { prev: block.previousHash })"
          >
            <div class="text-[10px] font-semibold text-gray-500 dark:text-gray-400">{{ block.label }} · {{ block.count }} {{ t('auditLog.chain.events') }}</div>
            <div class="font-mono text-[11px] text-emerald-600 dark:text-emerald-400">{{ block.hash }}</div>
          </div>
        </div>
      </div>

      <!-- Severity counters -->
      <div class="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <button
          v-for="sev in AUDIT_SEVERITIES"
          :key="sev"
          class="rounded-lg border px-3 py-2 text-left transition-colors"
          :class="auditStore.filters.severity === sev
            ? severityActiveClass(sev)
            : 'border-gray-200 bg-gray-50 hover:border-gray-300 dark:border-gray-700 dark:bg-gray-900/50'"
          @click="toggleSeverity(sev)"
        >
          <div class="text-lg font-bold" :class="severityTextClass(sev)">{{ auditStore.severityCounts[sev] }}</div>
          <div class="text-[10px] font-semibold uppercase text-gray-400">{{ t(`auditLog.severities.${sev}`) }}</div>
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <div class="flex flex-wrap items-end gap-3">
        <label class="flex flex-col gap-1 text-[10px] font-semibold uppercase text-gray-400">
          {{ t('auditLog.filters.dateFrom') }}
          <input
            v-model="auditStore.filters.dateFrom"
            type="date"
            class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          >
        </label>
        <label class="flex flex-col gap-1 text-[10px] font-semibold uppercase text-gray-400">
          {{ t('auditLog.filters.dateTo') }}
          <input
            v-model="auditStore.filters.dateTo"
            type="date"
            class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          >
        </label>
        <label class="flex flex-col gap-1 text-[10px] font-semibold uppercase text-gray-400">
          {{ t('auditLog.filters.actor') }}
          <select
            v-model="auditStore.filters.actor"
            class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          >
            <option value="">{{ t('auditLog.filters.allActors') }}</option>
            <option v-for="a in auditStore.actors" :key="a" :value="a">{{ a }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1 text-[10px] font-semibold uppercase text-gray-400">
          {{ t('auditLog.filters.agent') }}
          <select
            v-model="auditStore.filters.agent"
            class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          >
            <option value="">{{ t('auditLog.filters.allAgents') }}</option>
            <option v-for="a in auditStore.agents" :key="a" :value="a">{{ a }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1 text-[10px] font-semibold uppercase text-gray-400">
          {{ t('auditLog.filters.eventType') }}
          <select
            v-model="auditStore.filters.eventType"
            class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          >
            <option value="">{{ t('auditLog.filters.allEvents') }}</option>
            <option v-for="et in AUDIT_EVENT_TYPES" :key="et" :value="et">{{ t(`auditLog.eventTypes.${et}`) }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1 text-[10px] font-semibold uppercase text-gray-400">
          {{ t('auditLog.filters.severity') }}
          <select
            v-model="auditStore.filters.severity"
            class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          >
            <option value="">{{ t('auditLog.filters.allSeverities') }}</option>
            <option v-for="sev in AUDIT_SEVERITIES" :key="sev" :value="sev">{{ t(`auditLog.severities.${sev}`) }}</option>
          </select>
        </label>
        <label class="min-w-[180px] flex-1 flex flex-col gap-1 text-[10px] font-semibold uppercase text-gray-400">
          {{ t('auditLog.filters.search') }}
          <input
            v-model="auditStore.filters.search"
            type="search"
            :placeholder="t('auditLog.filters.searchPlaceholder')"
            class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          >
        </label>
        <button
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700"
          @click="auditStore.clearFilters()"
        >
          {{ t('auditLog.filters.clear') }}
        </button>
      </div>
      <div class="mt-3 text-xs text-gray-400">
        {{ t('auditLog.showing', { shown: pageEntries.length, total: auditStore.filteredEntries.length }) }}
      </div>
    </div>

    <!-- Table + pagination -->
    <AuditLogTable :entries="pageEntries" />
    <div class="flex items-center justify-between">
      <span class="text-xs text-gray-400">
        {{ t('auditLog.page', { page: totalPages === 0 ? 0 : page, total: totalPages }) }}
      </span>
      <div class="flex gap-2">
        <button
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          :disabled="page <= 1"
          @click="page--"
        >
          {{ t('auditLog.prevPage') }}
        </button>
        <button
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          :disabled="page >= totalPages"
          @click="page++"
        >
          {{ t('auditLog.nextPage') }}
        </button>
      </div>
    </div>

    <!-- PII redaction suite -->
    <div>
      <h2 class="mb-2 text-sm font-semibold text-gray-800 dark:text-gray-200">{{ t('piiSuite.sectionTitle') }}</h2>
      <PIIRedactionPreview />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuditLogStore } from '@/stores/auditLogStore'
import { useExport } from '@/composables/useExport'
import AuditLogTable from '@/components/audit/AuditLogTable.vue'
import PIIRedactionPreview from '@/components/pii/PIIRedactionPreview.vue'
import { AUDIT_EVENT_TYPES, AUDIT_SEVERITIES, type AuditLogSeverity } from '@/types/auditLog'

const { t } = useI18n()
const auditStore = useAuditLogStore()
const { exportCSV, exportJSON } = useExport()

const PAGE_SIZE = 15
const page = ref(1)
const exportingPdf = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(auditStore.filteredEntries.length / PAGE_SIZE)))

const pageEntries = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return auditStore.filteredEntries.slice(start, start + PAGE_SIZE)
})

const visibleChain = computed(() => auditStore.chain.slice(-6))

watch(() => auditStore.filteredEntries.length, () => {
  if (page.value > totalPages.value) page.value = totalPages.value
})

function toggleSeverity(sev: AuditLogSeverity) {
  auditStore.filters.severity = auditStore.filters.severity === sev ? '' : sev
}

function severityTextClass(sev: AuditLogSeverity): string {
  if (sev === 'CRITICAL') return 'text-red-600 dark:text-red-400'
  if (sev === 'HIGH') return 'text-orange-600 dark:text-orange-400'
  if (sev === 'MEDIUM') return 'text-amber-600 dark:text-amber-400'
  return 'text-blue-600 dark:text-blue-400'
}

function severityActiveClass(sev: AuditLogSeverity): string {
  if (sev === 'CRITICAL') return 'border-red-400 bg-red-50 dark:border-red-700 dark:bg-red-900/20'
  if (sev === 'HIGH') return 'border-orange-400 bg-orange-50 dark:border-orange-700 dark:bg-orange-900/20'
  if (sev === 'MEDIUM') return 'border-amber-400 bg-amber-50 dark:border-amber-700 dark:bg-amber-900/20'
  return 'border-blue-400 bg-blue-50 dark:border-blue-700 dark:bg-blue-900/20'
}

function exportRows() {
  return auditStore.exportRows()
}

function exportPDF() {
  const el = document.getElementById('audit-log-report')
  if (!el) return
  exportingPdf.value = true
  Promise.all([import('html2canvas'), import('jspdf')]).then(([html2canvasMod, jsPDFMod]) => {
    const { default: html2canvas } = html2canvasMod
    const { default: jsPDF } = jsPDFMod
    return html2canvas(el, { backgroundColor: '#ffffff', scale: 2 }).then(canvas => {
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF('p', 'mm', 'a4')
      const pdfWidth = pdf.internal.pageSize.getWidth()
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
      pdf.save('audit-log.pdf')
    })
  }).finally(() => {
    exportingPdf.value = false
  })
}
</script>
