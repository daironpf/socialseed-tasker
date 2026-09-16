<template>
  <div class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
      <h2 class="text-xl font-bold mb-4">{{ t('auth.login') }}</h2>
      <p class="text-gray-600 dark:text-gray-400 mb-4">
        {{ t('auth.enterApiKey') }}
      </p>
      <form @submit.prevent="handleLogin">
        <input
          v-model="apiKey"
          type="password"
          :placeholder="t('auth.apiKey')"
          :aria-label="t('auth.apiKey')"
          class="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 mb-4"
        />
        <div class="flex gap-2">
          <button
            type="submit"
            class="flex-1 bg-cyan-600 text-white py-2 px-4 rounded-lg hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-600"
          >
            {{ t('auth.submit') }}
          </button>
          <button
            type="button"
            @click="clearAndRetry"
            class="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 dark:bg-gray-600 dark:hover:bg-gray-500"
          >
            {{ t('common.close') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/authStore'
import { USE_MOCK } from '@/api/client'

const { t } = useI18n()

const authStore = useAuthStore()
const emit = defineEmits<{
  loggedIn: []
}>()

const apiKey = ref('')

function handleLogin() {
  authStore.setApiKey(apiKey.value)
  emit('loggedIn')
}

function clearAndRetry() {
  authStore.clearApiKey()
}

onMounted(() => {
  window.addEventListener('auth:unauthorized', handleUnauthorized)
})

onUnmounted(() => {
  window.removeEventListener('auth:unauthorized', handleUnauthorized)
})

function handleUnauthorized() {
  if (!USE_MOCK) {
    window.location.reload()
  }
}
</script>