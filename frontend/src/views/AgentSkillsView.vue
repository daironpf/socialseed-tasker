<template>
  <div class="flex-1 overflow-x-auto">
    <div v-if="loading" class="flex h-64 items-center justify-center">
      <LoadingSpinner />
    </div>

    <div v-else class="p-6">
      <div class="mb-6 flex items-center justify-between gap-3">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ t('agentSkills.title') }}
          </h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('agentSkills.subtitle') }}</p>
        </div>
        <div class="flex items-center gap-2">
          <input
            ref="fileInput"
            type="file"
            accept=".md,.markdown"
            class="hidden"
            @change="onFilePicked"
          />
          <button
            class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            :disabled="importing"
            @click="fileInput?.click()"
          >
            {{ importing ? t('agentSkills.importing') : t('agentSkills.import') }}
          </button>
          <button
            class="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
            @click="startCreate"
          >
            {{ t('agentSkills.newSkill') }}
          </button>
        </div>
      </div>

      <div
        v-if="feedback"
        class="mb-4 rounded-lg border px-4 py-2 text-sm"
        :class="
          feedbackKind === 'error'
            ? 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-900/30 dark:text-rose-400'
            : 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400'
        "
        role="status"
      >
        {{ feedback }}
      </div>

      <!-- Create / edit form: name + the full behavior text (#610). -->
      <div
        v-if="formOpen"
        class="mb-6 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
      >
        <h2 class="mb-3 font-semibold text-gray-900 dark:text-white">
          {{ editingId ? t('agentSkills.editTitle') : t('agentSkills.createTitle') }}
        </h2>
        <div class="space-y-3">
          <input
            v-model="formName"
            type="text"
            :placeholder="t('agentSkills.namePlaceholder')"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
          <textarea
            v-model="formBehavior"
            rows="10"
            :placeholder="t('agentSkills.behaviorPlaceholder')"
            class="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
          <p class="text-[11px] text-gray-400 dark:text-gray-500">
            {{ t('agentSkills.behaviorHint') }}
          </p>
          <div class="flex justify-end gap-2">
            <button
              class="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              @click="formOpen = false"
            >
              {{ t('agentSkills.cancel') }}
            </button>
            <button
              class="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
              :disabled="saving || !formName.trim() || !formBehavior.trim()"
              @click="saveForm"
            >
              {{ saving ? t('agentSkills.saving') : t('agentSkills.save') }}
            </button>
          </div>
        </div>
      </div>

      <p v-if="!skills.length" class="text-sm text-gray-500 dark:text-gray-400">
        {{ t('agentSkills.empty') }}
      </p>

      <div v-else class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <!-- Catalog list -->
        <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <input
            v-model="query"
            type="text"
            :placeholder="t('agentSkills.searchPlaceholder')"
            class="w-full border-b border-gray-200 bg-transparent px-4 py-3 text-sm focus:outline-none dark:border-gray-700 dark:text-white"
          />
          <ul class="max-h-[60vh] divide-y divide-gray-100 overflow-y-auto dark:divide-gray-700">
            <li v-for="skill in filtered" :key="skill.id">
              <button
                class="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/60"
                :class="
                  selected?.id === skill.id ? 'bg-purple-50 dark:bg-purple-900/20' : ''
                "
                @click="select(skill)"
              >
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{
                  skill.name
                }}</span>
                <span class="text-[11px] text-gray-400 dark:text-gray-500">{{ skill.id }}</span>
              </button>
            </li>
          </ul>
        </div>

        <!-- Full behavior reader -->
        <div class="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <template v-if="selected">
            <div class="flex items-center justify-between gap-3 border-b border-gray-200 px-4 py-3 dark:border-gray-700">
              <div class="min-w-0">
                <h2 class="truncate font-semibold text-gray-900 dark:text-white">
                  {{ selected.name }}
                </h2>
                <p class="text-[11px] text-gray-400 dark:text-gray-500">{{ selected.id }}</p>
              </div>
              <div class="flex shrink-0 gap-2">
                <button
                  class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                  @click="startEdit(selected)"
                >
                  {{ t('agentSkills.edit') }}
                </button>
                <button
                  v-if="!confirmDelete"
                  class="rounded-lg border border-rose-300 px-3 py-1.5 text-sm text-rose-600 hover:bg-rose-50 dark:border-rose-700 dark:text-rose-400 dark:hover:bg-rose-900/30"
                  @click="confirmDelete = true"
                >
                  {{ t('agentSkills.delete') }}
                </button>
                <template v-else>
                  <button
                    class="rounded-lg bg-rose-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-700"
                    @click="removeSelected"
                  >
                    {{ t('agentSkills.confirmDelete') }}
                  </button>
                  <button
                    class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-50 dark:border-gray-600 dark:text-gray-300"
                    @click="confirmDelete = false"
                  >
                    {{ t('agentSkills.cancel') }}
                  </button>
                </template>
              </div>
            </div>
            <div
              class="max-h-[60vh] overflow-y-auto whitespace-pre-wrap px-4 py-3 font-mono text-[13px] leading-relaxed text-gray-700 dark:text-gray-300"
            >
              {{ selected.behavior || t('agentSkills.noBehavior') }}
            </div>
          </template>
          <p v-else class="px-4 py-6 text-sm text-gray-500 dark:text-gray-400">
            {{ t('agentSkills.selectHint') }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import { isMockMode } from '@/api/client'
import {
  fetchAgentSkills,
  createAgentSkill,
  updateAgentSkill,
  deleteAgentSkill,
  importAgentSkill,
  type AgentSkill,
} from '@/api/agentSkillsApi'

const { t } = useI18n()

const skills = ref<AgentSkill[]>([])
const loading = ref(true)
const query = ref('')
const selected = ref<AgentSkill | null>(null)

const formOpen = ref(false)
const editingId = ref<string | null>(null)
const formName = ref('')
const formBehavior = ref('')
const saving = ref(false)

const importing = ref(false)
const confirmDelete = ref(false)
const feedback = ref('')
const feedbackKind = ref<'ok' | 'error'>('ok')
const fileInput = ref<HTMLInputElement | null>(null)

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return skills.value
  return skills.value.filter(skill => skill.name.toLowerCase().includes(q))
})

