<template>
  <div
    v-if="password"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    @click.self="close"
  >
    <div class="w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-5 space-y-4">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
        {{ t('users.tempPasswordTitle') }}
      </h3>
      <p class="text-sm text-amber-600 dark:text-amber-400">{{ t('users.passwordOnce') }}</p>
      <div class="flex items-center gap-2">
        <code
          data-testid="temp-password"
          class="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 px-3 py-2 text-sm font-mono break-all text-gray-900 dark:text-white"
        >{{ password }}</code>
        <button
          @click="copy"
          class="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          {{ copied ? t('users.copied') : t('users.copy') }}
        </button>
      </div>
      <div class="flex justify-end">
        <button
          @click="close"
          data-testid="temp-password-ack"
          class="rounded-lg bg-blue-600 hover:bg-blue-700 px-4 py-2 text-sm font-medium text-white"
        >
          {{ t('users.understood') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{ password: string | null }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const copied = ref(false)

async function copy() {
  if (!props.password) return
  try {
    await navigator.clipboard.writeText(props.password)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    /* clipboard unavailable; the password stays selectable on screen */
  }
}

function close() {
  emit('close')
}
</script>
