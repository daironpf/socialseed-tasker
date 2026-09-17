<template>
  <Teleport to="body">
    <!-- Messenger Bubble Button -->
    <button
      v-if="!isOpen"
      class="fixed bottom-20 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-500 text-white shadow-lg transition-all hover:scale-110 hover:bg-blue-600"
      :aria-label="t('floatingChat.open')"
      @click="toggleOpen"
    >
      <svg class="h-7 w-7" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2C6.477 2 2 6.145 2 11.243c0 2.908 1.432 5.507 3.676 7.21V22l3.588-1.97c.955.263 1.965.403 3.016.403 5.523 0 10-4.145 10-9.243S17.523 2 12 2zm1.075 12.478l-2.545-2.728-4.97 2.728 5.475-5.826 2.6 2.728 4.9-2.728-5.46 5.826z"/>
      </svg>
      <span
        v-if="chatStore.totalUnread > 0"
        class="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white"
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
        class="fixed bottom-20 right-6 z-50 flex flex-col overflow-hidden rounded-xl bg-white shadow-[0_2px_12px_rgba(0,0,0,0.15)] dark:bg-gray-900 dark:shadow-[0_2px_12px_rgba(0,0,0,0.4)]"
        :class="isMinimized ? 'w-[330px]' : 'w-[330px]'"
        :style="{ height: isMinimized ? '48px' : '460px' }"
      >
        <!-- ========== HEADER ========== -->
        <div
          class="flex h-12 flex-shrink-0 items-center gap-2.5 border-b border-gray-100 bg-white px-3 dark:border-gray-800 dark:bg-gray-900"
          :class="isMinimized ? 'border-b-0' : ''"
        >
          <!-- Back arrow (conversation view) -->
          <button
            v-if="activeConv && !showList"
            class="flex-shrink-0 rounded-full p-1 text-blue-500 hover:bg-blue-50 dark:hover:bg-gray-800"
            :aria-label="t('floatingChat.backToList')"
            @click="showList = true"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <!-- Avatar -->
          <div class="relative flex-shrink-0">
            <div
              v-if="activeConv && !showList"
              class="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-sm dark:bg-blue-900/30"
            >
              {{ getConvIcon(activeConv) }}
            </div>
            <div v-else class="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center">
              <svg class="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.477 2 2 6.145 2 11.243c0 2.908 1.432 5.507 3.676 7.21V22l3.588-1.97c.955.263 1.965.403 3.016.403 5.523 0 10-4.145 10-9.243S17.523 2 12 2z"/>
              </svg>
            </div>
            <span
              v-if="activeConv && isOnline(activeConv)"
              class="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white dark:border-gray-900 bg-green-500"
            ></span>
          </div>

          <!-- Title -->
          <div class="min-w-0 flex-1">
            <span v-if="activeConv && !showList" class="block truncate text-[13px] font-semibold text-gray-900 dark:text-white">
              {{ activeConv.name }}
            </span>
            <span v-else class="block text-[13px] font-semibold text-gray-900 dark:text-white">
              {{ t('floatingChat.chats') }}
            </span>
            <span v-if="activeConv && !showList && isOnline(activeConv)" class="block text-[11px] text-green-500">
              {{ t('floatingChat.activeNow') }}
            </span>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-0.5">
            <button
              class="rounded-full p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-gray-800"
              :aria-label="isMinimized ? t('floatingChat.expand') : t('floatingChat.minimize')"
              @click="isMinimized = !isMinimized"
            >
              <svg v-if="isMinimized" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
              </svg>
              <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <button
              class="rounded-full p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-gray-800"
              :aria-label="t('floatingChat.close')"
              @click="isOpen = false"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- ========== BODY ========== -->
        <template v-if="!isMinimized">
          <!-- Conversation List -->
          <div v-if="showList" class="flex flex-1 flex-col overflow-hidden">
            <!-- Search -->
            <div class="px-2 py-1.5">
              <div class="relative">
                <svg class="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  v-model="chatStore.searchQuery"
                  type="text"
                  :placeholder="t('floatingChat.search')"
                  class="w-full rounded-full bg-gray-100 py-1.5 pl-8 pr-3 text-[13px] text-gray-900 placeholder-gray-400 focus:bg-gray-50 focus:outline-none focus:ring-1 focus:ring-blue-200 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500 dark:focus:ring-blue-800"
                />
              </div>
            </div>

            <!-- Conversations -->
            <div class="flex-1 overflow-y-auto">
              <button
                v-for="conv in chatStore.filteredConversations"
                :key="conv.id"
                class="flex w-full items-center gap-2.5 px-2.5 py-2 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
                :class="conv.id === chatStore.activeConversationId ? 'bg-blue-50 dark:bg-blue-900/10' : ''"
                @click="openConversation(conv.id)"
              >
                <!-- Avatar -->
                <div class="relative flex-shrink-0">
                  <div
                    class="h-12 w-12 rounded-full flex items-center justify-center text-lg"
                    :class="conv.type === 'agent' ? 'bg-purple-100 dark:bg-purple-900/30' : conv.type === 'group' ? 'bg-green-100 dark:bg-green-900/30' : 'bg-blue-100 dark:bg-blue-900/30'"
                  >
                    {{ conv.avatar || getConvIcon(conv) }}
                  </div>
                  <span
                    v-if="isOnline(conv)"
                    class="absolute bottom-0 right-0 h-3.5 w-3.5 rounded-full border-2 border-white dark:border-gray-900 bg-green-500"
                  ></span>
                </div>

                <!-- Info -->
                <div class="min-w-0 flex-1 border-b border-gray-100 py-1 dark:border-gray-800">
                  <div class="flex items-center justify-between">
                    <span class="truncate text-[13px] font-semibold text-gray-900 dark:text-white">{{ conv.name }}</span>
                    <span v-if="conv.lastMessage" class="ml-1 flex-shrink-0 text-[11px] text-gray-400 dark:text-gray-500">
                      {{ formatShortTime(conv.updatedAt) }}
                    </span>
                  </div>
                  <div class="flex items-center justify-between">
                    <p class="mr-2 min-w-0 truncate text-[12px] text-gray-500 dark:text-gray-400">
                      <template v-if="conv.lastMessage">
                        {{ conv.lastMessage.senderId === 'admin' ? t('floatingChat.you') + ': ' : '' }}{{ conv.lastMessage.content }}
                      </template>
                      <template v-else>
                        {{ conv.description || t('floatingChat.noMessages') }}
                      </template>
                    </p>
                    <span
                      v-if="conv.unreadCount > 0"
                      class="flex h-5 min-w-5 flex-shrink-0 items-center justify-center rounded-full bg-blue-500 px-1.5 text-[10px] font-bold text-white"
                    >
                      {{ conv.unreadCount > 9 ? '9+' : conv.unreadCount }}
                    </span>
                  </div>
                </div>
              </button>
            </div>

            <!-- Footer link -->
            <div class="border-t border-gray-100 px-3 py-2 dark:border-gray-800">
              <button
                class="w-full text-center text-[12px] font-semibold text-blue-500 hover:text-blue-600 dark:hover:text-blue-400"
                @click="$emit('openFullChat')"
              >
                {{ t('floatingChat.openFullChat') }}
              </button>
            </div>
          </div>

          <!-- Active Conversation -->
          <div v-else-if="activeConv" class="flex flex-1 flex-col overflow-hidden">
            <!-- Messages -->
            <div ref="messagesContainer" class="flex-1 overflow-y-auto px-1.5 py-2">
              <div
                v-for="(msg, idx) in chatStore.activeMessages"
                :key="msg.id"
              >
                <div
                  v-if="shouldShowDateSeparator(idx)"
                  class="flex items-center justify-center py-2"
                >
                  <span class="rounded-full bg-gray-100 px-3 py-1 text-[10px] font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                    {{ formatDateSeparator(msg.createdAt) }}
                  </span>
                </div>

                <!-- System message -->
                <div
                  v-if="msg.type === 'system'"
                  class="flex justify-center py-1.5"
                >
                  <span class="rounded-full bg-gray-100 px-3 py-1 text-[11px] text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                    {{ msg.content }}
                  </span>
                </div>

                <!-- Agent action -->
                <div
                  v-else-if="msg.type === 'agent_action'"
                  class="flex justify-center py-1.5"
                >
                  <div class="rounded-full bg-purple-50 px-3 py-1 text-[11px] text-purple-600 dark:bg-purple-900/20 dark:text-purple-400">
                    <span class="font-medium">{{ msg.senderName }}</span> {{ msg.content }}
                  </div>
                </div>

                <!-- Code block -->
                <div v-else-if="msg.type === 'code'" class="mb-1 flex" :class="msg.senderId === 'admin' ? 'justify-end' : 'justify-start'">
                  <div class="max-w-[85%] overflow-hidden rounded-2xl bg-gray-900 shadow-sm">
                    <div class="flex items-center gap-1.5 border-b border-gray-700 px-3 py-1.5 text-[10px] text-gray-400">
                      <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>
                      <span>{{ msg.metadata?.language || 'code' }}</span>
                    </div>
                    <pre class="overflow-x-auto p-3 text-[12px] leading-relaxed text-gray-200"><code>{{ msg.content }}</code></pre>
                  </div>
                </div>

                <!-- Text bubble -->
                <div
                  v-else
                  class="mb-0.5 flex items-end gap-1.5"
                  :class="msg.senderId === 'admin' ? 'justify-end' : 'justify-start'"
                >
                  <!-- Other's avatar (show only on first message in a row) -->
                  <div
                    v-if="msg.senderId !== 'admin' && isFirstInGroup(idx)"
                    class="flex-shrink-0 mb-0.5"
                  >
                    <div class="h-7 w-7 rounded-full flex items-center justify-center text-xs bg-blue-100 dark:bg-blue-900/30">
                      {{ msg.senderAvatar }}
                    </div>
                  </div>
                  <div v-else-if="msg.senderId !== 'admin'" class="w-7 flex-shrink-0"></div>

                  <!-- Bubble -->
                  <div
                    class="max-w-[85%] rounded-2xl px-3 py-2 text-[13px] leading-relaxed"
                    :class="msg.senderId === 'admin'
                      ? 'bg-blue-500 text-white rounded-br-md'
                      : 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white rounded-bl-md'"
                    v-html="renderBubble(msg.content)"
                  ></div>
                </div>

                <!-- Timestamp under bubble group -->
                <div
                  v-if="isLastInGroup(idx)"
                  class="mt-0.5 flex px-1"
                  :class="msg.senderId === 'admin' ? 'justify-end' : 'justify-start'"
                >
                  <span class="ml-9 text-[10px] text-gray-400 dark:text-gray-500">
                    {{ formatBubbleTime(msg.createdAt) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Typing indicator -->
            <div v-if="chatStore.typingUsers.length > 0" class="flex items-center gap-1.5 px-4 py-1">
              <div class="flex gap-0.5">
                <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 dark:bg-gray-500" style="animation-delay: 0ms"></span>
                <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 dark:bg-gray-500" style="animation-delay: 150ms"></span>
                <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 dark:bg-gray-500" style="animation-delay: 300ms"></span>
              </div>
              <span class="text-[11px] text-gray-400 dark:text-gray-500">
                {{ chatStore.typingUsers.map(u => u.username).join(', ') }} {{ t('chat.typing') }}
              </span>
            </div>

            <!-- ========== INPUT BAR (Messenger style) ========== -->
            <div class="flex items-end gap-1.5 border-t border-gray-100 bg-white px-2 py-2 dark:border-gray-800 dark:bg-gray-900">
              <!-- Emoji button -->
              <button
                class="flex-shrink-0 rounded-full p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-gray-800"
                :aria-label="t('floatingChat.emoji')"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
                </svg>
              </button>

              <!-- Text input -->
              <div class="min-h-[36px] flex-1 rounded-full bg-gray-100 px-3.5 py-1.5 dark:bg-gray-800">
                <textarea
                  ref="textareaRef"
                  v-model="message"
                  :placeholder="t('floatingChat.placeholder')"
                  rows="1"
                  class="w-full resize-none bg-transparent text-[13px] text-gray-900 placeholder-gray-400 focus:outline-none dark:text-white dark:placeholder-gray-500"
                  style="line-height: 22px"
                  @keydown.enter.exact.prevent="handleSend"
                  @input="autoResize"
                ></textarea>
              </div>

              <!-- Send / Like button -->
              <button
                v-if="message.trim()"
                class="flex-shrink-0 rounded-full p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-gray-800 transition-colors"
                :aria-label="t('floatingChat.send')"
                @click="handleSend"
              >
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
              </button>
              <button
                v-else
                class="flex-shrink-0 rounded-full p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-gray-800"
                :aria-label="t('floatingChat.like')"
              >
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2 21h4V9H2v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/>
                </svg>
              </button>
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
      nextTick(() => scrollToBottom())
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
  textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 60) + 'px'
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

function isFirstInGroup(idx: number): boolean {
  if (idx === 0) return true
  const msgs = chatStore.activeMessages
  return msgs[idx].senderId !== msgs[idx - 1].senderId || msgs[idx].type === 'code'
}

function isLastInGroup(idx: number): boolean {
  const msgs = chatStore.activeMessages
  if (idx === msgs.length - 1) return true
  return msgs[idx].senderId !== msgs[idx + 1].senderId || msgs[idx + 1].type === 'code'
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

function formatBubbleTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function renderBubble(content: string): string {
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/`([^`]+)`/g, '<code class="rounded bg-black/10 px-1 text-[12px]">$1</code>')
  html = html.replace(/\n/g, '<br>')
  return html
}

watch(() => chatStore.activeMessages.length, () => {
  scrollToBottom()
})

watch(() => chatStore.activeConversationId, () => {
  showList.value = false
  scrollToBottom()
})
</script>
