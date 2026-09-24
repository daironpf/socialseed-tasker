<template>
  <div class="overflow-x-auto rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
    <table class="w-full text-left text-xs">
      <thead>
        <tr class="border-b border-gray-200 text-[10px] uppercase text-gray-400 dark:border-gray-700">
          <th class="px-4 py-3 font-semibold">{{ t('auditLog.columns.timestamp') }}</th>
          <th class="px-4 py-3 font-semibold">{{ t('auditLog.columns.actor') }}</th>
          <th class="px-4 py-3 font-semibold">{{ t('auditLog.columns.event') }}</th>
          <th class="px-4 py-3 font-semibold">{{ t('auditLog.columns.severity') }}</th>
          <th class="px-4 py-3 font-semibold">{{ t('auditLog.columns.resource') }}</th>
          <th class="px-4 py-3 font-semibold">{{ t('auditLog.columns.action') }}</th>
          <th class="px-4 py-3 font-semibold">{{ t('auditLog.columns.ip') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="entry in entries"
          :key="entry.id"
          class="border-b border-gray-100 last:border-0 hover:bg-gray-50 dark:border-gray-700/50 dark:hover:bg-gray-700/40"
        >
          <td class="whitespace-nowrap px-4 py-2.5 font-mono text-[11px] text-gray-500 dark:text-gray-400">
            {{ formatTimestamp(entry.timestamp) }}
          </td>
          <td class="px-4 py-2.5">
            <div class="flex items-center gap-2">
              <span
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
                :class="actorTypeClass(entry.actorType)"
              >
                {{ entry.actor.slice(0, 2).toUpperCase() }}
              </span>
              <div class="min-w-0">
                <div class="truncate font-medium text-gray-800 dark:text-gray-200">{{ entry.actor }}</div>
                <div class="text-[10px] uppercase text-gray-400">{{ t(`auditLog.actorTypes.${entry.actorType}`) }}</div>
              </div>
            </div>
          </td>
          <td class="px-4 py-2.5">
            <span class="rounded px-1.5 py-0.5 text-[10px] font-bold" :class="eventClass(entry.eventType)">
              {{ t(`auditLog.eventTypes.${entry.eventType}`) }}
            </span>
          </td>
          <td class="px-4 py-2.5">
            <span class="rounded-full px-2 py-0.5 text-[10px] font-bold" :class="severityClass(entry.severity)">
              {{ t(`auditLog.severities.${entry.severity}`) }}
            </span>
          </td>
          <td class="whitespace-nowrap px-4 py-2.5 font-mono text-[11px] text-gray-600 dark:text-gray-300">
            {{ entry.resource }}
          </td>
          <td class="max-w-[220px] truncate px-4 py-2.5 text-gray-700 dark:text-gray-300" :title="entry.action">
            {{ entry.action }}
          </td>
          <td class="whitespace-nowrap px-4 py-2.5 font-mono text-[11px] text-gray-400">
            {{ entry.ip || '—' }}
          </td>
        </tr>
        <tr v-if="entries.length === 0">
          <td colspan="7" class="px-4 py-10 text-center text-gray-400">
            {{ t('common.noData') }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { AuditLogEntry, AuditLogEventType, AuditLogSeverity } from '@/types/auditLog'

defineProps<{
  entries: AuditLogEntry[]
}>()

const { t } = useI18n()

function formatTimestamp(iso: string): string {
  return iso.replace('T', ' ').slice(0, 19)
}

function actorTypeClass(type: AuditLogEntry['actorType']): string {
  if (type === 'agent') return 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300'
  if (type === 'system') return 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
  return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
}

function severityClass(severity: AuditLogSeverity): string {
  if (severity === 'CRITICAL') return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
  if (severity === 'HIGH') return 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300'
  if (severity === 'MEDIUM') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
  return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
}

function eventClass(type: AuditLogEventType): string {
  switch (type) {
    case 'policy_violation':
    case 'governance_override':
      return 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-300'
    case 'hitl_decision':
    case 'pii_redaction':
      return 'bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-300'
    case 'export':
      return 'bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-300'
    case 'agent_run':
      return 'bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-300'
    default:
      return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
  }
}
</script>