function setFeedback(message: string, kind: 'ok' | 'error') {
  feedbackKind.value = kind
  feedback.value = message
  if (kind === 'ok') window.setTimeout(() => (feedback.value = ''), 4000)
}

async function load() {
  loading.value = true
  try {
    skills.value = await fetchAgentSkills()
  } catch {
    setFeedback(t('agentSkills.loadError'), 'error')
  } finally {
    loading.value = false
  }
}

function select(skill: AgentSkill) {
  selected.value = skill
  confirmDelete.value = false
}

function startCreate() {
  editingId.value = null
  formName.value = ''
  formBehavior.value = ''
  formOpen.value = true
}

function startEdit(skill: AgentSkill) {
  editingId.value = skill.id
  formName.value = skill.name
  formBehavior.value = skill.behavior
  formOpen.value = true
}

async function saveForm() {
  const name = formName.value.trim()
  const behavior = formBehavior.value.trim()
  if (!name || !behavior) return
  saving.value = true
  try {
    if (isMockMode()) {
      const skill: AgentSkill = {
        id: editingId.value ?? name.toLowerCase(),
        name,
        behavior,
      }
      skills.value = upsertLocal(skill)
      selected.value = skill
    } else if (editingId.value) {
      const updated = await updateAgentSkill(editingId.value, { name, behavior })
      skills.value = upsertLocal(updated)
      selected.value = updated
    } else {
      const created = await createAgentSkill(name, behavior)
      skills.value = upsertLocal(created)
      selected.value = created
    }
    formOpen.value = false
    setFeedback(t('agentSkills.saved'), 'ok')
  } catch {
    setFeedback(editingId.value ? t('agentSkills.saveError') : t('agentSkills.createError'), 'error')
  } finally {
    saving.value = false
  }
}

async function removeSelected() {
  if (!selected.value) return
  const target = selected.value
  try {
    if (!isMockMode()) await deleteAgentSkill(target.id)
    skills.value = skills.value.filter(skill => skill.id !== target.id)
    selected.value = null
    confirmDelete.value = false
    formOpen.value = false
    setFeedback(t('agentSkills.deleted'), 'ok')
  } catch {
    setFeedback(t('agentSkills.deleteError'), 'error')
  }
}

async function onFilePicked(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  importing.value = true
  try {
    let skill: AgentSkill
    if (isMockMode()) {
      const text = (await file.text()).trim()
      const heading = /^#[ \t]+(.+)$/m.exec(text)
      const stem = file.name.replace(/\.(md|markdown)$/i, '')
      skill = { id: stem.toLowerCase(), name: heading?.[1].trim() || stem, behavior: text }
      skills.value = upsertLocal(skill)
    } else {
      skill = await importAgentSkill(file)
      skills.value = upsertLocal(skill)
    }
    selected.value = skill
    setFeedback(t('agentSkills.imported', { name: skill.name }), 'ok')
  } catch (error) {
    const status = (error as { response?: { status?: number } })?.response?.status
    setFeedback(
      status === 409 ? t('agentSkills.importConflict') : t('agentSkills.importError'),
      'error',
    )
  } finally {
    importing.value = false
  }
}

function upsertLocal(skill: AgentSkill): AgentSkill[] {
  return [...skills.value.filter(entry => entry.id !== skill.id), skill].sort((a, b) =>
    a.name.localeCompare(b.name),
  )
}

onMounted(load)
</script>
