<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    @click.self="close"
  >
    <div class="w-full max-w-lg bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
      <div class="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full text-xl" :class="form.type === 'human' ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-purple-100 dark:bg-purple-900/30'">
            {{ form.type === 'human' ? '👤' : '🤖' }}
          </div>
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ form.type === 'human' ? t('users.newUserTitle') : t('users.newAgentTitle') }}
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ form.type === 'human' ? t('users.newUserSubtitle') : t('users.newAgentSubtitle') }}
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

      <!-- Type Toggle -->
      <div class="flex border-b border-gray-200 dark:border-gray-700">
        <button
          @click="form.type = 'human'"
          class="flex-1 py-3 text-sm font-medium transition-colors"
          :class="form.type === 'human' ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
        >
          👤 {{ t('users.human') }}
        </button>
        <button
          @click="form.type = 'agent'"
          class="flex-1 py-3 text-sm font-medium transition-colors"
          :class="form.type === 'agent' ? 'border-b-2 border-purple-500 text-purple-600 dark:text-purple-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
        >
          🤖 {{ t('users.aiAgent') }}
        </button>
      </div>

      <div class="p-4 space-y-4 max-h-[60vh] overflow-y-auto">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ form.type === 'human' ? t('users.username') : t('users.agentName') }} *
          </label>
          <input
            v-model="form.username"
            type="text"
            required
            :placeholder="form.type === 'human' ? '' : t('users.agentNamePlaceholder')"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.email') }} *
          </label>
          <input
            v-model="form.email"
            type="email"
            required
            :placeholder="form.type === 'human' ? '' : t('users.agentEmailPlaceholder')"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <div v-if="form.type === 'human'">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.role') }}
          </label>
          <select
            v-model="form.role"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option value="lead-developer">{{ t('users.leadDeveloper') }}</option>
            <option value="developer">{{ t('users.developer') }}</option>
            <option value="designer">{{ t('users.designer') }}</option>
            <option value="manager">{{ t('users.manager') }}</option>
            <option value="qa">{{ t('users.qa') }}</option>
          </select>
        </div>

        <!-- Agent-specific fields -->
        <template v-if="form.type === 'agent'">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ t('users.model') }} *
            </label>
            <select
              v-model="form.model"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            >
              <option value="">{{ t('users.selectModel') }}</option>
              <option v-for="m in modelOptions" :key="m.id" :value="m.id">
                {{ m.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ t('users.specialization') }}
            </label>
            <select
              v-model="form.specialization"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            >
              <option value="">{{ t('users.selectSpecialization') }}</option>
              <option value="code-review">{{ t('users.specCodeReview') }}</option>
              <option value="testing">{{ t('users.specTesting') }}</option>
              <option value="architecture">{{ t('users.specArchitecture') }}</option>
              <option value="documentation">{{ t('users.specDocumentation') }}</option>
              <option value="security">{{ t('users.specSecurity') }}</option>
            </select>
          </div>
        </template>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.skills') }}
          </label>
          <div class="flex flex-wrap gap-2 mb-2">
            <span
              v-for="skill in form.skills"
              :key="skill"
              class="flex items-center gap-1 rounded-md px-2 py-1 text-xs"
              :class="form.type === 'human' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'"
            >
              {{ skill }}
              <button
                @click="removeSkill(skill)"
                class="ml-1 hover:text-gray-900 dark:hover:text-gray-100"
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
              :placeholder="t('users.addSkill')"
              class="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            />
            <button
              @click="addSkill"
              class="rounded-lg px-3 py-2 text-sm font-medium text-white"
              :class="form.type === 'human' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-purple-600 hover:bg-purple-700'"
            >
              +
            </button>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.avatar') }}
          </label>
          <div class="flex gap-2">
            <button
              v-for="avatar in currentAvatarOptions"
              :key="avatar"
              @click="form.avatar = avatar"
              class="h-10 w-10 rounded-lg border-2 flex items-center justify-center text-xl transition-colors"
              :class="form.avatar === avatar ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30' : 'border-gray-200 hover:border-gray-300 dark:border-gray-700'"
            >
              {{ avatar }}
            </button>
          </div>
        </div>

        <div v-if="form.type === 'agent'">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ t('users.systemPrompt') }}
          </label>
          <textarea
            v-model="form.system_prompt"
            rows="3"
            :placeholder="t('users.systemPromptPlaceholder')"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>
      </div>

      <div class="flex items-center justify-end gap-3 border-t border-gray-200 dark:border-gray-700 p-4">
        <button
          @click="close"
          class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          {{ t('users.cancel') }}
        </button>
        <button
          @click="save"
          :disabled="!isValid"
          class="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          :class="form.type === 'human' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-purple-600 hover:bg-purple-700'"
        >
          {{ form.type === 'human' ? t('users.createUser') : t('users.createAgent') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  show: boolean
}

defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: { username: string; email: string; role: string; type: string; avatar: string; skills: string[]; model?: string; specialization?: string; system_prompt?: string }): void
}>()

const form = ref({
  username: '',
  email: '',
  role: 'developer',
  type: 'human' as 'human' | 'agent',
  avatar: '👤',
  skills: [] as string[],
  model: '',
  specialization: '',
  system_prompt: '',
})

const newSkill = ref('')

const humanAvatars = ['👤', '👩‍💻', '👨‍💻', '🧑‍💻', '👩‍🔬', '👨‍🔬', '👩‍🎨', '👨‍🎨', '👩‍💼', '👨‍💼', '🧑‍💼']
const agentAvatars = ['🤖', '🧠', '⚡', '🔬', '🛡️', '🎯', '🔧', '📊']
const currentAvatarOptions = computed(() => form.value.type === 'human' ? humanAvatars : agentAvatars)

const modelOptions = [
  { id: 'claude-3.5-sonnet', name: 'Claude 3.5 Sonnet' },
  { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
  { id: 'gpt-4o', name: 'GPT-4o' },
  { id: 'claude-3-opus', name: 'Claude 3 Opus' },
  { id: 'gemini-pro', name: 'Gemini Pro' },
  { id: 'llama-3', name: 'Llama 3' },
]

const isValid = computed(() => {
  if (!form.value.username || !form.value.email) return false
  if (form.value.type === 'agent' && !form.value.model) return false
  return true
})

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

function close() {
  emit('close')
}

function save() {
  emit('save', { ...form.value })
  form.value = { username: '', email: '', role: 'developer', type: 'human', avatar: '👤', skills: [], model: '', specialization: '', system_prompt: '' }
  close()
}
</script>
