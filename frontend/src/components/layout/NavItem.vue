<template>
  <button
    class="group flex w-full items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all"
    :class="[
      isActive
        ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400'
        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white',
    ]"
  >
    <div class="flex h-8 w-8 flex-shrink-0 items-center justify-center">
      <svg
        class="h-5 w-5"
        :class="[
          isActive
            ? 'text-brand-600 dark:text-brand-400'
            : 'text-gray-500 group-hover:text-gray-700 dark:text-gray-400 dark:group-hover:text-white',
        ]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="item.icon" />
      </svg>
    </div>
    <span
      v-if="isExpanded"
      class="ml-3 whitespace-nowrap transition-opacity"
    >
      {{ item.label }}
    </span>
    <span
      v-if="item.badge && isExpanded"
      class="ml-auto rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700 dark:bg-brand-900/50 dark:text-brand-400"
    >
      {{ item.badge }}
    </span>
  </button>
</template>

<script setup lang="ts">
interface NavItem {
  path: string
  label: string
  icon: string
  badge?: number
}

defineProps<{
  item: NavItem
  isExpanded: boolean
  isActive: boolean
}>()
</script>
