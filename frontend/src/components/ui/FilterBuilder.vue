<template>
  <div class="filter-builder space-y-3">
    <!-- Active Filter Chips -->
    <div v-if="activeChips.length > 0" class="flex flex-wrap items-center gap-1.5">
      <span
        v-for="chip in activeChips"
        :key="chip.key"
        class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-colors"
        :class="chipClass(chip.category)"
      >
        <span class="opacity-60">{{ chip.label }}:</span>
        <span class="font-semibold">{{ chip.value }}</span>
        <button
          class="ml-0.5 rounded-full p-0.5 hover:bg-black/10 dark:hover:bg-white/10"
          :aria-label="t('filterBuilder.removeFilter', { label: chip.label })"
          @click="removeChip(chip)"
        >
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </span>
      <button
        class="text-xs font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 ml-1"
        @click="clearAll"
      >
        {{ t('filterBuilder.clearAll') }}
      </button>
    </div>

    <!-- Filter Controls Row -->
    <div class="flex flex-wrap items-center gap-2">
      <!-- Status Multi-Select -->
      <div class="relative" ref="statusDropdownRef">
        <button
          class="flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors"
          :class="uiStore.filters.status.length > 0
            ? 'border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
            : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'"
          @click="openDropdown = openDropdown === 'status' ? null : 'status'"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {{ t('filterBuilder.status') }}
          <span v-if="uiStore.filters.status.length" class="rounded-full bg-blue-200 px-1.5 text-[10px] font-bold text-blue-800 dark:bg-blue-800 dark:text-blue-200">{{ uiStore.filters.status.length }}</span>
          <svg class="h-3 w-3 text-gray-400 transition-transform" :class="{ 'rotate-180': openDropdown === 'status' }" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
        </button>
        <Teleport to="body">
          <div v-if="openDropdown === 'status'" class="fixed z-50 w-48 rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900" :style="dropdownPos">
            <div class="p-1">
              <label v-for="s in statusOptions" :key="s.value" class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                <input type="checkbox" :checked="uiStore.filters.status.includes(s.value)" class="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600" @change="toggleArrayFilter('status', s.value)" />
                <span class="text-gray-700 dark:text-gray-300">{{ s.label }}</span>
              </label>
            </div>
          </div>
        </Teleport>
      </div>

      <!-- Priority Multi-Select -->
      <div class="relative" ref="priorityDropdownRef">
        <button
          class="flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors"
          :class="uiStore.filters.priority.length > 0
            ? 'border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
            : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'"
          @click="openDropdown = openDropdown === 'priority' ? null : 'priority'"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" /></svg>
          {{ t('filterBuilder.priority') }}
          <span v-if="uiStore.filters.priority.length" class="rounded-full bg-amber-200 px-1.5 text-[10px] font-bold text-amber-800 dark:bg-amber-800 dark:text-amber-200">{{ uiStore.filters.priority.length }}</span>
          <svg class="h-3 w-3 text-gray-400 transition-transform" :class="{ 'rotate-180': openDropdown === 'priority' }" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
        </button>
        <Teleport to="body">
          <div v-if="openDropdown === 'priority'" class="fixed z-50 w-48 rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900" :style="dropdownPos">
            <div class="p-1">
              <label v-for="p in priorityOptions" :key="p.value" class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                <input type="checkbox" :checked="uiStore.filters.priority.includes(p.value)" class="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600" @change="toggleArrayFilter('priority', p.value)" />
                <span class="text-gray-700 dark:text-gray-300">{{ p.label }}</span>
              </label>
            </div>
          </div>
        </Teleport>
      </div>

      <!-- Labels Multi-Select -->
      <div class="relative" ref="labelsDropdownRef">
        <button
          class="flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors"
          :class="uiStore.filters.labels.length > 0
            ? 'border-purple-300 bg-purple-50 text-purple-700 dark:border-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
            : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'"
          @click="openDropdown = openDropdown === 'labels' ? null : 'labels'"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
          {{ t('filterBuilder.labels') }}
          <span v-if="uiStore.filters.labels.length" class="rounded-full bg-purple-200 px-1.5 text-[10px] font-bold text-purple-800 dark:bg-purple-800 dark:text-purple-200">{{ uiStore.filters.labels.length }}</span>
          <svg class="h-3 w-3 text-gray-400 transition-transform" :class="{ 'rotate-180': openDropdown === 'labels' }" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
        </button>
        <Teleport to="body">
          <div v-if="openDropdown === 'labels'" class="fixed z-50 w-48 rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900" :style="dropdownPos">
            <div class="max-h-48 overflow-y-auto p-1">
              <label v-for="label in availableLabels" :key="label" class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                <input type="checkbox" :checked="uiStore.filters.labels.includes(label)" class="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600" @change="toggleArrayFilter('labels', label)" />
                <span class="text-gray-700 dark:text-gray-300">{{ label }}</span>
              </label>
              <div v-if="availableLabels.length === 0" class="px-2 py-3 text-center text-xs text-gray-400">{{ t('filterBuilder.noLabels') }}</div>
            </div>
          </div>
        </Teleport>
      </div>

      <!-- Has Tech Debt Toggle -->
      <button
        class="flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors"
        :class="uiStore.filters.hasTechDebt === true
          ? 'border-orange-300 bg-orange-50 text-orange-700 dark:border-orange-700 dark:bg-orange-900/30 dark:text-orange-300'
          : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'"
        @click="toggleTriState('hasTechDebt')"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
        {{ t('filterBuilder.techDebt') }}
        <span v-if="uiStore.filters.hasTechDebt !== null" class="rounded-full px-1.5 text-[10px] font-bold"
          :class="uiStore.filters.hasTechDebt ? 'bg-orange-200 text-orange-800 dark:bg-orange-800 dark:text-orange-200' : 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400'">
          {{ uiStore.filters.hasTechDebt ? 'YES' : 'NO' }}
        </span>
      </button>

      <!-- Has Affected Files Toggle -->
      <button
        class="flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors"
        :class="uiStore.filters.hasAffectedFiles === true
          ? 'border-cyan-300 bg-cyan-50 text-cyan-700 dark:border-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300'
          : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'"
        @click="toggleTriState('hasAffectedFiles')"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
        {{ t('filterBuilder.files') }}
        <span v-if="uiStore.filters.hasAffectedFiles !== null" class="rounded-full px-1.5 text-[10px] font-bold"
          :class="uiStore.filters.hasAffectedFiles ? 'bg-cyan-200 text-cyan-800 dark:bg-cyan-800 dark:text-cyan-200' : 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400'">
          {{ uiStore.filters.hasAffectedFiles ? 'YES' : 'NO' }}
        </span>
      </button>

      <!-- Date Range -->
      <div class="flex items-center gap-1">
        <input
          type="date"
          :value="uiStore.filters.dateFrom"
          :aria-label="t('filterBuilder.dateFrom')"
          class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
          @change="setDateFilter('dateFrom', ($event.target as HTMLInputElement).value)"
        />
        <span class="text-xs text-gray-400">-</span>
        <input
          type="date"
          :value="uiStore.filters.dateTo"
          :aria-label="t('filterBuilder.dateTo')"
          class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
          @change="setDateFilter('dateTo', ($event.target as HTMLInputElement).value)"
        />
      </div>

      <!-- Operator Toggle -->
      <div class="flex items-center rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <button
          class="px-2 py-1.5 text-[10px] font-bold uppercase transition-colors"
          :class="uiStore.filters.operator === 'AND'
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
            : 'bg-white text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
          @click="uiStore.setFilter('operator', 'AND')"
        >AND</button>
        <button
          class="px-2 py-1.5 text-[10px] font-bold uppercase transition-colors"
          :class="uiStore.filters.operator === 'OR'
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
            : 'bg-white text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
          @click="uiStore.setFilter('operator', 'OR')"
        >OR</button>
      </div>

      <!-- Saved Searches -->
      <div class="relative" ref="savedDropdownRef">
        <button
          class="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="openDropdown = openDropdown === 'saved' ? null : 'saved'"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" /></svg>
          {{ t('filterBuilder.saved') }}
          <span v-if="uiStore.savedSearches.length" class="rounded-full bg-gray-200 px-1.5 text-[10px] font-bold text-gray-600 dark:bg-gray-700 dark:text-gray-400">{{ uiStore.savedSearches.length }}</span>
        </button>
        <Teleport to="body">
          <div v-if="openDropdown === 'saved'" class="fixed z-50 w-56 rounded-xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900" :style="dropdownPos">
            <div v-if="canSaveCurrentSearch" class="border-b border-gray-200 p-2 dark:border-gray-700">
              <div class="flex gap-1">
                <input
                  v-model="saveSearchName"
                  :placeholder="t('filterBuilder.searchName')"
                  class="flex-1 rounded-md border border-gray-300 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                  @keydown.enter="saveCurrentSearch"
                />
                <button
                  class="rounded-md bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-700"
                  @click="saveCurrentSearch"
                >{{ t('filterBuilder.save') }}</button>
              </div>
            </div>
            <div class="max-h-48 overflow-y-auto p-1">
              <div v-if="uiStore.savedSearches.length === 0" class="px-2 py-3 text-center text-xs text-gray-400">{{ t('filterBuilder.noSavedSearches') }}</div>
              <div
                v-for="search in uiStore.savedSearches"
                :key="search.id"
                class="flex items-center justify-between rounded-lg px-2 py-1.5 text-xs hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <button class="flex-1 text-left text-gray-700 dark:text-gray-300" @click="loadSavedSearch(search.id)">
                  {{ search.name }}
                </button>
                <button class="ml-1 text-gray-400 hover:text-red-500" @click="uiStore.deleteSearch(search.id)">
                  <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>
          </div>
        </Teleport>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/uiStore'

