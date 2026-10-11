<template>
  <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-semibold text-gray-800 dark:text-gray-200">{{ t('agentStudio.workflows.title') }}</h2>
      <div class="flex items-center gap-2">
        <select
          v-model="sourceFilter"
          class="rounded-lg border border-gray-200 bg-gray-50 px-2 py-1 text-[11px] text-gray-700 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300"
          @change="load"
        >
          <option value="all">{{ t('agentStudio.workflows.filterAll') }}</option>
          <option value="builtin">{{ t('agentStudio.workflows.filterBuiltin') }}</option>
          <option value="custom">{{ t('agentStudio.workflows.filterCustom') }}</option>
        </select>
        <button
          class="rounded-lg border border-gray-300 px-2.5 py-1 text-[11px] font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          :disabled="loading"
          @click="toggleForm"
        >
          {{ t('agentStudio.workflows.new') }}
        </button>
        <button
          class="text-[11px] text-sky-600 hover:underline dark:text-sky-400"
          :disabled="loading"
          @click="load"
        >
          {{ t('agentStudio.workflows.retry') }}
        </button>
      </div>
    </div>

    <form v-if="formOpen" class="mb-4 space-y-2 rounded-lg border border-gray-200 p-3 dark:border-gray-700" @submit.prevent="save">
      <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <label class="block">
          <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">
            {{ t('agentStudio.workflows.slug') }}
          </span>
          <input
            v-model="form.slug"
            :disabled="Boolean(editingSlug)"
            required
            pattern="[a-z0-9]+(-[a-z0-9]+)*"
            class="w-full rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-xs text-gray-800 focus:border-sky-400 focus:outline-none disabled:opacity-60 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          />
        </label>
        <label class="block">
          <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">
            {{ t('agentStudio.workflows.name') }}
          </span>
          <input
            v-model="form.name"
            required
            class="w-full rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-xs text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          />
        </label>
      </div>
      <label class="block">
        <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">
          {{ t('agentStudio.workflows.description') }}
        </span>
        <input
          v-model="form.description"
          class="w-full rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-xs text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
        />
      </label>
      <label class="block">
        <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">
          {{ t('agentStudio.workflows.content') }}
        </span>
        <textarea
          v-model="form.content_md"
          rows="6"
          class="w-full rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 font-mono text-xs text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
        ></textarea>
      </label>
      <div class="flex items-center gap-2">
        <button
          type="submit"
          class="rounded-lg bg-sky-600 px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
          :disabled="saving"
        >
          {{ editingSlug ? t('agentStudio.workflows.save') : t('agentStudio.workflows.create') }}
        </button>
        <button
          type="button"
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-[11px] font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="formOpen = false"
        >
          {{ t('common.cancel') }}
        </button>
        <span v-if="saveError" class="text-[11px] text-rose-600 dark:text-rose-400">{{ saveError }}</span>
      </div>
    </form>

    <p v-if="loading" class="text-xs text-gray-500 dark:text-gray-400">{{ t('agentStudio.workflows.loading') }}</p>

    <div v-else-if="error" class="flex items-center gap-3">
      <span class="text-xs text-rose-600 dark:text-rose-400">{{ t('agentStudio.workflows.error') }}</span>
        <button
          class="rounded-lg border border-gray-300 px-2.5 py-1 text-[11px] font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="load"
        >
          {{ t('agentStudio.workflows.retry') }}
        </button>
    </div>

    <p v-else-if="!workflows.length" class="text-xs text-gray-500 dark:text-gray-400">{{ t('agentStudio.workflows.empty') }}</p>

    <ul v-else class="divide-y divide-gray-100 dark:divide-gray-700/60">
      <li v-for="wf in workflows" :key="wf.slug">
        <div class="flex w-full items-center gap-2 px-1 py-2">
          <button class="flex min-w-0 flex-1 items-center gap-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700/40" @click="toggleOpen(wf.slug)">
            <span
              class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold"
              :class="wf.source === 'builtin'
                ? 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300'
                : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'"
            >
              {{ t(`agentStudio.workflows.source.${wf.source}`) }}
            </span>
            <span class="truncate text-xs font-medium text-gray-700 dark:text-gray-300">{{ wf.name }}</span>
            <span class="shrink-0 text-[11px] text-gray-400 dark:text-gray-500">{{ wf.slug }}</span>
          </button>
          <div v-if="wf.source === 'custom'" class="flex shrink-0 items-center gap-1">
            <button
              class="rounded border border-gray-200 px-1.5 py-0.5 text-[10px] text-gray-500 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700"
              @click="startEdit(wf)"
            >
              {{ t('agentStudio.workflows.edit') }}
            </button>
            <button
              class="rounded border border-gray-200 px-1.5 py-0.5 text-[10px] text-rose-500 hover:bg-rose-50 dark:border-gray-600 dark:hover:bg-rose-900/30"
              :disabled="deletingSlug === wf.slug"
              @click="remove(wf.slug)"
            >
              {{ t('agentStudio.workflows.delete') }}
            </button>
          </div>
        </div>

        <div v-if="openedSlug === wf.slug" class="border-t border-gray-100 px-1 py-2 dark:border-gray-700/60">
          <p v-if="wf.description" class="mb-2 text-[11px] text-gray-500 dark:text-gray-400">{{ wf.description }}</p>
          <p v-if="detailLoading" class="text-[11px] text-gray-500 dark:text-gray-400">{{ t('agentStudio.workflows.loading') }}</p>
          <p v-else-if="detailError" class="text-[11px] text-rose-600 dark:text-rose-400">{{ t('agentStudio.workflows.error') }}</p>
          <MarkdownRenderer v-else-if="detail?.content_md" :content="detail.content_md" class="text-xs" />
          <p v-else class="text-[11px] text-gray-500 dark:text-gray-400">{{ t('agentStudio.workflows.noContent') }}</p>
        </div>
      </li>
    </ul>

    <p v-if="notice" class="mt-2 text-[11px] text-emerald-600 dark:text-emerald-400">{{ notice }}</p>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import MarkdownRenderer from '@/components/analysis/MarkdownRenderer.vue'
