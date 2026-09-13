<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    @click.self="close"
  >
    <div class="w-full max-w-lg bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
      <!-- Modal Header -->
      <div class="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100 text-xl dark:bg-purple-900/30">
            {{ form.avatar }}
          </div>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ isCreate ? t('agents.createAgent') : t('agents.editAgent') }}
            </h2>
            <p v-if="!isCreate" class="text-sm text-gray-500 dark:text-gray-400">
              {{ form.username }}
            </p>
          </div>
        </div>
        <button
          @click="close"
          class="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Modal Content -->
      <div class="p-4 space-y-4 max-h-[60vh] overflow-y-auto">
        <!-- Username -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('agents.name') }}
          </label>
          <input
            v-model="form.username"
            type="text"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <!-- Email -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('agents.email') }}
          </label>
          <input
            v-model="form.email"
            type="email"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <!-- Model -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('agents.model') }}
          </label>
          <select
            v-model="form.model"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option v-for="m in models" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>

        <!-- Temperature -->
        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ t('agents.temperature') }}
            </label>
            <span class="text-sm font-mono" :class="tempColor">{{ form.temperature.toFixed(2) }}</span>
          </div>
          <input
            v-model.number="form.temperature"
            type="range"
            min="0"
            max="2"
            step="0.05"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 accent-purple-600"
          />
          <div class="flex justify-between text-[10px] text-gray-400 mt-1">
            <span>{{ t('agents.tempPrecise') }}</span>
            <span>{{ t('agents.tempBalanced') }}</span>
            <span>{{ t('agents.tempCreative') }}</span>
          </div>
        </div>

        <!-- System Prompt -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('agents.systemPrompt') }}
          </label>
          <textarea
            v-model="form.system_prompt"
            rows="3"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white resize-none"
            :placeholder="t('agents.systemPromptPlaceholder')"
          />
        </div>

        <!-- Specialization -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('agents.specialization') }}
          </label>
          <input
            v-model="form.specialization"
            type="text"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <!-- Skills -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('agents.skills') }}
          </label>
          <div class="flex flex-wrap gap-2 mb-2">
            <span
              v-for="skill in form.skills"
              :key="skill"
              class="flex items-center gap-1 rounded-md bg-purple-100 px-2 py-1 text-xs text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
            >
              {{ skill }}
              <button
                @click="removeSkill(skill)"
                class="ml-1 hover:text-purple-900 dark:hover:text-purple-200"
              >
                ×
              </button>
            </span>
          </div>
          <div class="flex gap-2">
            <input
              v-model="newSkill"
              @keyup.enter="addSkill"
              type="text"
              :placeholder="t('agents.addSkill')"
              class="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            />
            <button
              @click="addSkill"
              class="rounded-lg bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700"
            >
              +
            </button>
          </div>
        </div>

        <!-- Tools -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('agents.tools') }}
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="tool in availableTools"
              :key="tool"
              @click="toggleTool(tool)"
              class="rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
              :class="form.tools.includes(tool)
                ? 'border-blue-500 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                : 'border-gray-200 text-gray-500 hover:border-gray-300 dark:border-gray-700 dark:text-gray-400'"
            >
              {{ tool }}
            </button>
          </div>
        </div>

        <!-- Folder Permissions -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('agents.writeAccess') }}
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="folder in availableFolders"
              :key="folder"
              @click="toggleFolder(folder)"
              class="rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
              :class="form.write_access.includes(folder)
                ? 'border-green-500 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                : 'border-gray-200 text-gray-500 hover:border-gray-300 dark:border-gray-700 dark:text-gray-400'"
            >
              {{ folder }}
            </button>
          </div>
        </div>

        <!-- Avatar -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('agents.avatar') }}
          </label>
          <div class="flex gap-2">
            <button
              v-for="avatar in avatarOptions"
              :key="avatar"
              @click="form.avatar = avatar"
              class="h-10 w-10 rounded-lg border-2 flex items-center justify-center text-xl transition-colors"
              :class="form.avatar === avatar ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/30' : 'border-gray-200 hover:border-gray-300 dark:border-gray-700'"
            >
              {{ avatar }}
            </button>
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="flex items-center justify-between border-t border-gray-200 dark:border-gray-700 p-4">
        <button
          v-if="!isCreate"
          @click="$emit('delete')"
          class="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20"
        >
          {{ t('agents.delete') }}
        </button>
        <div v-else></div>
        <div class="flex items-center gap-3">
          <button
            @click="close"
            class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            {{ t('agents.cancel') }}
          </button>
          <button
            @click="save"
            class="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
          >
            {{ isCreate ? t('agents.create') : t('agents.save') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface AgentForm {
  id?: string
  username: string
  email: string
  model: string
  temperature: number
  system_prompt: string
  specialization: string
  skills: string[]
  tools: string[]
  write_access: string[]
  avatar: string
}

interface Props {
  show: boolean
  agent: Record<string, any> | null
  isCreate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isCreate: false,
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: Record<string, any>): void
  (e: 'delete'): void
}>()

const defaultForm: AgentForm = {
  username: '',
  email: '',
  model: 'claude-3.5-sonnet',
  temperature: 0.7,
  system_prompt: '',
  specialization: '',
  skills: [],
  tools: [],
  write_access: [],
  avatar: '🤖',
}

const form = ref<AgentForm>({ ...defaultForm })
const newSkill = ref('')

const models = [
  { value: 'claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gemini-pro', label: 'Gemini Pro' },
  { value: 'llama-3', label: 'Llama 3' },
]

const availableTools = [
  'git-tools', 'neo4j-query', 'test-runner', 'file-manager',
  'web-search', 'api-caller', 'code-analyzer', 'doc-writer',
]

const availableFolders = [
  'src/', 'tests/', 'docs/', 'config/', 'scripts/', 'migrations/', 'mock-api/',
]

const avatarOptions = ['🤖', '🧠', '💻', '⚡', '🔧', '🎯', '🚀', '⚙️', '🔬', '🛠️']

const tempColor = computed(() => {
  const t = form.value.temperature
  if (t <= 0.3) return 'text-blue-600 dark:text-blue-400'
  if (t <= 1.0) return 'text-green-600 dark:text-green-400'
  return 'text-orange-600 dark:text-orange-400'
})

watch(() => props.agent, (agent) => {
  if (agent) {
    form.value = {
      ...defaultForm,
      ...agent,
      tools: [...(agent.tools || [])],
      write_access: [...(agent.write_access || [])],
      skills: [...(agent.skills || [])],
    }
  } else if (props.isCreate) {
    form.value = { ...defaultForm }
  }
}, { immediate: true })

function addSkill() {
  const skill = newSkill.value.trim()
  if (skill && !form.value.skills.includes(skill)) {
    form.value.skills.push(skill)
    newSkill.value = ''
  }
}

function removeSkill(skill: string) {
  form.value.skills = form.value.skills.filter(s => s !== skill)
}

function toggleTool(tool: string) {
  const idx = form.value.tools.indexOf(tool)
  if (idx >= 0) form.value.tools.splice(idx, 1)
  else form.value.tools.push(tool)
}

function toggleFolder(folder: string) {
  const idx = form.value.write_access.indexOf(folder)
  if (idx >= 0) form.value.write_access.splice(idx, 1)
  else form.value.write_access.push(folder)
}

function close() {
  emit('close')
}

function save() {
  emit('save', { ...form.value })
  close()
}
</script>
