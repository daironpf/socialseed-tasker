<template>
  <span class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
defineProps<{ label: string }>()
</script>
