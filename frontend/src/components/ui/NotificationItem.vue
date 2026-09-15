<template>
  <div
    class="group flex items-start gap-3 px-4 py-3 transition-colors cursor-pointer border-l-3"
    :class="notification.read
      ? 'bg-gray-50/50 dark:bg-gray-800/50 border-l-transparent opacity-60'
      : 'bg-blue-50 dark:bg-blue-900/20 border-l-blue-500'"
    @click="handleClick"
  >
    <div
      class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold"
      :class="categoryClasses"
    >
      {{ config.icon }}
    </div>

    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2">
        <span
          class="truncate text-sm"
          :class="notification.read
            ? 'font-normal text-gray-500 dark:text-gray-500'
            : 'font-semibold text-gray-900 dark:text-white'"
        >{{ notification.title }}</span>
        <span v-if="notification.requiresAction" class="shrink-0 rounded bg-amber-100 px-1.5 py-0.5 text-[9px] font-bold text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
          ACTION
        </span>
      </div>
      <p class="mt-0.5 truncate text-xs" :class="notification.read ? 'text-gray-400 dark:text-gray-500' : 'text-gray-600 dark:text-gray-300'">{{ notification.message }}</p>
      <div class="mt-1 flex items-center gap-2">
        <span class="text-[10px] text-gray-400">{{ timeAgo }}</span>
        <span v-if="!notification.read" class="h-2 w-2 rounded-full bg-blue-500 animate-pulse"></span>
      </div>
    </div>

    <button
      class="shrink-0 rounded p-1 text-gray-400 opacity-0 group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700"
      @click.stop="$emit('dismiss', notification.id)"
    >
      <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { CATEGORY_CONFIG } from '@/types/notifications'
import type { AppNotification } from '@/types/notifications'

const props = defineProps<{
  notification: AppNotification
}>()

const emit = defineEmits<{
  dismiss: [id: string]
  markRead: [id: string]
}>()

const router = useRouter()

const config = computed(() => CATEGORY_CONFIG[props.notification.category])

const categoryClasses = computed(() => {
  const base = props.notification.read
    ? 'bg-gray-100 dark:bg-gray-700 '
    : 'bg-gray-200 dark:bg-gray-600 '
  return base + config.value.color
})

const timeAgo = computed(() => {
  const diff = Date.now() - new Date(props.notification.createdAt).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
})

function handleClick() {
  if (!props.notification.read) {
    emit('markRead', props.notification.id)
  }
  if (props.notification.linkTo) {
    router.push(props.notification.linkTo)
  }
}
</script>
