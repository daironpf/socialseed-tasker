<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('agentStudio.title') }}</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('agentStudio.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <span class="rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-bold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
          {{ t('agentStudio.activeCount', { count: store.enabledCount }) }}
        </span>
        <button
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="startNew"
        >
          {{ t('agentStudio.new') }}
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <!-- Builder -->
      <div class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-800 dark:text-gray-200">
            {{ editingId ? t('agentStudio.builder.editing') : t('agentStudio.builder.title') }}
          </h2>
          <button
            v-if="editingId"
            class="text-[11px] text-sky-600 hover:underline dark:text-sky-400"
            @click="startNew"
          >
            {{ t('agentStudio.builder.discard') }}
          </button>
        </div>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_1fr_90px]">
          <label class="block">
            <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">{{ t('agentStudio.builder.name') }}</span>
            <input
              v-model="form.name"
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
              :placeholder="t('agentStudio.builder.namePlaceholder')"
            >
          </label>
          <label class="block">
            <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">{{ t('agentStudio.builder.role') }}</span>
            <input
              v-model="form.role"
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
              :placeholder="t('agentStudio.builder.rolePlaceholder')"
            >
          </label>
          <label class="block">
            <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">{{ t('agentStudio.builder.avatar') }}</span>
            <input
              v-model="form.avatar"
              maxlength="2"
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-center text-lg focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900"
            >
          </label>
        </div>

        <div class="mt-4">
          <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">{{ t('agentStudio.builder.model') }}</span>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="model in AGENT_MODELS"
              :key="model"
              class="rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors"
              :class="form.model === model
                ? 'bg-sky-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'"
              @click="form.model = model"
            >
              {{ model }}
            </button>
          </div>
        </div>

        <div class="mt-4">
          <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">{{ t('agentStudio.builder.systemPrompt') }}</span>
          <AgentPromptEditor v-model="form.systemPrompt" :tools="form.tools" />
        </div>

        <div class="mt-4">
          <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">{{ t('agentStudio.builder.tools') }}</span>
          <div class="flex flex-wrap gap-1.5">
            <label
              v-for="tool in AGENT_TOOLS"
              :key="tool"
              class="flex cursor-pointer items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[11px] font-medium"
              :class="form.tools.includes(tool)
                ? 'border-sky-400 bg-sky-50 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300'
                : 'border-gray-200 text-gray-500 hover:border-gray-300 dark:border-gray-700 dark:text-gray-400'"
            >
              <input
                type="checkbox"
                class="sr-only"
                :checked="form.tools.includes(tool)"
                @change="toggleTool(tool)"
              >
              <span>{{ tool }}</span>
            </label>
          </div>
        </div>

        <div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <label class="block">
            <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">{{ t('agentStudio.builder.maxTokens') }}</span>
            <select
              v-model.number="form.limits.maxTokensPerRun"
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-2 py-2 text-xs text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
            >
              <option :value="2000">2k</option>
              <option :value="4000">4k</option>
              <option :value="8000">8k</option>
              <option :value="16000">16k</option>
              <option :value="32000">32k</option>
            </select>
          </label>
          <label class="block">
            <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">{{ t('agentStudio.builder.timeout') }}</span>
            <select
              v-model.number="form.limits.timeoutSeconds"
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-2 py-2 text-xs text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
            >
              <option :value="30">30s</option>
              <option :value="60">60s</option>
              <option :value="120">120s</option>
              <option :value="300">300s</option>
            </select>
          </label>
          <label class="block">
            <span class="mb-1 block text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">{{ t('agentStudio.builder.maxRisk') }}</span>
            <select
              v-model="form.limits.maxRisk"
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-2 py-2 text-xs text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
            >
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
            </select>
          </label>
        </div>

        <div class="mt-5 flex items-center gap-3">
          <button
            class="rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
            :disabled="!canSave"
            @click="save"
          >
            {{ editingId ? t('agentStudio.builder.saveChanges') : t('agentStudio.builder.saveAgent') }}
          </button>
          <button
            v-if="editingId"
            class="rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="startNew"
          >
            {{ t('common.cancel') }}
          </button>
          <span v-if="editingId" class="text-[11px] text-gray-400">{{ t('agentStudio.builder.editHint') }}</span>
        </div>
      </div>

      <!-- Sandbox -->
      <AgentSandboxTester :profile="sandboxProfile" @used="onSandboxUsed" />
    </div>

    <!-- Library -->
    <AgentLibrary
      :profiles="store.profiles"
      @edit="editProfile"
      @clone="store.cloneProfile($event)"
      @toggle="store.toggleEnabled($event)"
      @remove="store.removeProfile($event)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAgentStudioStore } from '@/stores/agentStudioStore'
import { AGENT_MODELS, AGENT_TOOLS, DEFAULT_LIMITS } from '@/types/agentStudio'
import type { AgentProfile } from '@/types/agentStudio'
import AgentPromptEditor from '@/components/agents/AgentPromptEditor.vue'
import AgentSandboxTester from '@/components/agents/AgentSandboxTester.vue'
import AgentLibrary from '@/components/agents/AgentLibrary.vue'

const { t } = useI18n()
const store = useAgentStudioStore()

const editingId = ref<string | null>(null)

const form = reactive({
  name: '',
  role: 'developer',
  avatar: '🤖',
  model: AGENT_MODELS[0],
  systemPrompt: '',
  tools: [] as string[],
  limits: { ...DEFAULT_LIMITS },
  enabled: true,
})

const canSave = computed(() => form.name.trim().length > 0 && form.systemPrompt.trim().length > 0)

const sandboxProfile = computed<AgentProfile | null>(() => {
  if (editingId.value) {
    return store.profiles.find(p => p.id === editingId.value) ?? null
  }
  if (form.name.trim() && form.systemPrompt.trim()) {
    return {
      id: 'sandbox-draft',
      name: form.name.trim() || 'draft',
      role: form.role,
      avatar: form.avatar,
      model: form.model,
      systemPrompt: form.systemPrompt,
      tools: [...form.tools],
      limits: { ...form.limits },
      enabled: form.enabled,
      createdAt: new Date().toISOString(),
    }
  }
  return store.profiles[0] ?? null
})

function startNew() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    role: 'developer',
    avatar: '🤖',
    model: AGENT_MODELS[0],
    systemPrompt: '',
    tools: [],
    limits: { ...DEFAULT_LIMITS },
    enabled: true,
  })
}

function editProfile(id: string) {
  const profile = store.profiles.find(p => p.id === id)
  if (!profile) return
  editingId.value = id
  Object.assign(form, {
    name: profile.name,
    role: profile.role,
    avatar: profile.avatar,
    model: profile.model,
    systemPrompt: profile.systemPrompt,
    tools: [...profile.tools],
    limits: { ...profile.limits },
    enabled: profile.enabled,
  })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function toggleTool(tool: string) {
  const idx = form.tools.indexOf(tool)
  if (idx >= 0) form.tools.splice(idx, 1)
  else form.tools.push(tool)
}

function save() {
  if (!canSave.value) return
  const saved = store.saveProfile(
    {
      name: form.name,
      role: form.role,
      avatar: form.avatar,
      model: form.model,
      systemPrompt: form.systemPrompt,
      tools: [...form.tools],
      limits: { ...form.limits },
      enabled: form.enabled,
    },
    editingId.value ?? undefined,
  )
  if (saved && !editingId.value) startNew()
}

function onSandboxUsed() {
  if (editingId.value) store.markUsed(editingId.value)
}
</script>
