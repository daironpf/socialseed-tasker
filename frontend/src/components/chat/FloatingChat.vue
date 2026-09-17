<template>
  <Teleport to="body">
    <!-- Chat Toggle Button -->
    <button
      v-if="!isOpen"
      class="fixed bottom-20 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition-all hover:scale-110 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
      :aria-label="t('floatingChat.open')"
      @click="toggleOpen"
    >
      <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
      <span
        v-if="chatStore.totalUnread > 0"
        class="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1.5 text-[10px] font-bold text-white"
      >
        {{ chatStore.totalUnread > 99 ? '99+' : chatStore.totalUnread }}
      </span>
    </button>

    <!-- Chat Window -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-4 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-4 scale-95"
    >
      <div
        v-if="isOpen"
        class="fixed bottom-20 right-6 z-50 flex w-[480px] overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xl dark:border-gray-700 dark:bg-gray-900"
        :class="isMinimized ? 'h-14' : 'h-[500px]'"
        style="max-height: calc(100vh - 120px)"
      >
        <!-- Header -->
        <div class="flex items-center gap-2 border-b border-gray-200 bg-blue-600 px-4 py-3 dark:border-gray-700 dark:bg-blue-600">
          <template v-if="activeConv && !showList">
            <button
              class="rounded p-1 text-white/80 hover:bg-white/20 hover:text-white"
              :aria-label="t('floatingChat.backToList')"
              @click="showList = true"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div class="flex items-center gap-2 flex-1 min-w-0">
              <span class="text-sm">{{ getConvIcon(activeConv) }}</span>
              <span class="truncate text-sm font-semibold text-white">{{ activeConv.name }}</span>
              <span
                v-if="activeConv.type === 'agent'"
                class="flex-shrink-0 rounded bg-white/20 px-1.5 py-0.5 text-[9px] font-bold text-white"
              >AI</span>
            </div>
          </template>
          <template v-else>
            <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span class="flex-1 text-sm font-semibold text-white">{{ t('floatingChat.title') }}</span>
            <span v-if="chatStore.totalUnread > 0" class="rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
              {{ chatStore.totalUnread }}
            </span>
          </template>

          <div class="flex items-center gap-1 ml-2">
            <button
              class="rounded p-1 text-white/80 hover:bg-white/20 hover:text-white"
              :aria-label="isMinimized ? t('floatingChat.expand') : t('floatingChat.minimize')"
              @click="isMinimized = !isMinimized"
            >
              <svg v-if="isMinimized" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
              </svg>
              <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <button
              class="rounded p-1 text-white/80 hover:bg-white/20 hover:text-white"
              :aria-label="t('floatingChat.close')"
              @click="isOpen = false"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Body -->
        <template v-if="!isMinimized">
          <!-- Conversation List -->
          <div v-if="showList" class="flex flex-1 flex-col overflow-hidden">
            <div class="px-3 py-2">
              <div class="relative">
                <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  v-model="chatStore.searchQuery"
                  type="text"
                  :placeholder="t('floatingChat.search')"
                  class="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-9 pr-3 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
                />
              </div>
            </div>

            <div class="flex-1 overflow-y-auto">
              <button
                v-for="conv in chatStore.filteredConversations"
                :key="conv.id"
                class="flex w-full items-center gap-2.5 border-b border-gray-100 px-3 py-2.5 text-left transition-colors hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800/50"
                :class="{ 'bg-blue-50 dark:bg-blue-900/10': conv.id === chatStore.activeConversationId }"
                @click="openConversation(conv.id)"
              >
                <div class="relative flex-shrink-0">
                  <div
                    class="flex h-9 w-9 items-center justify-center rounded-full text-sm"
                    :class="conv.type === 'agent' ? 'bg-purple-100 dark:bg-purple-900/30' : conv.type === 'group' ? 'bg-green-100 dark:bg-green-900/30' : 'bg-blue-100 dark:bg-blue-900/30'"
                  >
                    {{ conv.avatar || getConvIcon(conv) }}
                  </div>
                  <span
                    v-if="isOnline(conv)"
                    class="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-white dark:border-gray-900 bg-green-500"
                  ></span>
                </div>

                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-1">
                    <span class="truncate text-sm font-medium text-gray-900 dark:text-white">{{ conv.name }}</span>
                    <span v-if="conv.isPinned" class="text-xs">📌</span>
                  </div>
                  <p class="mt-0.5 truncate text-xs text-gray-500 dark:text-gray-400">
                    {{ conv.lastMessage?.content || conv.description || t('floatingChat.noMessages') }}
                  </p>
                </div>

                <div class="flex flex-col items-end gap-0.5">
                  <span v-if="conv.lastMessage" class="text-[10px] text-gray-400 dark:text-gray-500">
                    {{ formatShortTime(conv.updatedAt) }}
                  </span>
                  <span
                    v-if="conv.unreadCount > 0"
                    class="flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-600 px-1 text-[9px] font-bold text-white"
                  >
                    {{ conv.unreadCount > 9 ? '9+' : conv.unreadCount }}
                  </span>
                </div>
              </button>
            </div>

            <!-- Quick new chat -->
            <div class="border-t border-gray-200 px-3 py-2 dark:border-gray-700">
              <button
                class="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-gray-300 py-2 text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 dark:border-gray-600 dark:text-gray-400 dark:hover:border-blue-500 dark:hover:text-blue-400"
                @click="$emit('openFullChat')"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                {{ t('floatingChat.newConversation') }}
              </button>
            </div>
          </div>

          <!-- Active Conversation -->
          <div v-else-if="activeConv" class="flex flex-1 flex-col overflow-hidden">
            <!-- Messages -->
            <div ref="messagesContainer" class="flex-1 overflow-y-auto">
              <div class="py-2">
                <div v-for="(msg, idx) in chatStore.activeMessages" :key="msg.id">
                  <div
                    v-if="shouldShowDateSeparator(idx)"
                    class="flex items-center justify-center py-2"
                  >
                    <span class="rounded-full bg-gray-100 px-2.5 py-0.5 text-[10px] text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                      {{ formatDateSeparator(msg.createdAt) }}
                    </span>
                  </div>
                  <ChatMessage
                    :content="msg.content"
                    :sender-name="msg.senderName"
                    :sender-avatar="msg.senderAvatar"
                    :sender-type="msg.senderType"
                    :type="msg.type"
                    :metadata="msg.metadata"
                    :reactions="msg.reactions"
                    :created-at="msg.createdAt"
                    :is-own="msg.senderId === 'admin'"
                  />
                </div>
              </div>
            </div>

            <!-- Typing indicator -->
            <div v-if="chatStore.typingUsers.length > 0" class="px-3 py-1 text-[11px] text-gray-500 dark:text-gray-400">
              <span v-for="(user, idx) in chatStore.typingUsers" :key="user.userId">
                <span class="font-medium">{{ user.username }}</span>
                <span v-if="idx < chatStore.typingUsers.length - 2">, </span>
                <span v-else-if="idx === chatStore.typingUsers.length - 2"> {{ t('chat.and') }} </span>
              </span>
              {{ t('chat.typing') }}
            </div>

            <!-- Input -->
            <div class="border-t border-gray-200 px-3 py-2 dark:border-gray-700">
              <div class="flex items-end gap-2">
                <textarea
                  ref="textareaRef"
                  v-model="message"
                  :placeholder="t('floatingChat.placeholder')"
                  rows="1"
                  class="max-h-20 min-h-[36px] flex-1 resize-none rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
                  @keydown.enter.exact.prevent="handleSend"
                  @input="autoResize"
                ></textarea>
                <button
                  class="flex-shrink-0 rounded-lg bg-blue-600 p-2 text-white transition-colors hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
                  :disabled="!message.trim()"
                  :aria-label="t('floatingChat.send')"
                  @click="handleSend"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useChatStore } from '@/stores/chatStore'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import type { Conversation } from '@/types/chat'

