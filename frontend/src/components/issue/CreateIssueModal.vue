<template>
  <div class="relative w-full max-w-lg rounded-lg bg-white shadow-xl dark:bg-gray-800">
    <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ t('issues.createIssue') }}</h3>
      <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" @click="$emit('close')">
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="submit">
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('issues.titleField') }} *</label>
        <input
          v-model="form.title"
          required
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('issues.description') }}</label>
        <textarea v-model="form.description" rows="3" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100" />
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('issues.priority') }}</label>
          <select v-model="form.priority" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100">
            <option value="LOW">{{ t('issues.low') }}</option>
            <option value="MEDIUM">{{ t('issues.medium') }}</option>
            <option value="HIGH">{{ t('issues.high') }}</option>
            <option value="CRITICAL">{{ t('issues.critical') }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('issues.component') }} *</label>
          <select v-model="form.component_id" required class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100">
            <option value="">{{ t('issues.selectComponent') }}</option>
            <option v-for="c in componentsStore.components" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('issues.assignee') }}</label>
        <select v-model="form.assignee" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100">
          <option value="">{{ t('issues.unassigned') }}</option>
          <option v-for="u in usersStore.users" :key="u.id" :value="u.id">
            {{ u.avatar }} {{ u.username }} ({{ u.type === 'agent' ? 'AI' : 'Human' }})
          </option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('issues.labels') }}</label>
        <div class="flex flex-wrap gap-1">
          <span v-for="(label, idx) in form.labels" :key="idx" class="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs dark:bg-gray-700">
            {{ label }}
            <button type="button" class="text-gray-400 hover:text-gray-600" @click="form.labels.splice(idx, 1)">x</button>
          </span>
          <input v-model="newLabel" :placeholder="t('issues.addLabel')" class="rounded-md border border-gray-300 bg-transparent px-2 py-0.5 text-xs focus:border-brand-500 focus:outline-none dark:border-gray-600" @keydown.enter.prevent="addLabel" />
        </div>
      </div>
      <div v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</div>
      <div class="flex justify-end gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
        <button type="button" class="rounded-md px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700" @click="$emit('close')">{{ t('issues.cancel') }}</button>
        <button type="submit" class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600">{{ t('issues.create') }}</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useComponentsStore } from '@/stores/componentsStore'
import { useIssuesStore } from '@/stores/issuesStore'
import { useUsersStore } from '@/stores/usersStore'
import { IssuePriority } from '@/types'

const { t } = useI18n()

const emit = defineEmits<{ close: []; created: [] }>()

const componentsStore = useComponentsStore()
const issuesStore = useIssuesStore()
const usersStore = useUsersStore()

const form = ref({
  title: '',
  description: '',
  priority: IssuePriority.MEDIUM,
  component_id: '',
  assignee: '',
  labels: [] as string[],
})
const newLabel = ref('')
const error = ref('')

onMounted(async () => {
  await usersStore.fetchUsers()
})

function addLabel() {
  const l = newLabel.value.trim()
  if (l && !form.value.labels.includes(l)) form.value.labels.push(l)
  newLabel.value = ''
}

async function submit() {
  error.value = ''
  if (!form.value.title || !form.value.component_id) {
    error.value = t('issues.titleRequired')
    return
  }
  const result = await issuesStore.createIssue({
    ...form.value,
    created_by: 'user-local',
  })
  if (result) {
    emit('created')
  } else {
    error.value = issuesStore.error ?? t('issues.failedCreate')
  }
}
</script>
