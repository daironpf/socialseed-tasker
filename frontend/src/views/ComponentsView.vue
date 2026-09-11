<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Componentes</h1>
        <p class="text-sm text-gray-500">Gestión de módulos del sistema</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="flex rounded-lg border border-gray-300 dark:border-gray-600">
          <button
            class="px-3 py-1.5 text-sm"
            :class="viewMode === 'table' ? 'bg-gray-100 dark:bg-gray-700 font-medium' : ''"
            @click="viewMode = 'table'"
          >Table</button>
          <button
            class="px-3 py-1.5 text-sm"
            :class="viewMode === 'grid' ? 'bg-gray-100 dark:bg-gray-700 font-medium' : ''"
            @click="viewMode = 'grid'"
          >Grid</button>
        </div>
        <button
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          @click="openCreateModal"
        >
          + Nuevo Componente
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="relative">
      <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        v-model="search"
        type="text"
        placeholder="Search by name, alias, or UUID..."
        class="w-full rounded-lg border border-gray-300 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
      />
    </div>

    <!-- Table View -->
    <div v-if="viewMode === 'table'" class="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Alias</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Description</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Project</th>
            <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Issues</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
          <tr
            v-for="comp in filteredComponents"
            :key="comp.id"
            class="cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
            @click="openDetail(comp)"
          >
            <td class="px-4 py-3">
              <span class="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100 text-xs font-bold text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
                {{ comp.alias || comp.name.slice(0, 2).toUpperCase() }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ comp.name }}</td>
            <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">{{ comp.description || '—' }}</td>
            <td class="px-4 py-3 text-sm text-gray-500">{{ comp.project }}</td>
            <td class="px-4 py-3 text-center">
              <span class="inline-flex h-6 min-w-[24px] items-center justify-center rounded-full bg-blue-100 px-2 text-xs font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                {{ getIssueCount(comp.id) }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1" @click.stop>
                <button class="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-blue-600 dark:hover:bg-gray-700" @click="openEditModal(comp)">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                </button>
                <button class="rounded p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20" @click="confirmDelete(comp)">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredComponents.length === 0">
            <td colspan="6" class="px-4 py-12 text-center text-sm text-gray-400">No components found</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Grid View -->
    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="comp in filteredComponents"
        :key="comp.id"
        class="cursor-pointer rounded-xl border border-gray-200 bg-white p-5 transition-all hover:shadow-lg dark:border-gray-700 dark:bg-gray-800"
        @click="openDetail(comp)"
      >
        <div class="mb-3 flex items-center gap-3">
          <span class="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-purple-100 text-sm font-bold text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
            {{ comp.alias || comp.name.slice(0, 2).toUpperCase() }}
          </span>
          <div class="flex-1">
            <h3 class="font-semibold text-gray-900 dark:text-white">{{ comp.name }}</h3>
            <p class="text-xs text-gray-500">{{ comp.project }}</p>
          </div>
          <span class="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
            {{ getIssueCount(comp.id) }} issues
          </span>
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{{ comp.description || 'No description' }}</p>
        <div class="mt-3 flex items-center justify-between text-xs text-gray-400">
          <span>UUID: {{ comp.id.slice(0, 8) }}...</span>
          <span>{{ new Date(comp.updated_at).toLocaleDateString() }}</span>
        </div>
      </div>
    </div>

    <!-- Detail Panel -->
    <div
      v-if="selectedComponent"
      class="fixed inset-0 z-50 flex justify-end bg-black/50"
      @click.self="selectedComponent = null"
    >
      <div class="h-full w-full max-w-2xl overflow-y-auto bg-white shadow-2xl dark:bg-gray-800">
        <div class="sticky top-0 z-10 border-b border-gray-200 bg-white px-6 py-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span class="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-purple-100 text-sm font-bold text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
                {{ selectedComponent.alias || selectedComponent.name.slice(0, 2).toUpperCase() }}
              </span>
              <div>
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ selectedComponent.name }}</h2>
                <p class="text-xs text-gray-500 font-mono">{{ selectedComponent.id }}</p>
              </div>
            </div>
            <button class="text-gray-400 hover:text-gray-600" @click="selectedComponent = null">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
        </div>

        <div class="p-6 space-y-6">
          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Description</label>
            <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedComponent.description || 'No description' }}</p>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Project</label>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ selectedComponent.project }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 dark:text-gray-400">Last Updated</label>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ new Date(selectedComponent.updated_at).toLocaleString() }}</p>
            </div>
          </div>

          <!-- Status breakdown -->
          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-3 block">Issues by Status</label>
            <div class="grid grid-cols-4 gap-3">
              <div v-for="stat in componentStats" :key="stat.status" class="rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-center">
                <div class="text-xl font-bold" :class="stat.color">{{ stat.count }}</div>
                <div class="text-[10px] text-gray-500 uppercase">{{ stat.label }}</div>
              </div>
            </div>
          </div>

          <!-- Issues list -->
          <div>
            <label class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-3 block">
              Associated Issues ({{ componentIssues.length }})
            </label>
            <div v-if="componentIssues.length === 0" class="rounded-lg border border-dashed border-gray-300 dark:border-gray-600 p-8 text-center text-sm text-gray-400">
              No issues associated with this component
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="issue in componentIssues"
                :key="issue.id"
                class="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 px-3 py-2"
              >
                <div class="flex items-center gap-2">
                  <span class="font-mono text-xs font-bold text-gray-500">{{ issue.id }}</span>
                  <span class="text-sm text-gray-800 dark:text-gray-200">{{ issue.title }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="rounded px-1.5 py-0.5 text-[10px] font-bold" :class="statusClass(issue.status)">{{ issue.status }}</span>
                  <span class="rounded px-1.5 py-0.5 text-[10px] font-bold" :class="priorityClass(issue.priority)">{{ issue.priority }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button class="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700" @click="openEditModal(selectedComponent); selectedComponent = null">
              Edit Component
            </button>
            <button class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700" @click="confirmDelete(selectedComponent); selectedComponent = null">
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="closeModal">
      <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl dark:bg-gray-800">
        <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          {{ editingComponent ? 'Edit Component' : 'New Component' }}
        </h2>
        <div class="space-y-4">
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Alias</label>
              <input v-model="form.alias" maxlength="4" placeholder="FE" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
            </div>
            <div class="col-span-2">
              <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Name *</label>
              <input v-model="form.name" placeholder="Component name" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
            </div>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Description</label>
            <textarea v-model="form.description" rows="3" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Project</label>
            <input v-model="form.project" class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
          </div>
        </div>
        <div class="mt-6 flex justify-end gap-2">
          <button class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700" @click="closeModal">Cancel</button>
          <button
            :disabled="!form.name"
            class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            @click="saveComponent"
          >
            {{ editingComponent ? 'Save' : 'Create' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { fetchComponents, createComponent, updateComponent, deleteComponent, fetchIssues } from '@/api/mockApi'
import type { Component, Issue } from '@/types'

const components = ref<Component[]>([])
const issues = ref<Issue[]>([])
const search = ref('')
const viewMode = ref<'table' | 'grid'>('table')
const selectedComponent = ref<Component | null>(null)
const showModal = ref(false)
const editingComponent = ref<Component | null>(null)

const form = ref({ name: '', alias: '', description: '', project: 'socialseed-tasker' })

const filteredComponents = computed(() => {
  if (!search.value) return components.value
  const q = search.value.toLowerCase()
  return components.value.filter(c =>
    c.name.toLowerCase().includes(q) ||
    (c.alias && c.alias.toLowerCase().includes(q)) ||
    c.id.toLowerCase().includes(q)
  )
})

function getIssueCount(componentId: string): number {
  return issues.value.filter(i => i.component_id === componentId).length
}

const componentIssues = computed(() => {
  if (!selectedComponent.value) return []
  return issues.value.filter(i => i.component_id === selectedComponent.value!.id)
})

const componentStats = computed(() => {
  if (!selectedComponent.value) return []
  const ci = componentIssues.value
  return [
    { status: 'OPEN', label: 'Open', count: ci.filter(i => i.status === 'OPEN').length, color: 'text-blue-600 dark:text-blue-400' },
    { status: 'IN_PROGRESS', label: 'In Progress', count: ci.filter(i => i.status === 'IN_PROGRESS').length, color: 'text-amber-600 dark:text-amber-400' },
    { status: 'BLOCKED', label: 'Blocked', count: ci.filter(i => i.status === 'BLOCKED').length, color: 'text-red-600 dark:text-red-400' },
    { status: 'CLOSED', label: 'Closed', count: ci.filter(i => i.status === 'CLOSED').length, color: 'text-green-600 dark:text-green-400' },
  ]
})

function statusClass(status: string) {
  const m: Record<string, string> = {
    OPEN: 'bg-blue-100 text-blue-700', IN_PROGRESS: 'bg-amber-100 text-amber-700',
    BLOCKED: 'bg-red-100 text-red-700', CLOSED: 'bg-green-100 text-green-700',
  }
  return m[status] || 'bg-gray-100 text-gray-700'
}

function priorityClass(priority: string) {
  const m: Record<string, string> = {
    CRITICAL: 'bg-red-100 text-red-700', HIGH: 'bg-orange-100 text-orange-700',
    MEDIUM: 'bg-yellow-100 text-yellow-700', LOW: 'bg-gray-100 text-gray-700',
  }
  return m[priority] || 'bg-gray-100 text-gray-700'
}

function openDetail(comp: Component) { selectedComponent.value = comp }

function openCreateModal() {
  editingComponent.value = null
  form.value = { name: '', alias: '', description: '', project: 'socialseed-tasker' }
  showModal.value = true
}

function openEditModal(comp: Component) {
  editingComponent.value = comp
  form.value = { name: comp.name, alias: comp.alias || '', description: comp.description || '', project: comp.project }
  showModal.value = true
}

function closeModal() { showModal.value = false; editingComponent.value = null }

async function saveComponent() {
  if (!form.value.name) return
  try {
    if (editingComponent.value) {
      const updated = await updateComponent(editingComponent.value.id, form.value)
      const idx = components.value.findIndex(c => c.id === editingComponent.value!.id)
      if (idx !== -1) components.value[idx] = updated
    } else {
      const created = await createComponent(form.value)
      components.value.push(created)
    }
  } catch (e) { console.error('Save failed:', e) }
  closeModal()
}

async function confirmDelete(comp: Component) {
  if (!confirm(`Delete "${comp.name}"?`)) return
  try {
    await deleteComponent(comp.id)
    components.value = components.value.filter(c => c.id !== comp.id)
  } catch (e) { console.error('Delete failed:', e) }
}

onMounted(async () => {
  const [comps, iss] = await Promise.all([fetchComponents(), fetchIssues(1, 200)])
  components.value = comps
  issues.value = iss
})
</script>
