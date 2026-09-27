<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
    <div class="w-full max-w-md rounded-xl border border-gray-200 bg-white p-8 text-center shadow-lg dark:border-gray-700 dark:bg-gray-800">
      <template v-if="busy">
        <div class="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-cyan-600 border-t-transparent" />
        <p class="text-gray-600 dark:text-gray-300">{{ t('auth.connecting') }}</p>
      </template>
      <template v-else-if="failed">
        <p class="mb-4 font-medium text-red-600 dark:text-red-400">{{ t('auth.oauthError') }}</p>
        <button
          class="rounded-lg bg-cyan-600 px-4 py-2 text-white hover:bg-cyan-700"
          data-testid="oauth-fallback"
          @click="router.push('/board')"
        >
          {{ t('auth.login') }}
        </button>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/authStore'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const busy = ref(true)
const failed = ref(false)

onMounted(async () => {
  const code = typeof route.query.code === 'string' ? route.query.code : ''
  if (!code) {
    busy.value = false
    failed.value = true
    return
  }
  try {
    await authStore.completeOAuth(code)
    router.replace('/board')
  } catch {
    busy.value = false
    failed.value = true
  }
})
</script>
