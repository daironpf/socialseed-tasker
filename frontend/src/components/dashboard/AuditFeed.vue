<template>
  <ModuleCard :title="t('boardModules.auditTitle')">
    <template #action>
      <span
        v-if="critical > 0"
        class="rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold text-red-700 dark:bg-red-900/40 dark:text-red-300"
      >
        {{ critical }}
      </span>
    </template>

    <div v-if="recent.length === 0" class="text-sm text-gray-400">
      {{ t('boardModules.auditEmpty') }}
    </div>

    <ul v-else class="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
      <li v-for="e in recent" :key="e.id" class="flex items-start gap-2.5">
        <span
          class="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full"
          :class="SEVERITY_DOT[e.severity]"
        />
        <div class="min-w-0 flex-1">
          <p class="flex items-center gap-2 text-xs font-semibold text-gray-900 dark:text-white">
            <span class="truncate">{{ t(`auditLog.eventTypes.${e.eventType}`) }}</span>
            <span
              class="flex-shrink-0 text-[9px] font-bold uppercase"
              :class="SEVERITY_TEXT[e.severity]"
            >
              {{ t(`auditLog.severities.${e.severity}`) }}
            </span>
          </p>
          <p class="truncate text-[10px] text-gray-400 dark:text-gray-500">
            {{ e.actor }} · <span class="font-mono">{{ e.resource }}</span>
          </p>
        </div>
        <span class="flex-shrink-0 text-[10px] text-gray-400 dark:text-gray-500">
          {{ timeOf(e.timestamp) }}
        </span>
      </li>
    </ul>

    <div class="mt-3 border-t border-gray-100 pt-2.5 text-right dark:border-gray-700">
      <RouterLink
        to="/audit-log"
        class="text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
      >
        {{ t('boardModules.viewAll') }} →
      </RouterLink>
    </div>
  </ModuleCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ModuleCard from './ModuleCard.vue'
import { useAuditLogStore } from '@/stores/auditLogStore'
import type { AuditLogSeverity } from '@/types/auditLog'

const { t } = useI18n()

const auditStore = useAuditLogStore()

const SEVERITY_DOT: Record<AuditLogSeverity, string> = {
  LOW: 'bg-blue-500',
  MEDIUM: 'bg-amber-500',
  HIGH: 'bg-orange-500',
  CRITICAL: 'bg-red-500',
}

const SEVERITY_TEXT: Record<AuditLogSeverity, string> = {
  LOW: 'text-blue-600 dark:text-blue-400',
  MEDIUM: 'text-amber-600 dark:text-amber-400',
  HIGH: 'text-orange-600 dark:text-orange-400',
  CRITICAL: 'text-red-600 dark:text-red-400',
}

const recent = computed(() => auditStore.entries.slice(0, 6))

const critical = computed(() => auditStore.severityCounts.CRITICAL ?? 0)

function timeOf(ts: string): string {
  const d = new Date(ts)
  const sameDay = d.toDateString() === new Date().toDateString()
  return sameDay
    ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString([], { day: '2-digit', month: '2-digit' })
}
</script>
