<template>
  <div
    class="relative overflow-hidden rounded-xl border border-gray-200 bg-white p-5 transition-all hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
    :class="[sizeClasses]"
  >
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ title }}</p>
        <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-gray-100">
          {{ displayValue }}
        </p>
        <p v-if="subtitle" class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ subtitle }}
        </p>
      </div>
      <div
        class="flex h-12 w-12 items-center justify-center rounded-lg"
        :class="iconBgClass"
      >
        <slot name="icon">
          <svg
            class="h-6 w-6"
            :class="iconClass"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              :d="iconPath"
            />
          </svg>
        </slot>
      </div>
    </div>

    <div v-if="trend !== undefined" class="mt-3 flex items-center gap-1">
      <span
        class="inline-flex items-center gap-1 text-sm font-medium"
        :class="trend >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'"
      >
        <svg
          v-if="trend >= 0"
          class="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 17l9.2-9.2M17 17V7H7" />
        </svg>
        <svg
          v-else
          class="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 7l-9.2 9.2M7 7v10h10" />
        </svg>
        {{ Math.abs(trend) }}%
      </span>
      <span class="text-sm text-gray-500 dark:text-gray-400">vs mes anterior</span>
    </div>

    <div
      v-if="color"
      class="absolute inset-x-0 bottom-0 h-1"
      :class="colorBarClass"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title: string
  value: number | string
  subtitle?: string
  trend?: number
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red'
  iconPath?: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  color: 'blue',
  iconPath: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
  size: 'md',
})

const displayValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'min-h-[120px]',
    md: 'min-h-[140px]',
    lg: 'min-h-[160px]',
  }
  return sizes[props.size]
})

const colorMap = {
  blue: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    icon: 'text-blue-600 dark:text-blue-400',
    bar: 'bg-blue-500',
  },
  green: {
    bg: 'bg-green-100 dark:bg-green-900/30',
    icon: 'text-green-600 dark:text-green-400',
    bar: 'bg-green-500',
  },
  purple: {
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    icon: 'text-purple-600 dark:text-purple-400',
    bar: 'bg-purple-500',
  },
  orange: {
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    icon: 'text-orange-600 dark:text-orange-400',
    bar: 'bg-orange-500',
  },
  red: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    icon: 'text-red-600 dark:text-red-400',
    bar: 'bg-red-500',
  },
}

const iconBgClass = computed(() => colorMap[props.color].bg)
const iconClass = computed(() => colorMap[props.color].icon)
const colorBarClass = computed(() => colorMap[props.color].bar)
</script>
