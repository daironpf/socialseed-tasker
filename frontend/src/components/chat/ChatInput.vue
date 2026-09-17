<template>
  <div class="border-t border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-900">
    <div v-if="chatStore.typingUsers.length > 0" class="mb-2 text-xs text-gray-500 dark:text-gray-400">
      <span v-for="(user, idx) in chatStore.typingUsers" :key="user.userId">
        <span class="font-medium">{{ user.username }}</span>
        <span v-if="idx < chatStore.typingUsers.length - 2">, </span>
        <span v-else-if="idx === chatStore.typingUsers.length - 2"> {{ t('chat.and') }} </span>
      </span>
      {{ t('chat.typing') }}
    </div>

    <div class="flex items-end gap-2">
      <div class="flex gap-1">
        <button
          class="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
          :aria-label="t('chat.attachFile')"
          @click="insertCodeBlock"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
        </button>
      </div>

      <div class="relative flex-1">
        <textarea
          ref="textareaRef"
          v-model="message"
          :placeholder="t('chat.placeholder')"
          rows="1"
          class="w-full resize-none rounded-lg border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          :aria-label="t('chat.messageInput')"
          @keydown.enter.exact.prevent="handleSend"
          @input="autoResize"
        ></textarea>
      </div>

      <button
        class="rounded-lg bg-blue-600 p-2.5 text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 dark:bg-blue-500 dark:hover:bg-blue-600"
        :disabled="!message.trim()"
        :aria-label="t('chat.send')"
        @click="handleSend"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useChatStore } from '@/stores/chatStore'

const { t } = useI18n()
const chatStore = useChatStore()

const message = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const emit = defineEmits<{
  sent: []
}>()

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
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
    }
  })
  emit('sent')
}

function insertCodeBlock() {
  message.value += '```\n\n```'
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.focus()
      textareaRef.value.setSelectionRange(4, 4)
    }
  })
}

function autoResize() {
  if (!textareaRef.value) return
  textareaRef.value.style.height = 'auto'
  textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 120) + 'px'
}
</script>
