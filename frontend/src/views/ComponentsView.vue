<template>
  <div class="flex-1 overflow-auto p-4">
    <div class="mb-6 flex items-center justify-between">
      <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Components</h2>
      <button
        class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600"
        @click="showCreate = true"
      >
        + New Component
      </button>
    </div>

    <div v-if="componentsStore.loading" class="flex items-center justify-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="componentsStore.components.length === 0" class="text-center py-12 text-gray-400">
      No components yet. Create one to get started.
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="comp in componentsStore.components"
        :key="comp.id"
        class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow dark:border-gray-700 dark:bg-gray-800"
      >
        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ comp.name }}</h3>
        <p v-if="comp.description" class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ comp.description }}</p>
        <p class="mt-2 text-xs text-gray-400">Project: {{ comp.project }}</p>
        <p class="text-xs text-gray-400">{{ getIssueCount(comp.id) }} issues</p>
        <div class="mt-4 flex gap-2">
          <button
            class="text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400"
            @click="editComponent(comp)"
          >
            Edit
          </button>
          <button
            class="text-sm text-red-600 hover:text-red-700 dark:text-red-400"
            @click="deleteComp(comp.id)"
          >
            Delete
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showCreate"
      class="fixed inset-0 z-40 bg-black/50 flex items-center justify-center"
      @click.self="showCreate = false"
    >
      <div class="w-full max-w-md rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          {{ editingId ? 'Edit Component' : 'New Component' }}
        </h3>
        <form @submit.prevent="submitComponent" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name *</label>
            <input v-model="form.name" required class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
            <textarea v-model="form.description" rows="2" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Project *</label>
            <input v-model="form.project" required class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100" />
          </div>
          <div v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</div>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded-md px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700" @click="showCreate = false">Cancel</button>
            <button type="submit" class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600">
              {{ editingId ? 'Update' : 'Create' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useComponentsStore } from '@/stores/componentsStore'
import { useIssuesStore } from '@/stores/issuesStore'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

const componentsStore = useComponentsStore()
const issuesStore = useIssuesStore()

const showCreate = ref(false)
const editingId = ref<string | null>(null)
const error = ref('')
const form = ref({ name: '', description: '', project: '' })

function getIssueCount(componentId: string): number {
  return issuesStore.issues.filter((i) => i.component_id === componentId).length
}

function editComponent(comp: { id: string; name: string; description: string | null; project: string }) {
  editingId.value = comp.id
  form.value = { name: comp.name, description: comp.description ?? '', project: comp.project }
  showCreate.value = true
}

async function submitComponent() {
  error.value = ''
  if (!form.value.name || !form.value.project) {
    error.value = 'Name and Project are required'
    return
  }
  if (editingId.value) {
    const result = await componentsStore.updateComponent(editingId.value, { ...form.value })
    if (result) {
      showCreate.value = false
      editingId.value = null
      form.value = { name: '', description: '', project: '' }
    } else {
      error.value = componentsStore.error ?? 'Failed to update'
    }
  } else {
    const result = await componentsStore.createComponent({ ...form.value })
    if (result) {
      showCreate.value = false
      form.value = { name: '', description: '', project: '' }
    } else {
      error.value = componentsStore.error ?? 'Failed to create'
    }
  }
}

async function deleteComp(id: string) {
  if (confirm('Delete this component?')) {
    await componentsStore.deleteComponent(id, true)
  }
}

onMounted(async () => {
  await Promise.all([
    componentsStore.fetchComponents(),
    issuesStore.fetchIssues(),
  ])
})
</script>
