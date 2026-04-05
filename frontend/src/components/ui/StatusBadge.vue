<template>
  <span
    class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
    :class="statusClasses"
  >
    {{ status }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const statusClasses = computed(() => {
  const map: Record<string, string> = {
    OPEN: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    IN_PROGRESS: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
    CLOSED: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    BLOCKED: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  }
  return map[props.status] ?? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
})
</script>