import {
  fetchWorkflows,
  fetchWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
} from '@/api/workflowsApi'
import type { Workflow, WorkflowSource } from '@/api/workflowsApi'

const { t } = useI18n()

const workflows = ref<Workflow[]>([])
const loading = ref(false)
const error = ref(false)
const sourceFilter = ref<'all' | WorkflowSource>('all')
const openedSlug = ref<string | null>(null)
const detail = ref<Workflow | null>(null)
const detailLoading = ref(false)
const detailError = ref(false)
const formOpen = ref(false)
const editingSlug = ref<string | null>(null)
const saving = ref(false)
const saveError = ref<string | null>(null)
const deletingSlug = ref<string | null>(null)
const notice = ref<string | null>(null)

const form = reactive({
  slug: '',
  name: '',
  description: '',
  content_md: '',
})

async function load() {
  loading.value = true
  error.value = false
  try {
    workflows.value = await fetchWorkflows(sourceFilter.value === 'all' ? undefined : sourceFilter.value)
  } catch {
    workflows.value = []
    error.value = true
  } finally {
    loading.value = false
  }
}

async function loadDetail(slug: string) {
  detailLoading.value = true
  detailError.value = false
  try {
    detail.value = await fetchWorkflow(slug)
  } catch {
    detail.value = null
    detailError.value = true
  } finally {
    detailLoading.value = false
  }
}

async function toggleOpen(slug: string) {
  if (openedSlug.value === slug) {
    openedSlug.value = null
    detail.value = null
    return
  }
  openedSlug.value = slug
  const row = workflows.value.find(wf => wf.slug === slug)
  if (row?.content_md) {
    detail.value = row
    detailError.value = false
    return
  }
  await loadDetail(slug)
}

function toggleForm() {
  formOpen.value = !formOpen.value
  editingSlug.value = null
  saveError.value = null
  form.slug = ''
  form.name = ''
  form.description = ''
  form.content_md = ''
}

function startEdit(wf: Workflow) {
  editingSlug.value = wf.slug
  formOpen.value = true
  saveError.value = null
  form.slug = wf.slug
  form.name = wf.name
  form.description = wf.description ?? ''
  form.content_md = wf.content_md ?? ''
  if (!wf.content_md && wf.slug) void loadDetail(wf.slug).then(() => {
    if (detail.value?.content_md) form.content_md = detail.value.content_md
  })
}

async function save() {
  saving.value = true
  saveError.value = null
  notice.value = null
  try {
    if (editingSlug.value) {
      await updateWorkflow(editingSlug.value, {
        name: form.name,
        description: form.description || null,
        content_md: form.content_md || null,
      })
      notice.value = t('agentStudio.workflows.updated')
    } else {
      const created = await createWorkflow({
        slug: form.slug,
        name: form.name,
        description: form.description || null,
        content_md: form.content_md || null,
      })
      notice.value = t('agentStudio.workflows.created')
      openedSlug.value = created.slug
      detail.value = created
    }
    formOpen.value = false
    editingSlug.value = null
    await load()
  } catch (err) {
    const status = (err as { status?: number } | null)?.status
    if (status === 409) saveError.value = t('agentStudio.workflows.conflict')
    else if (status === 422) saveError.value = t('agentStudio.workflows.invalid')
    else saveError.value = t('agentStudio.workflows.saveError')
  } finally {
    saving.value = false
  }
}

async function remove(slug: string) {
  deletingSlug.value = slug
  notice.value = null
  try {
    await deleteWorkflow(slug)
    notice.value = t('agentStudio.workflows.deleted')
    if (openedSlug.value === slug) {
      openedSlug.value = null
      detail.value = null
    }
    await load()
  } catch {
    saveError.value = t('agentStudio.workflows.deleteError')
  } finally {
    deletingSlug.value = null
  }
}

onMounted(load)

defineExpose({ load })
</script>
