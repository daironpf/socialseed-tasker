<template>
  <div class="audit-trail">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{{ t('audit.title') }}</h3>
      <div class="flex gap-1">
        <button
          v-for="filter in filters"
          :key="filter.key"
          class="rounded px-2 py-1 text-[10px] font-medium transition-colors"
          :class="activeFilter === filter.key
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
            : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'"
          @click="activeFilter = filter.key"
        >
          {{ filter.label }}
        </button>
      </div>
    </div>

    <!-- Timeline -->
    <div v-if="filteredEntries.length === 0" class="flex flex-col items-center justify-center py-8 text-gray-400">
      <svg class="h-8 w-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-sm">{{ t('audit.noEntries') }}</p>
    </div>

    <div v-else class="space-y-0">
      <AuditEntry
        v-for="entry in visibleEntries"
        :key="entry.id"
        :entry="entry"
      />
    </div>

    <!-- Load more -->
    <div v-if="visibleCount < filteredEntries.length" class="flex justify-center pt-2">
      <button
        class="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
        @click="loadMore"
      >
        {{ t('audit.loadMore', { n: remaining }) }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AuditEntry from './AuditEntry.vue'
import type { AuditEntry as AuditEntryType, AuditAction } from '@/types/audit'

const { t } = useI18n()

const props = defineProps<{
  entries: AuditEntryType[]
}>()

const PAGE_SIZE = 15
const activeFilter = ref<'all' | AuditAction>('all')
const visibleCount = ref(PAGE_SIZE)

const filters = computed(() => [
  { key: 'all' as const, label: t('audit.filterAll') },
  { key: 'status' as const, label: t('audit.filterStatus') },
  { key: 'priority' as const, label: t('audit.filterPriority') },
  { key: 'assignment' as const, label: t('audit.filterAssignment') },
  { key: 'agent' as const, label: t('audit.filterAgent') },
  { key: 'system' as const, label: t('audit.filterSystem') },
])

const filteredEntries = computed(() => {
  const sorted = [...props.entries].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )
  if (activeFilter.value === 'all') return sorted
  return sorted.filter(e => e.action === activeFilter.value)
})

const visibleEntries = computed(() => filteredEntries.value.slice(0, visibleCount.value))

const remaining = computed(() => Math.max(0, filteredEntries.value.length - visibleCount.value))

function loadMore() {
  visibleCount.value += PAGE_SIZE
}
</script>
