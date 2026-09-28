<template>
  <div class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
      <h2 class="text-xl font-bold mb-4">{{ t('auth.login') }}</h2>
      <p class="text-gray-600 dark:text-gray-400 mb-4">
        {{ t('auth.enterApiKey') }}
      </p>

      <div class="flex flex-col gap-2 mb-4">
        <button
          type="button"
          data-testid="oauth-github"
          :disabled="authStore.busy"
          class="flex items-center justify-center gap-2 w-full border border-gray-300 dark:border-gray-600 rounded-lg py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          @click="handleOAuth('github')"
        >
          <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-2.15c-3.2.7-3.87-1.36-3.87-1.36-.53-1.33-1.28-1.69-1.28-1.69-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.55-.29-5.23-1.28-5.23-5.68 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 015.78 0c2.21-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.12 3.05.74.81 1.18 1.84 1.18 3.1 0 4.41-2.69 5.38-5.25 5.67.41.35.77 1.05.77 2.12v3.14c0 .3.21.67.8.55A11.51 11.51 0 0023.5 12C23.5 5.65 18.35.5 12 .5z" />
          </svg>
          {{ t('auth.github') }}
        </button>
        <button
          type="button"
          data-testid="oauth-google"
          :disabled="authStore.busy"
          class="flex items-center justify-center gap-2 w-full border border-gray-300 dark:border-gray-600 rounded-lg py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          @click="handleOAuth('google')"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="#4285F4" d="M23.5 12.27c0-.85-.08-1.66-.22-2.45H12v4.64h6.45a5.52 5.52 0 01-2.39 3.62v3h3.87c2.26-2.09 3.57-5.17 3.57-8.81z" />
            <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.93-2.91l-3.87-3c-1.07.72-2.44 1.14-4.06 1.14-3.12 0-5.77-2.11-6.71-4.95H1.29v3.09A12 12 0 0012 24z" />
            <path fill="#FBBC05" d="M5.29 14.28A7.2 7.2 0 014.91 12c0-.79.14-1.56.38-2.28V6.63H1.29A12 12 0 000 12c0 1.94.46 3.77 1.29 5.37l4-3.09z" />
            <path fill="#EA4335" d="M12 4.77c1.76 0 3.34.61 4.58 1.79l3.44-3.44A11.98 11.98 0 0012 0 12 12 0 001.29 6.63l4 3.09C6.23 6.88 8.88 4.77 12 4.77z" />
          </svg>
          {{ t('auth.google') }}
        </button>
      </div>

      <div class="flex items-center gap-3 mb-4">
        <div class="h-px flex-1 bg-gray-200 dark:bg-gray-600" />
        <span class="text-xs uppercase text-gray-500 dark:text-gray-400">{{ t('auth.orContinue') }}</span>
        <div class="h-px flex-1 bg-gray-200 dark:bg-gray-600" />
      </div>

      <p v-if="authStore.error" class="text-sm text-red-600 dark:text-red-400 mb-3" data-testid="login-error" role="alert">
        {{ authStore.error }}
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
            data-testid="login-submit"
            :disabled="authStore.busy"
            class="flex-1 bg-cyan-600 text-white py-2 px-4 rounded-lg hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-600 disabled:opacity-50"
          >
            {{ authStore.busy ? t('auth.connecting') : t('auth.submit') }}
          </button>
          <button
            type="button"
            data-testid="login-clear"
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
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/authStore'

const { t } = useI18n()

const authStore = useAuthStore()
const emit = defineEmits<{
  loggedIn: []
}>()

const apiKey = ref('')

async function handleLogin() {
  try {
    await authStore.login(apiKey.value)
    emit('loggedIn')
  } catch {
    // Error surfaced via authStore.error.
  }
}

async function handleOAuth(provider: 'github' | 'google') {
  try {
    await authStore.loginOAuth(provider)
  } catch {
    // Error surfaced via authStore.error.
  }
}

function clearAndRetry() {
  authStore.clearSession()
}
</script>
