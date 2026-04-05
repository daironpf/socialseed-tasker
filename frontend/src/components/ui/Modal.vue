<template>
  <div
    class="relative w-full max-w-md rounded-lg bg-white shadow-lg dark:bg-gray-800"
    role="dialog"
    aria-modal="true"
  >
    <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
        <slot name="title">Modal</slot>
      </h3>
      <button
        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        @click="$emit('close')"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    <div class="px-6 py-4">
      <slot />
    </div>
    <div v-if="$slots.footer" class="border-t border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-900">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{ close: [] }>()
</script>