const { t } = useI18n()
const uiStore = useUiStore()

const openDropdown = ref<string | null>(null)
const saveSearchName = ref('')
const statusDropdownRef = ref<HTMLElement | null>(null)
const priorityDropdownRef = ref<HTMLElement | null>(null)
const labelsDropdownRef = ref<HTMLElement | null>(null)
const savedDropdownRef = ref<HTMLElement | null>(null)

const statusOptions = [
  { value: 'OPEN', label: t('issues.open') },
  { value: 'IN_PROGRESS', label: t('issues.inProgress') },
  { value: 'BLOCKED', label: t('issues.blocked') },
  { value: 'WAITING_HUMAN_APPROVAL', label: t('hitl.title') },
  { value: 'CLOSED', label: t('issues.closed') },
]

const priorityOptions = [
  { value: 'CRITICAL', label: t('issues.critical') },
  { value: 'HIGH', label: t('issues.high') },
  { value: 'MEDIUM', label: t('issues.medium') },
  { value: 'LOW', label: t('issues.low') },
]

const availableLabels = computed((): string[] => {
  return []
})

const dropdownPos = computed(() => ({ top: '36px', left: '0px' }))

const canSaveCurrentSearch = computed(() => uiStore.hasActiveFilters())

const activeChips = computed(() => {
  const chips: Array<{ key: string; label: string; value: string; category: string; field: string; fieldValue: unknown }> = []
  const f = uiStore.filters

  f.status.forEach(s => {
    const opt = statusOptions.find(o => o.value === s)
    chips.push({ key: `status-${s}`, label: t('filterBuilder.status'), value: opt?.label || s, category: 'status', field: 'status', fieldValue: s })
  })
  f.priority.forEach(p => {
    const opt = priorityOptions.find(o => o.value === p)
    chips.push({ key: `priority-${p}`, label: t('filterBuilder.priority'), value: opt?.label || p, category: 'priority', field: 'priority', fieldValue: p })
  })
  f.labels.forEach(l => {
    chips.push({ key: `label-${l}`, label: t('filterBuilder.labels'), value: l, category: 'labels', field: 'labels', fieldValue: l })
  })
  if (f.hasTechDebt !== null) {
    chips.push({ key: 'techDebt', label: t('filterBuilder.techDebt'), value: f.hasTechDebt ? 'YES' : 'NO', category: 'boolean', field: 'hasTechDebt', fieldValue: null })
  }
  if (f.hasAffectedFiles !== null) {
    chips.push({ key: 'affectedFiles', label: t('filterBuilder.files'), value: f.hasAffectedFiles ? 'YES' : 'NO', category: 'boolean', field: 'hasAffectedFiles', fieldValue: null })
  }
  if (f.dateFrom) {
    chips.push({ key: 'dateFrom', label: t('filterBuilder.dateFrom'), value: f.dateFrom, category: 'date', field: 'dateFrom', fieldValue: null })
  }
  if (f.dateTo) {
    chips.push({ key: 'dateTo', label: t('filterBuilder.dateTo'), value: f.dateTo, category: 'date', field: 'dateTo', fieldValue: null })
  }
  return chips
})