defineEmits<{
  openFullChat: []
}>()

const { t } = useI18n()
const chatStore = useChatStore()

const isOpen = ref(false)
const isMinimized = ref(false)
const showList = ref(true)
const message = ref('')
const messagesContainer = ref<HTMLDivElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const activeConv = computed(() => chatStore.activeConversation)

function toggleOpen() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    isMinimized.value = false
    if (!chatStore.activeConversationId) {
      showList.value = true
    } else {
      showList.value = false
    }
  }
}

function openConversation(id: string) {
  chatStore.selectConversation(id)
  showList.value = false
  nextTick(() => scrollToBottom())
}

function handleSend() {
  const text = message.value.trim()
  if (!text || !chatStore.activeConversationId) return

  if (text.startsWith('```')) {
    const codeContent = text.replace(/^```\w*\n?/, '').replace(/\n?```$/, '')
    const langMatch = text.match(/^```(\w+)/)
    chatStore.sendMessage(chatStore.activeConversationId, codeContent, 'code', { language: langMatch?.[1] || 'text' })
  } else {
    chatStore.sendMessage(chatStore.activeConversationId, text)
  }

  message.value = ''
  nextTick(() => {
    if (textareaRef.value) textareaRef.value.style.height = 'auto'
    scrollToBottom()
  })
}

function autoResize() {
  if (!textareaRef.value) return
  textareaRef.value.style.height = 'auto'
  textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 80) + 'px'
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

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

function shouldShowDateSeparator(idx: number): boolean {
  if (idx === 0) return true
  const msgs = chatStore.activeMessages
  const prev = new Date(msgs[idx - 1].createdAt)
  const curr = new Date(msgs[idx].createdAt)
  return prev.toDateString() !== curr.toDateString()
}

function formatDateSeparator(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return t('chat.today')
  if (days === 1) return t('chat.yesterday')
  return date.toLocaleDateString()
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

watch(() => chatStore.activeMessages.length, () => {
  scrollToBottom()
})

watch(() => chatStore.activeConversationId, () => {
  scrollToBottom()
})
</script>
