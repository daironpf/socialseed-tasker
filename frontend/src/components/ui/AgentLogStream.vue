<template>
  <div class="agent-log-stream flex flex-col h-full">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <div
          class="h-2 w-2 rounded-full"
          :class="{
            'bg-green-500 animate-pulse': status === 'connected',
            'bg-yellow-500 animate-pulse': status === 'connecting' || status === 'reconnecting',
            'bg-red-500': status === 'disconnected',
          }"
        />
        <span class="text-xs text-gray-500 dark:text-gray-400">{{ t('stream.status.' + status) }}</span>
        <span v-if="logs.length" class="text-[10px] text-gray-400 dark:text-gray-500">
          {{ logs.length }} {{ t('stream.entries') }}
        </span>
        <span v-if="isMockActive" class="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium"
          :class="isMockPaused
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
            : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'"
        >
          <span class="h-1.5 w-1.5 rounded-full" :class="isMockPaused ? 'bg-amber-500' : 'bg-green-500 animate-pulse'" />
          {{ isMockPaused ? t('mockStream.paused') : t('mockStream.live') }}
        </span>
        <span v-if="tokenCount && tokenCount > 0" class="text-[10px] text-purple-500 dark:text-purple-400 font-mono">
          {{ tokenCount.toLocaleString() }} tokens
        </span>
      </div>
      <div class="flex items-center gap-1">
        <!-- Speed selector -->
        <div v-if="isMockActive" class="flex items-center gap-0.5 mr-1">
          <button
            v-for="s in (['1x', '2x', '5x'] as const)"
            :key="s"
            class="rounded px-1.5 py-0.5 text-[10px] font-bold transition-colors"
            :class="mockSpeed === s
              ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
              : 'text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'"
            @click="$emit('setSpeed', s)"
          >
            {{ s }}
          </button>
        </div>
        <!-- Pause/Resume -->
        <button
          v-if="isMockActive"
          class="rounded px-2 py-1 text-[10px] font-medium transition-colors"
          :class="isMockPaused
            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
            : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'"
          @click="$emit('togglePause')"
        >
          {{ isMockPaused ? t('mockStream.resume') : t('mockStream.pause') }}
        </button>
        <button
          class="rounded px-2 py-1 text-[10px] font-medium transition-colors"
          :class="autoScroll ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'"
          @click="autoScroll = !autoScroll"
        >
          {{ t('stream.autoScroll') }}
        </button>
        <button
          v-if="status === 'connected' || isMockActive"
          class="rounded px-2 py-1 text-[10px] font-medium text-red-600 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-900/30 transition-colors"
          @click="killSwitch"
        >
          {{ t('stream.killSwitch') }}
        </button>
      </div>
    </div>

    <div
      ref="scrollContainer"
      class="flex-1 overflow-y-auto space-y-2 min-h-[200px] max-h-[400px]"
      @scroll="onScroll"
    >
      <div v-if="logs.length === 0 && status === 'disconnected'" class="flex flex-col items-center justify-center h-full text-gray-400">
        <svg class="mb-3 h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <p class="text-sm">{{ t('stream.noLogs') }}</p>
      </div>

      <div
        v-for="(log, idx) in logs"
        :key="idx"
        class="rounded-lg border p-3 transition-colors"
        :class="logTypeStyles(log.type)"
      >
        <div class="flex items-center gap-2 mb-1.5">
          <span
            class="rounded px-1.5 py-0.5 text-[10px] font-bold"
            :class="logTypeBadge(log.type)"
          >
            {{ logTypeLabel(log.type) }}
          </span>
          <span class="text-[10px] text-gray-400">{{ formatTime(log.timestamp) }}</span>
        </div>
        <div class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words">
          {{ log.content_markdown }}
        </div>
      </div>

      <div v-if="status === 'connecting' || status === 'reconnecting'" class="flex items-center justify-center py-4">
        <div class="h-4 w-4 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent"></div>
        <span class="ml-2 text-xs text-gray-500">{{ t('stream.connecting') }}</span>
      </div>
    </div>

    <div v-if="!autoScroll && logs.length > 0" class="flex justify-center pt-2">
      <button
        class="rounded-full bg-gray-200 dark:bg-gray-700 px-3 py-1 text-[10px] text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        @click="scrollToBottom"
      >
        ↓ {{ t('stream.scrollToBottom') }}
      </button>
    </div>

    <!-- Kill Switch Confirmation Modal -->
    <div
      v-if="showKillConfirm"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showKillConfirm = false"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-sm rounded-lg bg-white shadow-xl p-6 dark:bg-gray-800">
        <div class="flex items-center gap-3 mb-4">
          <div class="flex-shrink-0 rounded-full bg-red-100 p-2 dark:bg-red-900/30">
            <svg class="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('stream.killSwitch') }}</h3>
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">{{ t('stream.killConfirm') }}</p>
        <div class="flex justify-end gap-3">
          <button
            type="button"
            class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300"
            @click="showKillConfirm = false"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="button"
            class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600"
            @click="executeKill"
          >
            {{ t('stream.killSwitch') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AgentLog } from '@/types'
import type { ConnectionStatus } from '@/composables/useAgentStream'

const { t } = useI18n()

defineProps<{
  logs: AgentLog[]
  status: ConnectionStatus
  isMockActive?: boolean
  isMockPaused?: boolean
  mockSpeed?: '1x' | '2x' | '5x'
  tokenCount?: number
}>()

const emit = defineEmits<{
  killSwitch: []
  togglePause: []
  setSpeed: [speed: '1x' | '2x' | '5x']
}>()

const autoScroll = ref(true)
const scrollContainer = ref<HTMLDivElement | null>(null)
const showKillConfirm = ref(false)

function logTypeStyles(type: string): string {
  switch (type) {
    case 'reasoning': return 'border-cyan-200 dark:border-cyan-800 bg-cyan-50/50 dark:bg-cyan-900/10'
    case 'progress': return 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10'
    case 'files': return 'border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/10'
    case 'debt': return 'border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-900/10'
    default: return 'border-gray-200 dark:border-gray-700'
  }
}

function logTypeBadge(type: string): string {
  switch (type) {
    case 'reasoning': return 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300'
    case 'progress': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
    case 'files': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
    case 'debt': return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
    default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }
}

function logTypeLabel(type: string): string {
  switch (type) {
    case 'reasoning': return 'THINKING'
    case 'progress': return 'PROGRESS'
    case 'files': return 'FILES'
    case 'debt': return 'DEBT'
    default: return 'LOG'
  }
}

function formatTime(timestamp: string): string {
  try {
    return new Date(timestamp).toLocaleTimeString()
  } catch {
    return ''
  }
}

function onScroll() {
  if (!scrollContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value
  autoScroll.value = scrollHeight - scrollTop - clientHeight < 50
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  })
}

function killSwitch() {
  showKillConfirm.value = true
}

function executeKill() {
  showKillConfirm.value = false
  emit('killSwitch')
}

watch(
  () => autoScroll.value,
  (val) => {
    if (val) scrollToBottom()
  }
)
</script>
