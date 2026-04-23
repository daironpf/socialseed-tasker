<template>
  <div class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
      <h2 class="text-xl font-bold mb-4">Tasker API Authentication</h2>
      <p class="text-gray-600 dark:text-gray-400 mb-4">
        Enter your API key to access the dashboard.
      </p>
      <form @submit.prevent="handleLogin">
        <input
          v-model="apiKey"
          type="password"
          placeholder="API Key"
          class="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 mb-4"
        />
        <div class="flex gap-2">
          <button
            type="submit"
            class="flex-1 bg-cyan-600 text-white py-2 px-4 rounded-lg hover:bg-cyan-700"
          >
            Login
          </button>
          <button
            type="button"
            @click="clearAndRetry"
            class="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600"
          >
            Clear
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import client from '@/api/client'

const authStore = useAuthStore()
const emit = defineEmits<{
  loggedIn: []
}>()

const apiKey = ref('')

function handleLogin() {
  authStore.setApiKey(apiKey.value)
  if (apiKey.value) {
    client.defaults.headers.common['X-API-Key'] = apiKey.value
  }
  emit('loggedIn')
  window.location.reload()
}

function clearAndRetry() {
  authStore.clearApiKey()
  delete client.defaults.headers.common['X-API-Key']
}

onMounted(() => {
  window.addEventListener('auth:unauthorized', handleUnauthorized)
})

onUnmounted(() => {
  window.removeEventListener('auth:unauthorized', handleUnauthorized)
})

function handleUnauthorized() {
  window.location.reload()
}
</script>