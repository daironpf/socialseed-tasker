<template>
  <div class="mb-4 flex items-center gap-3">
    <h2 class="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
      {{ title }}
    </h2>
    <div class="h-px flex-1 bg-gray-200 dark:bg-gray-700" />
    <slot name="action" />
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string }>()
</script>
