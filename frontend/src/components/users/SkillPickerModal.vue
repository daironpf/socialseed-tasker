<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60"
    @click.self="$emit('close')"
  >
    <div class="w-full max-w-xl bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
      <div class="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 p-4">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ t('skillPicker.title') }}
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{ mode === 'agent' ? t('skillPicker.agentHint') : t('skillPicker.humanHint') }}
          </p>
        </div>
        <button
          :aria-label="t('skillPicker.close')"
          @click="$emit('close')"
          class="rounded-lg p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="p-4 space-y-3 max-h-[55vh] overflow-y-auto">
        <input
          v-model="query"
          type="text"
          :placeholder="t('skillPicker.searchPlaceholder')"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        />

        <p v-if="loading" class="text-sm text-gray-500 dark:text-gray-400">
          {{ t('skillPicker.loading') }}
        </p>
        <p v-else-if="loadError" class="text-sm text-rose-600 dark:text-rose-400">
          {{ t('skillPicker.loadError') }}
        </p>
        <p v-else-if="!filtered.length" class="text-sm text-gray-500 dark:text-gray-400">
          {{ t('skillPicker.noResults') }}
        </p>

        <div v-else class="space-y-1">
          <div
            v-for="skill in filtered"
            :key="skill.id"
            class="rounded-lg border border-gray-200 dark:border-gray-700"
          >
            <label class="flex cursor-pointer items-center gap-3 px-3 py-2">
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
                :checked="isPicked(skill.name)"
                @change="toggle(skill.name)"
              />
              <span class="flex-1 text-sm text-gray-800 dark:text-gray-200">{{ skill.name }}</span>
              <button
                v-if="skill.behavior"
                type="button"
                class="rounded border border-gray-200 px-2 py-0.5 text-[11px] text-gray-500 hover:border-blue-400 hover:text-blue-600 dark:border-gray-600 dark:text-gray-400 dark:hover:border-blue-500 dark:hover:text-blue-400"
                @click.prevent="expanded = expanded === skill.id ? null : skill.id"
              >
                {{ expanded === skill.id ? t('skillPicker.hideBehavior') : t('skillPicker.showBehavior') }}
              </button>
            </label>
            <div
              v-if="skill.behavior && expanded === skill.id"
              class="whitespace-pre-wrap border-t border-gray-200 bg-gray-50 px-3 py-2 text-[11px] leading-relaxed text-gray-600 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-300"
            >
              {{ skill.behavior }}
            </div>
          </div>
        </div>

        <!-- Human mode: free name stays allowed (backend upserts it on save, #572). -->
        <div v-if="mode === 'human'" class="flex gap-2 border-t border-gray-200 pt-3 dark:border-gray-700">
          <input
            v-model="customName"
            type="text"
            :placeholder="t('skillPicker.customPlaceholder')"
            class="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
          <button
            type="button"
            :disabled="!customName.trim()"
            @click="addCustom"
            class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {{ t('skillPicker.addCustom') }}
          </button>
        </div>

        <!-- Agent mode: new skills need name + large behavior text (#577). -->
        <div v-else class="border-t border-gray-200 pt-3 dark:border-gray-700">
          <button
            v-if="!showCreate"
            type="button"
            @click="showCreate = true"
            class="text-sm font-medium text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300"
          >
            + {{ t('skillPicker.newSkill') }}
          </button>
          <div v-else class="space-y-2">
            <input
              v-model="newName"
              type="text"
              :placeholder="t('skillPicker.newName')"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            />
            <textarea
              v-model="newBehavior"
              rows="6"
              :placeholder="t('skillPicker.newBehavior')"
              class="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            />
            <p class="text-[11px] text-gray-400 dark:text-gray-500">{{ t('skillPicker.newBehaviorHint') }}</p>
            <p v-if="createError" class="text-[11px] text-rose-600 dark:text-rose-400">
              {{ t('skillPicker.createError') }}
            </p>
            <div class="flex justify-end gap-2">
              <button
                type="button"
                @click="showCreate = false"
                class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                {{ t('skillPicker.cancel') }}
              </button>
              <button
                type="button"
                :disabled="creating || !newName.trim() || !newBehavior.trim()"
                @click="createSkill"
                class="rounded-lg bg-purple-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
              >
                {{ creating ? t('skillPicker.creating') : t('skillPicker.createAndSelect') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3 border-t border-gray-200 dark:border-gray-700 p-4">
        <span class="text-xs text-gray-500 dark:text-gray-400">
          {{ t('skillPicker.selected') }}: {{ picked.length }}
        </span>
        <div class="flex gap-3">
          <button
            type="button"
            @click="$emit('close')"
            class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            {{ t('skillPicker.cancel') }}
          </button>
          <button
            type="button"
            @click="apply"
            class="rounded-lg px-4 py-2 text-sm font-medium text-white"
            :class="mode === 'agent' ? 'bg-purple-600 hover:bg-purple-700' : 'bg-blue-600 hover:bg-blue-700'"
          >
            {{ t('skillPicker.apply') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { isMockMode } from '@/api/client'
import { fetchSkills } from '@/api/catalogsApi'
import { fetchAgentSkills, createAgentSkill, type AgentSkill } from '@/api/agentSkillsApi'
import { useUsersStore } from '@/stores/usersStore'

const { t } = useI18n()

interface PickerSkill {
  id: string
  name: string
  behavior?: string
}

interface Props {
  show: boolean
  mode: 'human' | 'agent'
  selected: string[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'apply', names: string[]): void
}>()

const query = ref('')
const customName = ref('')
const picked = ref<string[]>([])
const items = ref<PickerSkill[]>([])
const loading = ref(false)
const loadError = ref(false)
const expanded = ref<string | null>(null)
const showCreate = ref(false)
const newName = ref('')
const newBehavior = ref('')
const creating = ref(false)
const createError = ref(false)
const usersStore = useUsersStore()

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return items.value
  return items.value.filter(skill => skill.name.toLowerCase().includes(q))
})

function isPicked(name: string): boolean {
  return picked.value.some(entry => entry.toLowerCase() === name.toLowerCase())
}

function toggle(name: string) {
  if (isPicked(name)) {
    picked.value = picked.value.filter(entry => entry.toLowerCase() !== name.toLowerCase())
  } else {
    picked.value = [...picked.value, name]
  }
}

function addCustom() {
  const name = customName.value.trim()
  if (!name) return
  if (!isPicked(name)) picked.value = [...picked.value, name]
  if (!items.value.some(skill => skill.name.toLowerCase() === name.toLowerCase())) {
    items.value = [...items.value, { id: name.toLowerCase(), name }]
  }
  customName.value = ''
}

async function createSkill() {
  const name = newName.value.trim()
  const behavior = newBehavior.value.trim()
  if (!name || !behavior) return
  creating.value = true
  createError.value = false
  try {
    let skill: AgentSkill
    if (isMockMode()) {
      skill = { id: name.toLowerCase(), name, behavior }
    } else {
      skill = await createAgentSkill(name, behavior)
    }
    items.value = [...items.value.filter(entry => entry.id !== skill.id), skill]
    if (!isPicked(skill.name)) picked.value = [...picked.value, skill.name]
    newName.value = ''
    newBehavior.value = ''
    showCreate.value = false
  } catch {
    createError.value = true
  } finally {
    creating.value = false
  }
}

async function loadCatalog() {
  loading.value = true
  loadError.value = false
  try {
    if (isMockMode()) {
      // Mock derives the vocabulary from the in-memory dataset (#576 pattern).
      const pool = props.mode === 'agent'
        ? usersStore.users.filter(user => user.type === 'agent')
        : usersStore.users
      const seen = new Map<string, PickerSkill>()
      for (const user of pool) {
        for (const name of user.skills) {
          if (!seen.has(name.toLowerCase())) seen.set(name.toLowerCase(), { id: name.toLowerCase(), name })
        }
      }
      items.value = Array.from(seen.values()).sort((a, b) => a.name.localeCompare(b.name))
    } else if (props.mode === 'agent') {
      const rows = await fetchAgentSkills()
      items.value = rows.map(row => ({ id: row.id, name: row.name, behavior: row.behavior }))
    } else {
      const rows = await fetchSkills()
      items.value = rows.map(row => ({ id: row.id, name: row.name }))
    }
  } catch {
    // Degrades to the free-name row (human) / create form (agent).
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function apply() {
  emit('apply', [...picked.value])
  emit('close')
}

watch(
  () => props.show,
  visible => {
    if (visible) {
      picked.value = [...props.selected]
      query.value = ''
      customName.value = ''
      expanded.value = null
      showCreate.value = false
      newName.value = ''
      newBehavior.value = ''
      createError.value = false
      void loadCatalog()
    }
  },
  { immediate: true },
)
</script>
