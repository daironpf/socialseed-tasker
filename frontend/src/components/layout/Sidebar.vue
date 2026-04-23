<template>
  <aside
    class="w-64 border-r border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800 flex-shrink-0"
    :class="uiStore.sidebarOpen ? '' : 'hidden'"
  >
    <div class="p-4 space-y-6">
      <div>
        <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
          Search
        </h3>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search issues..."
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          @input="uiStore.setFilter('search', searchQuery)"
        />
      </div>

      <div>
        <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
          Status
        </h3>
        <div class="space-y-1">
          <label v-for="s in statuses" :key="s" class="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              :checked="uiStore.filters.status.includes(s)"
              class="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              @change="toggleStatus(s)"
            />
            <StatusBadge :status="s" />
          </label>
        </div>
      </div>

      <div>
        <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
          Priority
        </h3>
        <div class="space-y-1">
          <label v-for="p in priorities" :key="p" class="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              :checked="uiStore.filters.priority.includes(p)"
              class="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              @change="togglePriority(p)"
            />
            <PriorityBadge :priority="p" />
          </label>
        </div>
      </div>

      <div>
        <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
          Project
        </h3>
        <select
          :value="uiStore.filters.project ?? ''"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          @change="onProjectChange"
        >
          <option value="">All Projects</option>
          <option v-for="p in componentsStore.projects" :key="p" :value="p">
            {{ p }}
          </option>
        </select>
      </div>

      <div>
        <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
          Component
        </h3>
        <select
          :value="uiStore.filters.component ?? ''"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          @change="onComponentChange"
        >
          <option value="">All Components</option>
          <option v-for="c in filteredComponents" :key="c.id" :value="c.id">
            {{ c.name }}
          </option>
        </select>
      </div>

      <button
        class="w-full text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
        @click="uiStore.clearFilters"
      >
        Clear Filters
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUiStore } from '@/stores/uiStore'
import { useComponentsStore } from '@/stores/componentsStore'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import PriorityBadge from '@/components/ui/PriorityBadge.vue'

const uiStore = useUiStore()
const componentsStore = useComponentsStore()

const searchQuery = ref('')

const statuses = ['OPEN', 'IN_PROGRESS', 'BLOCKED', 'CLOSED']
const priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

const filteredComponents = computed(() => {
  if (!uiStore.filters.project) return componentsStore.components
  return componentsStore.componentsByProject(uiStore.filters.project)
})

function toggleStatus(status: string) {
  const current = uiStore.filters.status
  const updated = current.includes(status)
    ? current.filter((s) => s !== status)
    : [...current, status]
  uiStore.setFilter('status', updated)
}

function togglePriority(priority: string) {
  const current = uiStore.filters.priority
  const updated = current.includes(priority)
    ? current.filter((p) => p !== priority)
    : [...current, priority]
  uiStore.setFilter('priority', updated)
}

function onProjectChange(event: Event) {
  const val = (event.target as HTMLSelectElement).value
  uiStore.setFilter('project', val || null)
  // Clear component filter when project changes
  uiStore.setFilter('component', null)
}

function onComponentChange(event: Event) {
  const val = (event.target as HTMLSelectElement).value
  uiStore.setFilter('component', val || null)
}
</script>
