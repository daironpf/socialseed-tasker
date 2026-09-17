<template>
  <div
    class="group flex gap-3 px-4 py-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
    :class="{ 'bg-blue-50 dark:bg-blue-900/10': isOwn }"
  >
    <div class="flex-shrink-0">
      <div
        class="flex h-9 w-9 items-center justify-center rounded-full text-sm"
        :class="senderType === 'agent' ? 'bg-purple-100 dark:bg-purple-900/30' : senderType === 'system' ? 'bg-gray-100 dark:bg-gray-700' : 'bg-blue-100 dark:bg-blue-900/30'"
      >
        {{ senderAvatar }}
      </div>
    </div>

    <div class="min-w-0 flex-1">
      <div class="flex items-baseline gap-2">
        <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ senderName }}</span>
        <span
          v-if="senderType === 'agent'"
          class="rounded bg-purple-100 px-1.5 py-0.5 text-[9px] font-bold text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
        >AI</span>
        <span v-if="senderType === 'system'" class="text-[10px] text-gray-400 dark:text-gray-500">SYSTEM</span>
        <span class="text-[10px] text-gray-400 dark:text-gray-500">{{ formattedTime }}</span>
      </div>

      <div v-if="type === 'code'" class="mt-1.5">
        <div class="flex items-center gap-2 rounded-t bg-gray-800 px-3 py-1.5 text-[10px] text-gray-400">
          <span>{{ metadata?.language || 'code' }}</span>
        </div>
        <pre class="overflow-x-auto rounded-b bg-gray-900 p-3 text-xs text-gray-200"><code>{{ content }}</code></pre>
      </div>

      <div
        v-else-if="type === 'agent_action'"
        class="mt-1.5 rounded-lg border border-purple-200 bg-purple-50 p-3 dark:border-purple-800 dark:bg-purple-900/20"
      >
        <div class="flex items-center gap-2 text-xs text-purple-700 dark:text-purple-300">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span class="font-medium">{{ content }}</span>
        </div>
        <div v-if="metadata?.issueId" class="mt-1 text-[10px] text-purple-500 dark:text-purple-400">
          {{ t('chat.issue') }} {{ metadata.issueId }}
        </div>
      </div>

      <div
        v-else-if="type === 'system'"
        class="mt-1.5 rounded-lg border border-gray-200 bg-gray-100 p-3 text-xs text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400"
      >
        {{ content }}
      </div>

      <div
        v-else
        class="mt-1.5 text-sm leading-relaxed text-gray-700 dark:text-gray-300"
        v-html="renderedContent"
      ></div>

      <div v-if="reactions && Object.keys(reactions).length > 0" class="mt-2 flex flex-wrap gap-1">
        <button
          v-for="(users, emoji) in reactions"
          :key="emoji"
          class="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-gray-50 px-2 py-0.5 text-xs hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700"
        >
          <span>{{ emoji }}</span>
          <span class="text-gray-500 dark:text-gray-400">{{ users.length }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ChatMessageType } from '@/types/chat'

const { t } = useI18n()

const props = defineProps<{
  content: string
  senderName: string
  senderAvatar: string
  senderType: 'human' | 'agent' | 'system'
  type: ChatMessageType
  metadata?: { language?: string; filename?: string; action?: string; issueId?: string }
  reactions?: Record<string, string[]>
  createdAt: string
  isOwn?: boolean
}>()

const formattedTime = computed(() => {
  const date = new Date(props.createdAt)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  const diffHrs = Math.floor(diffMin / 60)

  if (diffMin < 1) return t('chat.justNow')
  if (diffMin < 60) return t('chat.minutesAgo', { count: diffMin })
  if (diffHrs < 24) return t('chat.hoursAgo', { count: diffHrs })
  return date.toLocaleDateString()
})

const renderedContent = computed(() => {
  let html = props.content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/`([^`]+)`/g, '<code class="rounded bg-gray-100 px-1 py-0.5 text-xs font-mono dark:bg-gray-800">$1</code>')
  html = html.replace(/\n/g, '<br>')

  return html
})
</script>
