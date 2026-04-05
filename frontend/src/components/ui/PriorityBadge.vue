<template>
  <span
    class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
    :class="priorityClasses"
  >
    {{ priority }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  priority: string
}>()

const priorityClasses = computed(() => {
  const map: Record<string, string> = {
    LOW: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
    MEDIUM: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    HIGH: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
    CRITICAL: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  }
  return map[props.priority] ?? 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
})
</script>
