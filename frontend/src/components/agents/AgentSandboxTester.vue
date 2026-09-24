<template>
  <div class="flex h-full flex-col rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
    <div class="flex items-center gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-700">
      <span class="text-sm font-semibold text-gray-800 dark:text-gray-200">{{ t('agentStudio.sandbox.title') }}</span>
      <span v-if="profile" class="rounded-full bg-sky-100 px-2 py-0.5 text-[10px] font-bold text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">
        {{ profile.name }} · {{ profile.model }}
      </span>
      <button
        v-if="messages.length || log.length"
        class="ml-auto rounded-lg px-2 py-1 text-[11px] text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
        @click="reset"
      >
        {{ t('agentStudio.sandbox.reset') }}
      </button>
    </div>

    <div class="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[1fr_220px]">
      <!-- Chat -->
      <div class="flex min-h-[240px] flex-col overflow-y-auto p-3 space-y-2">
        <div v-if="!profile" class="m-auto text-center text-xs text-gray-400">
          {{ t('agentStudio.sandbox.noAgent') }}
        </div>
        <template v-else>
          <div v-if="!messages.length" class="m-auto max-w-[280px] text-center text-xs text-gray-400">
            {{ t('agentStudio.sandbox.hint') }}
          </div>
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="max-w-[90%] rounded-xl px-3 py-2 text-xs"
            :class="msg.role === 'user'
              ? 'ml-auto bg-sky-600 text-white'
              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'"
          >
            <div class="mb-0.5 text-[9px] opacity-60">{{ msg.role === 'user' ? t('agentStudio.sandbox.you') : profile.name }}</div>
            {{ msg.content }}
          </div>
          <div v-if="thinking" class="flex items-center gap-1.5 px-2 text-[11px] text-gray-400">
            <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-sky-500" />
            {{ t('agentStudio.sandbox.thinking') }}
          </div>
        </template>
      </div>

      <!-- Action log -->
      <div class="border-t border-gray-100 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900/40 md:border-l md:border-t-0">
        <div class="mb-2 text-[10px] font-semibold uppercase text-gray-400">{{ t('agentStudio.sandbox.actionLog') }}</div>
        <div class="space-y-1 font-mono text-[10px] leading-relaxed text-gray-500 dark:text-gray-400">
          <div v-if="!log.length" class="text-gray-300 dark:text-gray-600">—</div>
          <div v-for="(line, i) in log" :key="i" :class="lineClass(line)">{{ line }}</div>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="flex items-end gap-2 border-t border-gray-200 p-3 dark:border-gray-700">
      <textarea
        v-model="draft"
        rows="1"
        :placeholder="t('agentStudio.sandbox.placeholder')"
        class="min-h-[38px] flex-1 resize-none rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-800 focus:border-sky-400 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
        :disabled="!profile || thinking"
        @keydown.enter.exact.prevent="send"
      />
      <button
        class="rounded-lg bg-sky-600 px-4 py-2 text-xs font-medium text-white hover:bg-sky-700 disabled:opacity-50"
        :disabled="!profile || thinking || !draft.trim()"
        @click="send"
      >
        {{ t('agentStudio.sandbox.send') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AgentProfile } from '@/types/agentStudio'

const props = defineProps<{
  profile: AgentProfile | null
}>()

const emit = defineEmits<{
  used: []
}>()

const { t } = useI18n()

const draft = ref('')
const thinking = ref(false)
const messages = ref<Array<{ role: 'user' | 'agent'; content: string }>>([])
const log = ref<string[]>([])
let timers: ReturnType<typeof setTimeout>[] = []

onUnmounted(() => timers.forEach(clearTimeout))

function schedule(fn: () => void, delay: number) {
  timers.push(setTimeout(fn, delay))
}

function hash(text: string): number {
  let h = 0
  for (let i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) >>> 0
  return h
}

function send() {
  const text = draft.value.trim()
  if (!text || !props.profile || thinking.value) return
  const profile = props.profile
  messages.value.push({ role: 'user', content: text })
  draft.value = ''
  thinking.value = true

  const lower = text.toLowerCase()
  const highRisk = /\b(delete|deploy|drop|destroy|prod)\b/.test(lower)
  const refused = highRisk && profile.limits.maxRisk === 'LOW'

  log.value.push(`› plan "${text.slice(0, 28)}${text.length > 28 ? '…' : ''}"`)
  const tools = profile.tools.slice(0, 3)
  tools.forEach((tool, i) => {
    schedule(() => log.value.push(`› tool ${tool}() ok`), 250 * (i + 1))
  })
  schedule(() => {
    if (refused) {
      log.value.push('✗ guardrail: maxRisk=LOW blocked action')
      messages.value.push({
        role: 'agent',
        content: t('agentStudio.sandbox.refused', { name: profile.name, risk: profile.limits.maxRisk }),
      })
    } else {
      log.value.push(`✓ reply via ${profile.model} (${text.split(/\s+/).length} tokens in)`)
      messages.value.push({ role: 'agent', content: buildReply(profile, text) })
    }
    thinking.value = false
    emit('used')
  }, 250 * (tools.length + 1) + 200)
}

function buildReply(profile: AgentProfile, text: string): string {
  const variants = [
    t('agentStudio.sandbox.replyAnalyze', { name: profile.name, topic: text.slice(0, 60) }),
    t('agentStudio.sandbox.replyPlan', { name: profile.name, tools: profile.tools.join(', ') || '—' }),
    t('agentStudio.sandbox.replyReport', { name: profile.name, model: profile.model }),
  ]
  const base = variants[hash(text) % variants.length]
  const toolNote = profile.tools.length
    ? ` ${t('agentStudio.sandbox.toolNote', { tool: profile.tools[hash(text + profile.model) % profile.tools.length] })}`
    : ''
  return `${base}${toolNote}`
}

function reset() {
  timers.forEach(clearTimeout)
  timers = []
  messages.value = []
  log.value = []
  thinking.value = false
  draft.value = ''
}

function lineClass(line: string): string {
  if (line.startsWith('✗')) return 'text-red-500'
  if (line.startsWith('✓')) return 'text-emerald-600 dark:text-emerald-400'
  if (line.startsWith('›')) return 'text-sky-600 dark:text-sky-400'
  return ''
}
</script>