function chipClass(category: string): string {
  switch (category) {
    case 'status': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
    case 'priority': return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
    case 'labels': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
    case 'boolean': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'
    case 'date': return 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300'
    default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }
}

function toggleArrayFilter(field: 'status' | 'priority' | 'labels', value: string) {
  const current = [...(uiStore.filters[field] as string[])]
  const idx = current.indexOf(value)
  if (idx >= 0) current.splice(idx, 1)
  else current.push(value)
  uiStore.setFilter(field, current as never)
}

function toggleTriState(field: 'hasTechDebt' | 'hasAffectedFiles') {
  const current = uiStore.filters[field]
  if (current === null) uiStore.setFilter(field, true)
  else if (current === true) uiStore.setFilter(field, false)
  else uiStore.setFilter(field, null)
}

function setDateFilter(field: 'dateFrom' | 'dateTo', value: string) {
  uiStore.setFilter(field, value || null)
}

function removeChip(chip: { field: string; fieldValue: unknown }) {
  if (chip.field === 'hasTechDebt') {
    uiStore.setFilter('hasTechDebt', null)
  } else if (chip.field === 'hasAffectedFiles') {
    uiStore.setFilter('hasAffectedFiles', null)
  } else if (chip.field === 'dateFrom') {
    uiStore.setFilter('dateFrom', null)
  } else if (chip.field === 'dateTo') {
    uiStore.setFilter('dateTo', null)
  } else if (chip.fieldValue !== null && chip.fieldValue !== undefined) {
    if (chip.field === 'status') {
      const current = [...uiStore.filters.status]
      const idx = current.indexOf(chip.fieldValue as string)
      if (idx >= 0) current.splice(idx, 1)
      uiStore.setFilter('status', current)
    } else if (chip.field === 'priority') {
      const current = [...uiStore.filters.priority]
      const idx = current.indexOf(chip.fieldValue as string)
      if (idx >= 0) current.splice(idx, 1)
      uiStore.setFilter('priority', current)
    } else if (chip.field === 'labels') {
      const current = [...uiStore.filters.labels]
      const idx = current.indexOf(chip.fieldValue as string)
      if (idx >= 0) current.splice(idx, 1)
      uiStore.setFilter('labels', current)
    }
  }
}

function clearAll() {
  uiStore.clearFilters()
}

function saveCurrentSearch() {
  const name = saveSearchName.value.trim()
  if (!name) return
  uiStore.saveSearch(name)
  saveSearchName.value = ''
}

function loadSavedSearch(id: string) {
  uiStore.loadSearch(id)
  openDropdown.value = null
}

function handleClickOutside(e: MouseEvent) {
  const targets = [statusDropdownRef, priorityDropdownRef, labelsDropdownRef, savedDropdownRef]
  for (const refEl of targets) {
    if (refEl.value && refEl.value.contains(e.target as Node)) return
  }
  openDropdown.value = null
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>
