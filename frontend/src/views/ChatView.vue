<template>
  <div class="flex h-[calc(100vh-4rem)]">
    <div class="w-80 flex-shrink-0">
      <ChatSidebar @newConversation="showNewChatModal = true" />
    </div>

    <div class="flex flex-1 flex-col">
      <template v-if="chatStore.activeConversation">
        <div class="flex items-center gap-3 border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-800">
          <div class="relative">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-full text-lg"
              :class="chatStore.activeConversation.type === 'agent' ? 'bg-purple-100 dark:bg-purple-900/30' : chatStore.activeConversation.type === 'group' ? 'bg-green-100 dark:bg-green-900/30' : 'bg-blue-100 dark:bg-blue-900/30'"
            >
              {{ getConvIcon(chatStore.activeConversation) }}
            </div>
            <span
              v-if="isConvOnline(chatStore.activeConversation)"
              class="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-white dark:border-gray-800 bg-green-500"
            ></span>
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ chatStore.activeConversation.name }}</h3>
              <span
                v-if="chatStore.activeConversation.type === 'agent'"
                class="rounded bg-purple-100 px-1.5 py-0.5 text-[9px] font-bold text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
              >AI</span>
              <span
                v-if="chatStore.activeConversation.type === 'group'"
                class="rounded bg-green-100 px-1.5 py-0.5 text-[9px] font-bold text-green-700 dark:bg-green-900/30 dark:text-green-400"
              >{{ chatStore.activeConversation.participants.length }}</span>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ chatStore.activeConversation.description || getParticipantNames(chatStore.activeConversation) }}
            </p>
          </div>
          <button
            class="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
            :aria-label="t('chat.togglePin')"
            @click="chatStore.togglePin(chatStore.activeConversation!.id)"
          >
            {{ chatStore.activeConversation.isPinned ? '📌' : '📍' }}
          </button>
        </div>

        <div ref="messagesContainer" class="flex-1 overflow-y-auto">
          <div class="py-2">
            <div
              v-for="(msg, idx) in chatStore.activeMessages"
              :key="msg.id"
            >
              <div
                v-if="shouldShowDateSeparator(idx)"
                class="flex items-center justify-center py-3"
              >
                <span class="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-500 dark:bg-gray-800 dark:text-gray-400">
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

        <ChatInput @sent="scrollToBottom" />
      </template>

      <template v-else>
        <div class="flex flex-1 items-center justify-center">
          <div class="text-center">
            <div class="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
              <svg class="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('chat.selectConversation') }}</h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ t('chat.selectConversationDesc') }}</p>
          </div>
        </div>
      </template>
    </div>

    <Teleport to="body">
      <Transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="showNewChatModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          @click.self="showNewChatModal = false"
        >
          <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl dark:bg-gray-800">
            <div class="mb-4 flex items-center justify-between">
              <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('chat.newConversationTitle') }}</h3>
              <button
                class="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700"
                :aria-label="t('common.close')"
                @click="showNewChatModal = false"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div class="space-y-3">
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('chat.conversationType') }}</label>
                <select
                  v-model="newChat.type"
                  class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                >
                  <option value="direct">{{ t('chat.typeDirect') }}</option>
                  <option value="group">{{ t('chat.typeGroup') }}</option>
                  <option value="agent">{{ t('chat.typeAgent') }}</option>
                </select>
              </div>

              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('chat.name') }} *</label>
                <input
                  v-model="newChat.name"
                  type="text"
                  class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  :placeholder="t('chat.namePlaceholder')"
                />
              </div>

              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('chat.participants') }}</label>
                <div class="max-h-40 space-y-1 overflow-y-auto">
                  <label
                    v-for="user in availableParticipants"
                    :key="user.id"
                    class="flex cursor-pointer items-center gap-2 rounded-lg p-2 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    <input
                      v-model="newChat.participantIds"
                      type="checkbox"
                      :value="user.id"
                      class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                    />
                    <span class="text-lg">{{ user.avatar }}</span>
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ user.username }}</span>
                    <span v-if="user.type === 'agent'" class="rounded bg-purple-100 px-1 py-0.5 text-[9px] font-bold text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">AI</span>
                    <span v-if="user.isOnline" class="ml-auto h-2 w-2 rounded-full bg-green-500"></span>
                  </label>
                </div>
              </div>

              <div class="flex justify-end gap-2 pt-2">
                <button
                  class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                  @click="showNewChatModal = false"
                >{{ t('common.cancel') }}</button>
                <button
                  class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
                  :disabled="!newChat.name.trim() || newChat.participantIds.length === 0"
                  @click="createChat"
                >{{ t('chat.create') }}</button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useChatStore } from '@/stores/chatStore'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import type { Conversation } from '@/types/chat'

const { t } = useI18n()
const chatStore = useChatStore()

const messagesContainer = ref<HTMLDivElement | null>(null)
const showNewChatModal = ref(false)

const newChat = ref({
  type: 'direct' as 'direct' | 'group' | 'agent',
  name: '',
  participantIds: [] as string[],
})

const availableParticipants = computed(() => {
  return Object.values(chatStore.MOCK_PARTICIPANTS).filter(p => p.id !== 'admin')
})

function getConvIcon(conv: Conversation): string {
  if (conv.type === 'group') return '👥'
  if (conv.type === 'agent') return '🤖'
  const other = conv.participants.find(p => p.id !== 'admin')
  return other?.avatar || '👤'
}

function isConvOnline(conv: Conversation): boolean {
  if (conv.type === 'group') return conv.participants.some(p => p.id !== 'admin' && p.isOnline)
  const other = conv.participants.find(p => p.id !== 'admin')
  return other?.isOnline || false
}

function getParticipantNames(conv: Conversation): string {
  return conv.participants
    .filter(p => p.id !== 'admin')
    .map(p => p.username)
    .join(', ')
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

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function createChat() {
  if (!newChat.value.name.trim() || newChat.value.participantIds.length === 0) return
  const conv = chatStore.createConversation(newChat.value.type, newChat.value.name, newChat.value.participantIds)
  chatStore.selectConversation(conv.id)
  showNewChatModal.value = false
  newChat.value = { type: 'direct', name: '', participantIds: [] }
}

watch(() => chatStore.activeMessages.length, () => {
  scrollToBottom()
})

watch(() => chatStore.activeConversationId, () => {
  scrollToBottom()
})
</script>
