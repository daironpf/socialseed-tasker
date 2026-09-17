<template>
  <div class="flex h-full flex-col border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
    <div class="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
      <h2 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('chat.title') }}</h2>
      <button
        class="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
        :aria-label="t('chat.newConversation')"
        @click="$emit('newConversation')"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>

    <div class="px-3 py-2">
      <div class="relative">
        <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="chatStore.searchQuery"
          type="text"
          :placeholder="t('chat.search')"
          class="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-9 pr-3 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div v-if="chatStore.filteredConversations.length === 0" class="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
        {{ t('chat.noConversations') }}
      </div>

      <button
        v-for="conv in chatStore.filteredConversations"
        :key="conv.id"
        class="flex w-full items-center gap-3 border-b border-gray-100 px-4 py-3 text-left transition-colors hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800/50"
        :class="{ 'bg-blue-50 dark:bg-blue-900/10': conv.id === chatStore.activeConversationId }"
        @click="chatStore.selectConversation(conv.id)"
      >
        <div class="relative flex-shrink-0">
          <div
            class="flex h-11 w-11 items-center justify-center rounded-full text-lg"
            :class="conv.type === 'agent' ? 'bg-purple-100 dark:bg-purple-900/30' : conv.type === 'group' ? 'bg-green-100 dark:bg-green-900/30' : 'bg-blue-100 dark:bg-blue-900/30'"
          >
            {{ conv.avatar || getConvIcon(conv) }}
          </div>
          <span
            v-if="isOnline(conv)"
            class="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white dark:border-gray-900 bg-green-500"
          ></span>
        </div>

        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-1">
            <span class="truncate text-sm font-medium text-gray-900 dark:text-white">{{ conv.name }}</span>
            <span v-if="conv.isPinned" class="text-gray-400">📌</span>
          </div>
          <p class="mt-0.5 truncate text-xs text-gray-500 dark:text-gray-400">
            {{ conv.lastMessage?.content || conv.description || t('chat.noMessages') }}
          </p>
        </div>

        <div class="flex flex-col items-end gap-1">
          <span v-if="conv.lastMessage" class="text-[10px] text-gray-400 dark:text-gray-500">
            {{ formatShortTime(conv.updatedAt) }}
          </span>
          <span
            v-if="conv.unreadCount > 0"
            class="flex h-5 min-w-5 items-center justify-center rounded-full bg-blue-600 px-1.5 text-[10px] font-bold text-white"
          >
            {{ conv.unreadCount > 99 ? '99+' : conv.unreadCount }}
          </span>
        </div>
      </button>
    </div>

    <div class="border-t border-gray-200 px-4 py-2 dark:border-gray-700">
      <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        <span class="h-2 w-2 rounded-full bg-green-500"></span>
        {{ t('chat.online', { count: onlineCount }) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useChatStore } from '@/stores/chatStore'
import type { Conversation } from '@/types/chat'

defineEmits<{
  newConversation: []
}>()

const { t } = useI18n()
const chatStore = useChatStore()

const onlineCount = computed(() => chatStore.getOnlineParticipants().length)

function getConvIcon(conv: Conversation): string {
  if (conv.type === 'group') return '👥'
  if (conv.type === 'agent') return '🤖'
  const other = conv.participants.find(p => p.id !== 'admin')
  return other?.avatar || '👤'
}

function isOnline(conv: Conversation): boolean {
  if (conv.type === 'group') return conv.participants.some(p => p.id !== 'admin' && p.isOnline)
  const other = conv.participants.find(p => p.id !== 'admin')
  return other?.isOnline || false
}

function formatShortTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  const diffHrs = Math.floor(diffMin / 60)

  if (diffMin < 1) return t('chat.now')
  if (diffMin < 60) return `${diffMin}m`
  if (diffHrs < 24) return `${diffHrs}h`
  return `${Math.floor(diffHrs / 24)}d`
}
</script>
