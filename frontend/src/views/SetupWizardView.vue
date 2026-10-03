<template>
  <div class="flex items-center justify-center min-h-[60vh] px-4">
    <div
      class="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800"
    >
      <div
        class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300"
        aria-hidden="true"
      >
        <span class="text-xl font-bold">T</span>
      </div>
      <h1 class="mt-4 text-2xl font-bold text-gray-900 dark:text-gray-100">
        {{ t('setup.title') }}
      </h1>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
        {{ t('setup.loading') }}
      </p>
      <div class="mt-6 flex justify-center" aria-hidden="true">
        <div
          class="h-6 w-6 animate-spin rounded-full border-2 border-brand-600 border-t-transparent"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>
